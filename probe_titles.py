#!/usr/bin/env python3
"""probe_titles.py — search with plain generic words, then read what sellers actually wrote.

    python3 probe_titles.py

Deliberately dumb queries ("laptop", "notebook", the Thai words, "gaming"). The point is not to
find machines but to see the vocabulary: which model names, GPU names and phrasings appear in
real titles that our GPU-led query set never asked for.
"""
import asyncio, re
from collections import Counter

import harvest

QUERIES = ["laptop", "notebook", "โน้ตบุ๊ค", "โน๊ตบุ๊ค", "gaming laptop", "แล็ปท็อป", "เกมมิ่ง"]
BANDS = ["", "&minPrice=8000&maxPrice=400000"]

GPU_TOKENS = re.compile(
    r"\b(rtx|gtx|rx|quadro|radeon|arc)\s*[- ]?(\d{3,4}\s?(?:ti|super|xt|s)?)\b", re.I)


def analyse():
    cards = [c for c in harvest.load_jsonl(harvest.CARDS) if c.get("query") in QUERIES]
    texts = [c["card"] for c in cards]
    print(f"\n{len(texts)} cards from {len(QUERIES)} generic queries")

    toks, gpu_titles = Counter(), 0
    for t in texts:
        hits = list(GPU_TOKENS.finditer(t))
        if hits:
            gpu_titles += 1
        for m in hits:
            toks[f"{m.group(1).upper()} {m.group(2).strip().upper()}"] += 1
    print(f"{gpu_titles} of them name a GPU chip")

    print("\nGPU names sellers actually wrote:")
    for k, v in toks.most_common(30):
        print(f"   {v:>3}  {k}")

    words = Counter()
    for t in texts:
        for w in re.findall(r"[A-Za-z][A-Za-z0-9\-]{2,}", t):
            words[w.lower()] += 1
    print("\nmost common Latin words in those titles:")
    print("   " + ", ".join(f"{w}({n})" for w, n in words.most_common(28)))
    print("\nsample titles:")
    for t in texts[:20]:
        print("   " + t.replace("\n", " ")[:112])


def main():
    asyncio.run(harvest.main([
        "--region=bangkok",
        "--queries=" + ",".join(QUERIES),
        "--bands=" + ",".join(BANDS),
        "--sorts=none",
        "--days=90",
        "--no-details",
    ]))
    analyse()


if __name__ == "__main__":
    main()
