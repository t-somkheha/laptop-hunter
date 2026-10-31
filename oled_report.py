#!/usr/bin/env python3
"""oled_report.py — every listing with an OLED panel AND a dedicated RTX GPU, anywhere in Thailand.

No VRAM gate, no screen-size gate: this is the "show me OLED + RTX" answer, not the
bang-for-buck ranking.
"""
import os, re
import report, harvest

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data", "oled_rtx.txt")

RTX = re.compile(r"\brtx\b|\brtx\s*(?:pro)?\s*\d|\b(?:a|ada)\s*\d{4}\b|\bquadro\s*rtx\b")


def is_rtx(r):
    gpu = (r.get("gpu") or "")
    if RTX.search(gpu.lower()):
        return True
    # 'RTX 5000 Ada Laptop' style names come through the table already; catch anything else
    return bool(re.search(r"\brtx", gpu.lower()))


def dedupe(hits):
    """Shops repost the same machine from two branches; keep the cheapest of each fingerprint."""
    seen, out = {}, []
    for r in hits:
        key = (r.get("gpu"), r.get("screen"), r.get("ram"), r.get("storage"),
               round((r.get("price") or 0) / 3000))
        if key in seen:
            continue
        seen[key] = r
        out.append(r)
    return out


def main():
    rows, rejected = report.build()
    hits = [r for r in rows
            if r.get("oled") and r.get("price") and is_rtx(r)
            and r.get("laptop", True) and not r.get("dead")]  # no VRAM gate here
    hits.sort(key=lambda r: r["price"])   # sort first, so dedupe keeps the CHEAPEST repost
    hits = dedupe(hits)

    lines = [f"OLED + dedicated RTX — Thailand — {len(hits)} listings", ""]
    for i, r in enumerate(hits, 1):
        ram = f"{r['ram']}GB" if r.get("ram") else "RAM?"
        ssd = (f"{r['storage']//1024}TB" if (r.get("storage") or 0) >= 1024
               else f"{r['storage']}GB" if r.get("storage") else "SSD?")
        flags = ",".join(r.get("flags") or [])
        lines.append(f"{i:>2}. ฿{r['price']:,}  {r['title'][:78]}")
        lines.append(f"    {r['gpu']} {r['vram']}GB | {r.get('cpu') or 'CPU ?'} | "
                     f"{r['screen'] or '?'}\" OLED | {r['ram'] or '?'}GB RAM | {ssd} | "
                     f"{r.get('condition') or '?'} | {r.get('location') or '?'}"
                     + (f" | {flags}" if flags else ""))
        lines.append(f"    {r['url']}")
        if r.get("desc"):
            lines.append(f"    \"{r['desc'][:200]}\"")
        lines.append("")
    txt = "\n".join(lines)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        f.write(txt + "\n")
    print(txt)
    print(f"written to {OUT}")


if __name__ == "__main__":
    main()
