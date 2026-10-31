#!/usr/bin/env python3
"""sweep_refresh.py — recency-oriented re-read of the market, for finding NEW listings.

    FB_PORT=9222 FB_PROFILE=.ffprofile python3 sweep_refresh.py 0 3

Newest-first sort, 30-day window, the queries that actually surface OLED/RTX machines,
two price bands per query, spread across the same five regional marketplaces.
"""
import asyncio, sys
import harvest

REGIONS = ["bangkok", "chiangmai", "phuket", "khonkaen", "songkhla"]

QUERIES = [
    "oled rtx", "oled laptop", "notebook oled", "laptop rtx", "gaming laptop",
    "RTX 5090", "RTX 5080", "RTX 5070 Ti", "RTX 4090", "RTX 4080",
    "RTX 5000 Ada", "RTX 4000 Ada", "laptop oled 16", "โน้ตบุ๊ค oled",
]
BANDS = ["", "&minPrice=15000&maxPrice=300000"]

idx, total = int(sys.argv[1]), int(sys.argv[2])
mine = REGIONS[idx::total]
print(f"refresh worker {idx}/{total}: regions {mine}")

for region in mine:
    print(f"=== region {region}")
    asyncio.run(harvest.main([
        f"--region={region}",
        "--queries=" + ",".join(QUERIES),
        "--bands=" + ",".join(BANDS),
        "--sorts=&sortBy=creation_time_descend",
        "--days=30",
        "--radius=500",
        "--no-details",
    ]))
