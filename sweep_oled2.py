#!/usr/bin/env python3
"""sweep_oled2.py — clean, focused hunt: OLED panel + dedicated RTX card, nationwide.

    FB_PORT=9222 FB_PROFILE=.ffprofile python3 sweep_oled2.py 0 3

Deliberately narrow: only queries that plausibly surface an OLED machine with an RTX card —
generic OLED terms in Thai and English, the 2.8K/3K panel phrasing sellers actually use, and
the model lines that ship such a panel. Two price bands per query, five regional marketplaces.
"""
import asyncio, sys
import harvest

REGIONS = ["bangkok", "chiangmai", "phuket", "khonkaen", "songkhla"]

QUERIES = [
    # generic panel language
    "oled rtx", "oled laptop", "oled gaming laptop", "notebook oled", "โน้ตบุ๊ค oled",
    "จอ oled", "oled 2.8k", "oled 3k laptop", "oled 240hz laptop", "oled rtx 4060",
    # model lines that ship OLED + RTX
    "Zephyrus G16", "Zephyrus G14", "Blade 16", "Vivobook Pro oled", "Zenbook Pro oled",
    "ProArt oled", "Legion oled", "Predator Helios Neo 16S", "Stealth 16", "Omen oled",
    "XPS 15 oled", "Precision oled", "ThinkPad P16 oled", "Yoga Pro oled",
]
BANDS = ["", "&minPrice=15000&maxPrice=300000"]

idx, total = int(sys.argv[1]), int(sys.argv[2])
mine = REGIONS[idx::total]
print(f"OLED worker {idx}/{total}: regions {mine}, "
      f"{len(QUERIES)} queries x {len(BANDS)} bands per region")

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
