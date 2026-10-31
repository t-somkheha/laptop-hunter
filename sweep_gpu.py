#!/usr/bin/env python3
"""sweep_gpu.py — listings with a DISCRETE GPU: any RTX laptop card, or a dedicated AMD Radeon.

    FB_PORT=9222 FB_PROFILE=.ffprofile python3 sweep_gpu.py 0 3

Query set is built for that one question: every RTX generation the used market still carries,
the AMD Radeon mobile line, the Ada/workstation cards, and the Thai words for a discrete card.
Two price bands per query (the only reliable way past the 24-card wall), five regions.
"""
import asyncio, sys
import harvest

REGIONS = ["bangkok", "chiangmai", "phuket", "khonkaen", "songkhla"]

QUERIES = [
    # NVIDIA current and previous generation
    "rtx 5090 laptop", "rtx 5080 laptop", "rtx 5070 ti laptop", "rtx 5070 laptop",
    "rtx 5060 laptop", "rtx 4090 laptop", "rtx 4080 laptop", "rtx 4070 laptop", "rtx 4060 laptop",
    "rtx 3080 laptop", "rtx 3070 laptop", "rtx 3060 laptop", "rtx 3050 laptop",
    # AMD discrete mobile
    "rx 7900m", "rx 7600m", "rx 7700s", "rx 6800m", "rx 6850m", "rx 6600m", "rx 6500m",
    "radeon rx laptop", "radeon pro laptop",
    # workstation / Ada
    "rtx 5000 ada laptop", "rtx 4000 ada laptop", "rtx a4000 laptop",
    # Thai phrasings for "discrete graphics card"
    "โน้ตบุ๊ค การ์ดจอแยก", "โน๊ตบุ๊ค การ์ดจอแยก", "แล็ปท็อป rtx", "การ์ดจอแยก rtx",
    "โน้ตบุ๊ค rtX", "notebook การ์ดจอ",
]
BANDS = ["", "&minPrice=8000&maxPrice=400000"]

idx, total = int(sys.argv[1]), int(sys.argv[2])
mine = REGIONS[idx::total]
print(f"GPU worker {idx}/{total}: regions {mine}, {len(QUERIES)} queries x {len(BANDS)} bands")

for region in mine:
    print(f"=== region {region}")
    asyncio.run(harvest.main([
        f"--region={region}",
        "--queries=" + ",".join(QUERIES),
        "--bands=" + ",".join(BANDS),
        "--sorts=none",
        "--days=90",
        "--radius=500",
        "--no-details",
    ]))
