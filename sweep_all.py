#!/usr/bin/env python3
"""sweep_all.py — every laptop listing we can reach, not just the OLED ones.

    FB_PORT=9222 FB_PROFILE=.ffprofile python3 sweep_all.py 0 3

Generic category words, the Thai words sellers actually type, and the brand/series names that
identify a notebook without naming a GPU. Two price bands per query (price bands are the only
thing that reliably gets past Facebook's 24-card wall), five regional marketplaces.
"""
import asyncio, sys
import harvest

REGIONS = ["bangkok", "chiangmai", "phuket", "khonkaen", "songkhla"]

QUERIES = [
    # category words
    "laptop", "notebook", "โน้ตบุ๊ค", "โน๊ตบุ๊ค", "โน้ตบุ๊ก", "gaming laptop", "laptop gaming",
    "laptop rtx", "แล็ปท็อป", "computer laptop",
    # GPU-led
    "RTX 5090", "RTX 5080", "RTX 5070", "RTX 4090", "RTX 4080", "RTX 4070", "RTX 4060",
    "RTX 3080", "RTX 3070", "RTX 3060",
    # series-led
    "ROG", "TUF Gaming", "Legion", "Predator", "Nitro", "Katana", "Stealth", "Raider",
    "Omen", "Victus", "Zephyrus", "Alienware", "XPS", "ThinkPad", "Vivobook", "Zenbook",
    "workstation laptop",
]
BANDS = ["", "&minPrice=8000&maxPrice=400000"]

idx, total = int(sys.argv[1]), int(sys.argv[2])
mine = REGIONS[idx::total]
print(f"all-laptop worker {idx}/{total}: regions {mine}, {len(QUERIES)} queries x {len(BANDS)} bands")

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
