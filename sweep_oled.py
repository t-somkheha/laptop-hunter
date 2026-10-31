#!/usr/bin/env python3
"""sweep_oled.py — nationwide hunt for OLED panels with a dedicated RTX card.

    FB_PORT=9222 FB_PROFILE=.ffprofile python3 sweep_oled.py 0 3

Facebook keeps results clustered near the searched city even at radius=2000, so the country
is tiled with regional marketplaces instead. Worker i takes regions[i::n].
"""
import asyncio, sys
import harvest

REGIONS = ["bangkok", "chiangmai", "phuket", "khonkaen", "songkhla"]

QUERIES = [
    "oled rtx", "oled laptop", "oled gaming laptop", "notebook oled", "จอ oled",
    "โน้ตบุ๊ค oled", "oled 4k laptop", "oled creator laptop",
    "XPS oled", "Zephyrus oled", "Vivobook Pro oled", "ProArt oled",
    "Legion oled", "Predator oled", "ThinkPad oled", "Precision oled", "Blade oled",
]
BANDS = ["", "&minPrice=15000&maxPrice=60000", "&minPrice=60000&maxPrice=300000"]

idx, total = int(sys.argv[1]), int(sys.argv[2])
mine = REGIONS[idx::total]
print(f"worker {idx}/{total}: regions {mine}, {len(QUERIES)}x{len(BANDS)} per region")

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
