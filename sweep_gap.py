#!/usr/bin/env python3
"""sweep_gap.py — the second wave, built from words sellers actually use.

    FB_PORT=9222 FB_PROFILE=.ffprofile python3 sweep_gap.py 0 3

Everything here came out of reading real titles from a generic search (probe_titles.py) rather
than from a spec sheet. Three families of gap:

  1. GPU names absent from the first query set — RTX 4050, RTX 5050, and the whole GTX line
     (1650, 1650 Ti, 1660 Ti, 1050 Ti, 1050, 1060, 1070, 1080). A dedicated card is a dedicated
     card; RTX was my own narrowing, not the sellers'.
  2. AMD Radeon mobile parts never queried — RX 5500M, 5600M, 6700M.
  3. Thai gaming phrasing: sellers write เกมมิ่ง more often than "gaming", and the model words
     (IdeaPad Gaming, Nitro V, Katana, Bravo, Alpha, Cyborg, LOQ, Victus 16, TUF F15/A15).
"""
import asyncio, sys
import harvest

REGIONS = ["bangkok", "chiangmai", "phuket", "khonkaen", "songkhla"]

QUERIES = [
    "rtx 4050", "rtx 5050",
    "gtx 1650", "gtx 1660 ti", "gtx 1650 ti", "gtx 1050", "gtx 1060", "gtx 1070", "gtx 1080",
    "rx 5500m", "rx 5600m", "rx 6700m",
    "โน้ตบุ๊คเกมมิ่ง", "โน๊ตบุ๊คเกมมิ่ง", "เกมมิ่งโน๊ตบุ๊ค", "โน้ตบุ๊คเล่นเกม",
    "Ideapad Gaming", "Nitro V", "Katana", "Bravo 15", "Alpha 15", "Cyborg 15",
    "TUF F15", "TUF A15", "Victus 16", "LOQ", "Thin GF63", "Pulse 15",
]
BANDS = ["", "&minPrice=8000&maxPrice=400000"]

idx, total = int(sys.argv[1]), int(sys.argv[2])
mine = REGIONS[idx::total]
print(f"gap worker {idx}/{total}: regions {mine}, {len(QUERIES)} queries x {len(BANDS)} bands")

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
