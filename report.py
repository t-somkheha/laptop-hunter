#!/usr/bin/env python3
"""report.py — parse harvested listings, score bang-for-buck, rank, write a report.

Judgement, in order:
  1. hard gate  : notebook, GPU VRAM >= 12 GB, price known
  2. perf index : 0.78 * GPU class index + 0.22 * CPU class index (0-100)
  3. value      : perf per 10,000 baht, times modifiers (OLED, size, RAM, warranty, damage)
  4. market test: compare each price against the median price of its own GPU class
"""
import json, os, statistics, sys
from collections import defaultdict
import specs
import harvest

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_TXT = os.path.join(HERE, "data", "report.txt")
OUT_MD = os.path.join(HERE, "data", "report.md")


def extract_detail(rec):
    """Turn a detail record (og tags + body innerText) into title/desc/price/location."""
    body = rec.get("body") or ""
    lines = [l.strip() for l in body.split("\n")]
    lines = [l.strip("\u200b\ufeff ") for l in lines if l.strip()]
    loc = re_search(r"Listed in (.+)", lines)
    if not loc:      # some listings render "<district>, <province> · Location is approximate"
        loc = re_search(r"^([^·]{2,60}) · Location is approximate", lines)

    cond = ""
    price = None
    desc = ""
    try:
        di = lines.index("Details")
    except ValueError:
        di = -1
    if di >= 0:
        seg = lines[di:di + 120]
        for i, l in enumerate(seg):
            if l == "Condition" and i + 1 < len(seg):
                cond = seg[i + 1]
                rest = seg[i + 2:]
                cut = len(rest)
                for j, r in enumerate(rest):
                    if r in ("Tags", "Seller information", "Seller details", "Related searches"):
                        cut = j
                        break
                desc = " ".join(rest[:cut])
                break
    for l in lines:
        p = specs.find_price(l)
        if p:
            price = p
            break
    title = (rec.get("og_title") or "").replace(" | Facebook", "").strip()
    if not title or title.lower() == "facebook":
        for l in lines:
            if specs.find_price(l) is None and len(l) > 8 and "Marketplace" not in l:
                title = l
                break
    return title, (rec.get("og_desc") or ""), desc, price, cond, loc


def re_search(pat, lines):
    import re
    for l in lines:
        m = re.search(pat, l)
        if m:
            return m.group(1).strip()
    return ""


def card_title(card):
    """Card text looks like 'Just listed | ฿65,990 | TITLE | Bangkok, Thailand'."""
    import re
    parts = [p.strip() for p in (card or "").split("|")]
    keep = []
    for p in parts:
        if re.fullmatch(r"(just listed|sponsored|sold|\d+\s+(minutes?|hours?|days?)\s+ago)",
                        p, re.I):
            continue
        if p.startswith("฿"):
            continue
        if re.fullmatch(r"[^,]{1,40},\s*(Thailand|Krung Thep Maha Nakhon)", p):
            continue
        keep.append(p)
    return (max(keep, key=len) if keep else (card or ""))[:120].strip(" |")


def build():
    details = {d["id"]: d for d in harvest.load_jsonl(harvest.DETAILS)}
    cards, seen = [], set()
    for c in harvest.load_jsonl(harvest.CARDS):
        if c["id"] in seen:            # two workers may find the same listing
            continue
        seen.add(c["id"])
        cards.append(c)
    rows, rejected = [], defaultdict(int)
    for c in cards:
        d = details.get(c["id"])
        if d and not d.get("error") and d.get("body"):
            title, ogdesc, desc, price, cond, loc = extract_detail(d)
            if "just listed" in title.lower() or title.startswith("฿"):
                title = card_title(c.get("card", ""))
            blob = " ".join([title, ogdesc, desc, c.get("card", "")])
            rec = specs.parse(blob)
            rec["price"] = rec["price"] or price
            rec["condition"] = cond
            rec["location"] = loc
            rec["title"] = title[:120]
            rec["desc"] = desc[:1200]
            rec["source"] = "detail"
        else:
            rec = specs.parse(c.get("card", ""))
            rec["title"] = card_title(c.get("card", ""))
            rec["condition"] = ""
            rec["location"] = ""
            rec["desc"] = ""
            rec["source"] = "card"
        rec["id"] = c["id"]
        rec["url"] = f"https://www.facebook.com/marketplace/item/{c['id']}/"
        rec["query"] = c.get("query")
        rec["first_seen"] = c.get("first_seen")
        if not rec["laptop"]:
            rejected["not a notebook"] += 1
            continue
        if rec["vram"] is None:
            rows.append(rec)          # kept aside as "manual look", not a rejection
            continue
        if rec["vram"] < 12:
            rejected[f"VRAM {rec['vram']} GB < 12 GB"] += 1
            rec["low"] = True          # kept for the site's "near miss" list
            rows.append(rec)
            continue
        if not rec["price"]:
            rejected["no price"] += 1
            continue
        rec["perf"] = specs.perf_score(rec["gpu_perf"], rec["cpu_perf"])
        rec["value"] = specs.value_index(rec["perf"], rec["price"], rec)
        if "PARTS" in rec["flags"]:
            # a machine that does not power on is a parts donor, never a "qualifier"
            rec["dead"] = True
            rec["value"] = round(rec["value"] * 0.15, 2)
            rejected["for parts / dead"] = rejected.get("for parts / dead", 0) + 1
        rows.append(rec)
    return rows, dict(rejected)


def median_by_class(rows):
    groups = defaultdict(list)
    for r in rows:
        if r.get("perf") and r.get("price") and r.get("vram") and r["vram"] >= 12:
            groups[r["gpu_key"]].append(r["price"])
    return {k: statistics.median(v) for k, v in groups.items() if len(v) >= 2}


def render(rows, rejected, radius=500, top=30, only_ids=None):
    med = median_by_class(rows)
    qual = [r for r in rows if r.get("vram") and r["vram"] >= 12 and r.get("perf")
            and not r.get("dead")]
    unknown = [r for r in rows if r.get("vram") is None]
    if only_ids is not None:
        ids = set(only_ids)
        qual = [r for r in qual if r["id"] in ids]
    qual.sort(key=lambda r: r["value"], reverse=True)

    def vs_median(r):
        m = med.get(r["gpu_key"])
        if not m:
            return ""
        delta = 100.0 * (r["price"] - m) / m
        return f"{delta:+.0f}%"

    lines = []
    A = lines.append
    A(f"LAPTOP HUNT — Facebook Marketplace, {radius} km around Bangkok")
    A(f"hard gate: notebook, VRAM >= 12 GB, price known   |   pool: {len(rows)} parsed, "
      f"{len(qual)} qualified, {len(unknown)} unknown-spec")
    A("")
    if rejected:
        A("dropped: " + ", ".join(f"{k} ({v})" for k, v in sorted(rejected.items(),
                                                                   key=lambda x: -x[1])))
        A("")
    if not qual:
        A("Nothing qualified yet.")
        return "\n".join(lines)

    A(f"{'#':>3} {'฿ price':>9} {'vs peer':>8} {'GPU':<26} {'VRAM':>4} {'CPU':<12} "
      f"{'scr':>5} {'OLED':<4} {'RAM':>4} {'SSD':>5} {'perf':>5} {'value':>6}  flags")
    A("-" * 132)
    for i, r in enumerate(qual[:top], 1):
        flags = ",".join(r["flags"]) if r["flags"] else ""
        A(f"{i:>3} {r['price']:>9,} {vs_median(r):>8} {r['gpu'][:26]:<26} {r['vram']:>4} "
          f"{(r['cpu'] or '?')[:12]:<12} {(r['screen'] or 0):>5} "
          f"{'yes' if r['oled'] else '-':<4} {(r['ram'] or 0):>4} {(r['storage'] or 0):>5} "
          f"{r['perf']:>5} {r['value']:>6}  {flags}")
    A("")
    A("detail on the top ten")
    A("-" * 132)
    for i, r in enumerate(qual[:10], 1):
        A(f"{i}. {r['title']}")
        A(f"   {r['price']:,} THB | {r['gpu']} {r['vram']}GB | {r['cpu'] or 'CPU ?'} | "
          f"{r['screen'] or '?'}in{' OLED' if r['oled'] else ''} | RAM {r['ram'] or '?'} "
          f"| SSD {r['storage'] or '?'} | {r['condition'] or '?'} | {r['location'] or '?'}")
        A(f"   value {r['value']} | perf {r['perf']} | {r['url']}")
        if r["desc"]:
            A(f"   \"{r['desc'][:260]}\"")
        A("")
    if unknown:
        A("unknown spec — worth a manual look")
        A("-" * 132)
        for r in unknown[:15]:
            A(f"   {r['price'] or 0:>9,}  {r['title'][:70]:<70} {r['url']}")
    return "\n".join(lines)


def main(argv):
    rows, rejected = build()
    txt = render(rows, rejected)
    os.makedirs(os.path.dirname(OUT_TXT), exist_ok=True)
    with open(OUT_TXT, "w") as f:
        f.write(txt + "\n")
    print(txt)
    print("\nwritten to", OUT_TXT)


if __name__ == "__main__":
    main(sys.argv[1:])
