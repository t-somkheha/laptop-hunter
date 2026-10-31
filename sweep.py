#!/usr/bin/env python3
"""sweep.py — run one shard of the expanded sweep in its own headless browser.

    FB_PORT=9223 FB_PROFILE=.ffprofile2 python3 sweep.py 1 3

Shards split QUERIES round-robin so no two workers hammer the same search, while all three
append to the same JSONL files (single-record appends, deduped at report time).
"""
import asyncio, os, sys
import harvest

idx, total = int(sys.argv[1]), int(sys.argv[2])
queries = [q for i, q in enumerate(harvest.QUERIES) if i % total == idx]
# price bands are the coverage lever; the extra sort orders are marginal once bands are used
bands = [harvest.BANDS[0], harvest.BANDS[2], harvest.BANDS[3], harvest.BANDS[4]]
args = [
    "--queries=" + ",".join(queries),
    "--bands=" + ",".join(bands),
    "--sorts=none",
    "--days=90",
    "--cap=250",
]
print(f"worker {idx}/{total}: {len(queries)} queries x {len(bands)} bands = "
      f"{len(queries)*len(bands)} pages")
asyncio.run(harvest.main(args))
