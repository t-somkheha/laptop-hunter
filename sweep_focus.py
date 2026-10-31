#!/usr/bin/env python3
"""sweep_focus.py — OLED panel AND a dedicated RTX card with more than 8 GB of VRAM.

    FB_PORT=9222 FB_PROFILE=.ffprofile python3 sweep_focus.py 0 3

Two sides have to meet: the panel (OLED) and the memory (12 GB and up, since >8 means 12, 16 or
24). Queries therefore come in three shapes — panel-led, memory-led, and the model lines that
actually ship that combination — plus the Thai phrasings, because sellers here write the panel
word and the series name far more often than a full specification.
"""
import asyncio, sys
import harvest

REGIONS = ["bangkok", "chiangmai", "phuket", "khonkaen", "songkhla"]

QUERIES = [
    # panel-led
    "oled rtx", "oled laptop rtx", "notebook oled rtx", "oled gaming laptop", "จอ oled rtx",
    "โน้ตบุ๊ค oled rtx", "โน๊ตบุ๊ค oled", "oled 2.8k", "oled 16 inch", "oled 240hz",
    # memory-led
    "rtx 5070 ti", "rtx 5080", "rtx 5090", "rtx 4080", "rtx 4090", "rtx 3080 16gb",
    "12gb vram laptop", "16gb vram laptop", "rtx 5000 ada", "rtx 4000 ada", "rtx 3500 ada",
    "rtx pro 4000", "rx 7900m", "rx 6850m xt",
    # model lines that ship OLED with 12 GB or more
    "Legion Pro 5", "Legion Pro 7", "Legion 9", "Helios Neo 16S", "Helios 16S",
    "Predator Helios 16", "Zephyrus G16 5080", "Zephyrus G16 5090", "Blade 16", "ProArt P16",
    "ProArt Studiobook", "Stealth 16", "Stealth 17", "Raider GE78", "Titan 18",
    "Strix SCAR 16", "Strix SCAR 18", "Aorus 16X", "Omen Transcend", "Yoga Pro 9",
]
BANDS = ["", "&minPrice=15000&maxPrice=400000"]

idx, total = int(sys.argv[1]), int(sys.argv[2])
mine = REGIONS[idx::total]
print(f"focus worker {idx}/{total}: regions {mine}, {len(QUERIES)} queries x {len(BANDS)} bands")

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
