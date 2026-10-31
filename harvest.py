#!/usr/bin/env python3
"""harvest.py — pull Facebook Marketplace listings (cards + item pages) into JSONL.

Written against a logged-in headless Firefox driven over WebDriver BiDi; see fb.py.

Two facts established live and worth remembering:
  * `radius=<km>` is honoured by FB's search URL ("Within 500 km").
  * valid `sortBy` values are default(best match), creation_time_descend, distance_ascend.
    price_ascend / price_descend render an EMPTY grid, so coverage comes from fanning out
    over query wording x sort order instead (24 cards per slice, no deeper pagination —
    FB only appends on trusted input scroll, which synthetic events do not satisfy).
"""
import asyncio, datetime, json, os, random, re, sys, time
import fb

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
CARDS = os.path.join(DATA, "cards.jsonl")
DETAILS = os.path.join(DATA, "details.jsonl")

# Which Marketplace region to search. Bangkok with a big radius reaches most of the country,
# but the specialised OLED/RTX hunt also walks the regional marketplaces directly.
REGION = os.environ.get("FB_REGION", "bangkok")

QUERIES = [
    # generic
    "laptop rtx", "notebook rtx", "gaming laptop", "gaming notebook",
    "โน้ตบุ๊ค rtx", "แล็ปท็อป rtx", "โน้ตบุ๊คเกมมิ่ง", "โน้ตบุ๊ค oled",
    "workstation laptop", "creator laptop", "laptop ตัดต่อ", "โน้ตบุ๊ค เรนเดอร์",
    "laptop 16GB VRAM", "laptop 24GB VRAM", "RTX laptop 16 GB",
    # GPU models with a >=12 GB laptop trim
    "RTX 4090", "RTX 4080", "RTX 3080 Ti", "RTX 3080 16GB", "RTX 5090", "RTX 5080",
    "RTX 5070 Ti", "RTX 5000 Ada", "RTX 4000 Ada", "RTX 3500 Ada", "RTX A5500", "RTX A4500",
    "RX 7900M", "RX 6850M XT", "RX 6800M", "Arc A770M", "Arc A730M",
    # models that ship a >=12 GB option
    "Zephyrus", "Zephyrus Duo", "Legion Pro", "Legion 7", "Legion 9", "ROG Strix SCAR",
    "Predator Helios", "Helios 18", "Raider GE78", "Vector 16", "Titan 18", "Katana 17",
    "Blade 16", "Aorus 16X", "Alienware m16", "Alienware m18", "ThinkPad P1",
    "ThinkPad P16", "Precision 7680", "Precision 7780", "ZBook Fury", "ZBook Studio",
    "laptop oled 16", "โน้ตบุ๊ค 16 นิ้ว RTX", "notebook RTX 16 นิ้ว",
]
SORTS = ["", "&sortBy=creation_time_descend"]
# price bands are valid FB parameters and each returns a DIFFERENT set of 24 cards,
# which is the main lever for going deeper than one page per query.
BANDS = ["", "&minPrice=25000&maxPrice=55000", "&minPrice=55000&maxPrice=85000",
         "&minPrice=85000&maxPrice=130000", "&minPrice=130000&maxPrice=400000"]

CARD_JS = r"""
(() => {
  const items = [], seen = new Set();
  document.querySelectorAll('a[href*="/marketplace/item/"]').forEach(a => {
    const m = (a.getAttribute('href') || '').match(/\/marketplace\/item\/(\d+)/);
    if (!m || seen.has(m[1])) return;
    seen.add(m[1]);
    const t = (a.innerText || '').split('\n').map(s => s.trim()).filter(Boolean);
    if (!t.length) return;
    items.push({id: m[1], text: t.join(' | ')});
  });
  return items;
})()
"""

DETAIL_JS = r"""
(() => {
  const meta = p => { const e = document.querySelector(`meta[property="${p}"]`); return e ? e.content : ''; };
  const canon = document.querySelector('link[rel="canonical"]');
  const body = document.body ? document.body.innerText : '';
  const good = s => s && /^https?:/.test(s) && /(scontent|fbcdn)/.test(s);
  let imgs = [...document.querySelectorAll('img')]
      .map(i => i.currentSrc || i.src).filter(good)
      .map(s => s.replace(/&amp;/g, '&'));
  const big = imgs.filter(s => !/s\d+x\d+|p\d+x\d+/.test(s));   // prefer full-size over thumbnails
  imgs = [...new Set((big.length ? big : imgs))].slice(0, 10);
  return {og_title: meta('og:title'), og_desc: meta('og_description') || meta('og:description'),
          og_image: meta('og:image'), canonical: canon ? canon.href : location.href,
          images: imgs, body: body.slice(0, 9000)};
})()
"""


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def load_jsonl(path):
    if not os.path.exists(path):
        return []
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return out


def append_jsonl(path, rec):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


async def harvest_cards(b, queries, radius=500, days=90, sorts=None, bands=None, region=None):
    """One page per (query, sort, price band). FB returns a different set of 24 cards for
    each, which is how recall grows past the no-pagination wall."""
    region = region or REGION
    sorts = sorts if sorts is not None else SORTS
    bands = bands if bands is not None else BANDS
    seen_ids = {r["id"] for r in load_jsonl(CARDS)}
    new_total = 0
    t_query = time.time()
    for qi, q in enumerate(queries, 1):
        per_query = 0
        for s in sorts:
            for band in bands:
                url = (f"https://www.facebook.com/marketplace/{region}/search/?query="
                       + re.sub(r"\s+", "%20", q)
                       + f"&daysSinceListed={days}&radius={radius}" + s + band)
                try:
                    await b.navigate(url)
                except Exception as e:
                    print(f"  ! navigate failed {q!r}{s}{band}: {e}")
                    continue
                await asyncio.sleep(6.0 + random.random() * 1.5)
                try:
                    items = await b.js(CARD_JS) or []
                except Exception as e:
                    print(f"  ! extract failed {q!r}{s}{band}: {e}")
                    continue
                for it in items:
                    if it["id"] in seen_ids:
                        continue
                    seen_ids.add(it["id"])
                    append_jsonl(CARDS, {"id": it["id"], "card": it["text"], "query": q,
                                         "sort": s, "band": band, "region": region,
                                         "first_seen": now()})
                    per_query += 1
        new_total += per_query
        print(f"  [{qi}/{len(queries)}] {q!r}: {per_query} new "
              f"({per_query and round((time.time()-t_query)/per_query,1) or 0}s/item, "
              f"{len(seen_ids)} ids on file)")
    return new_total


def card_is_candidate(card_text, min_vram=12):
    """Which cards deserve an item-page fetch.

    Cards almost never carry the specification, so a card that simply fails to name a GPU is
    NOT evidence of a weak GPU — it may be a twelve-gigabyte machine described as "gaming
    laptop". Only cards that name a GPU below 12 GB, or that are plainly not notebooks, are
    dropped without opening them.
    """
    import specs
    rec = specs.parse(card_text)
    if not rec["laptop"]:
        return False
    if rec["gpu_key"] and rec["vram"] is not None:
        return rec["vram"] >= min_vram
    low = card_text.lower()
    if any(k in low for k in ("การ์ดจอ", "for parts", "อะไหล่", "รับซื้อ", "รับซ่อม")):
        return False
    return True


async def fetch_details(b, ids, pause=3.0, cap=None):
    have = {r["id"] for r in load_jsonl(DETAILS)}
    todo = [i for i in ids if i not in have]
    if cap:
        todo = todo[:cap]
    print(f"  detail pages: {len(todo)} to fetch ({len(have)} cached)")
    done = 0
    for iid in todo:
        try:
            await b.navigate(f"https://www.facebook.com/marketplace/item/{iid}/")
            await asyncio.sleep(pause + random.random() * 1.6)
            d = await b.js(DETAIL_JS)
            d["id"] = iid
            d["fetched"] = now()
            append_jsonl(DETAILS, d)
            done += 1
            if done % 15 == 0:
                print(f"    {done}/{len(todo)}")
        except Exception as e:
            print(f"    ! {iid}: {e}")
            append_jsonl(DETAILS, {"id": iid, "error": str(e), "fetched": now()})
    return done


async def with_browser(run):
    """Run `run(browser)`, healing the one-session-per-agent limit.

    Firefox's Remote Agent allows exactly one BiDi session. A run killed mid-flight leaves
    it held, and every later session.new returns "session not created" — so treat that as
    a stale session and restart the browser once.
    """
    fb.start()
    for attempt in (1, 2):
        try:
            async with fb.Browser() as b:
                return await run(b)
        except RuntimeError as e:
            if "session not created" in str(e) and attempt == 1:
                print("  stale BiDi session — restarting headless browser")
                fb.stop()
                await asyncio.sleep(3)
                fb.start(force=True)
                continue
            raise


async def main(argv):
    radius = 500
    days = 90
    region = REGION
    queries = QUERIES
    bands = BANDS
    sorts = SORTS
    cap = 400
    if "--quick" in argv:
        queries = QUERIES[:4]
    if "--no-bands" in argv:
        bands = [""]
    for a in argv:
        if a.startswith("--limit="):
            cap = int(a.split("=", 1)[1])
        if a.startswith("--cap="):
            cap = int(a.split("=", 1)[1])
        if a.startswith("--days="):
            days = int(a.split("=", 1)[1])
        if a.startswith("--radius="):
            radius = int(a.split("=", 1)[1])
        if a.startswith("--region="):
            region = a.split("=", 1)[1]
        if a.startswith("--queries="):
            queries = a.split("=", 1)[1].split(",")
        if a.startswith("--bands="):
            bands = a.split("=", 1)[1].split(",")
        if a.startswith("--sorts="):
            sorts = [s for s in a.split("=", 1)[1].split("|") if s != "none"]
            sorts = sorts or [""]
    details_only = "--details-only" in argv
    no_details = "--no-details" in argv
    shard = None
    for a in argv:
        if a.startswith("--shard="):
            i, n = a.split("=", 1)[1].split("/")
            shard = (int(i), int(n))

    async def run(b):
        t0 = time.time()
        if not details_only:
            print(f"harvesting {len(queries)} queries x {len(sorts)} sorts x {len(bands)} "
                  f"price bands = {len(queries)*len(sorts)*len(bands)} pages, region "
                  f"{region}, radius {radius} km, last {days} days")
            added = await harvest_cards(b, queries, radius=radius, days=days,
                                        sorts=sorts, bands=bands, region=region)
            print(f"  +{added} new cards")
        cards = load_jsonl(CARDS)
        cands = [c["id"] for c in cards if card_is_candidate(c["card"])]
        if shard:
            i, n = shard
            cands = [cid for idx, cid in enumerate(cands) if idx % n == i]
        print(f"  {len(cards)} cards on file, {len(cands)} candidates in this shard")
        if not no_details:
            await fetch_details(b, cands, cap=cap)
        print(f"done in {time.time()-t0:.0f}s")

    await with_browser(run)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
