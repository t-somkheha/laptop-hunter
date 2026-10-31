#!/usr/bin/env python3
"""follow.py — re-read specific listings by id, whatever the search engine thinks of them.

    python3 follow.py                # everything in data/watchlist.txt
    python3 follow.py 861516143690174 993224663828951

Why this exists: Facebook's query matching is fussy. A machine can be live and unchanged and
still fail to appear for every wording you try — a clean re-sweep therefore silently drops
machines you already knew about. Following ids directly is the immune response.

Any id not already in cards.jsonl gets a synthetic card so report.build() will include it.
"""
import asyncio, sys
import fb, harvest

WATCHLIST = harvest.DATA + "/watchlist.txt"


def watch_ids(argv):
    for a in argv:
        if a.startswith("--ids="):
            with open(a.split("=", 1)[1]) as f:
                return [ln.strip() for ln in f if ln.strip()]
    ids = [a for a in argv if a.isdigit()]
    if ids:
        return ids
    try:
        with open(WATCHLIST) as f:
            return [ln.strip() for ln in f if ln.strip().isdigit()]
    except FileNotFoundError:
        return []


def ensure_cards(ids):
    have = {c["id"] for c in harvest.load_jsonl(harvest.CARDS)}
    added = 0
    for iid in ids:
        if iid in have:
            continue
        harvest.append_jsonl(harvest.CARDS, {
            "id": iid, "card": f"watchlist | {iid}", "query": "watchlist",
            "first_seen": harvest.now(), "region": "watchlist",
        })
        added += 1
    return added


async def run(b, ids):
    # force a re-read: cached detail pages could predate a price change
    fresh = []
    for iid in ids:
        try:
            await b.navigate(f"https://www.facebook.com/marketplace/item/{iid}/")
            await asyncio.sleep(3.5)
            d = await b.js(harvest.DETAIL_JS)
            d["id"] = iid
            d["fetched"] = harvest.now()
            fresh.append(d)
        except Exception as e:
            print(f"  ! {iid}: {e}")
    if fresh:
        # rewrite details.jsonl, replacing the same ids
        old = [r for r in harvest.load_jsonl(harvest.DETAILS) if r["id"] not in ids]
        with open(harvest.DETAILS, "w") as f:
            for r in old + fresh:
                f.write(__import__("json").dumps(r, ensure_ascii=False) + "\n")
    return len(fresh)


def main(argv):
    ids = watch_ids(argv)
    import re as _re
    for a in argv:
        if _re.fullmatch(r"\d+/\d+", a):
            i, n = a.split("/")
            ids = [x for k, x in enumerate(ids) if k % int(n) == int(i)]
    if not ids:
        print("no ids — put listing ids in data/watchlist.txt, one per line")
        return
    added = ensure_cards(ids)
    print(f"following {len(ids)} listings ({added} added as synthetic cards)")

    async def go(b):
        n = await run(b, ids)
        print(f"re-read {n} item pages")

    asyncio.run(harvest.with_browser(go))


if __name__ == "__main__":
    main(sys.argv[1:])
