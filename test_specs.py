#!/usr/bin/env python3
"""Self-check for specs.parse on realistic Marketplace listing text."""
import json
import specs

SAMPLES = [
 ("LENOVO LEGION PRO 7(2023) (Intel Core i9-13900HX NVIDIA GeForce RTX 4090 16GB GDDR7, TGP 175W) จอ 16 นิ้ว 2K 240Hz rams 32GB ssd 1TB ประกันศูนย์",
  {"gpu_key": "rtx4090", "vram": 16, "screen": 16.0, "ram": 32, "storage": 1024,
   "laptop": True, "cpu": "i9-13900hx"}),
 ("Acer Predator Helios Neo 16 Core i9-14900HX/RTX 4060 8GB/RAM16GB/SSD 1TB/จอ16”240Hz/ประกันศูนย์04/27",
  {"gpu_key": "rtx4060", "vram": 8, "screen": 16.0, "ram": 16, "storage": 1024, "laptop": True}),
 ("RTX2080 ROG 8GB",
  {"gpu_key": "rtx2080", "vram": 8, "laptop": False}),
 ("Asus ROG Zephyrus G16 RTX 4080 12GB OLED 16” i7-13700H 16GB 1TB ฿45,900",
  {"gpu_key": "rtx4080", "vram": 12, "oled": True, "screen": 16.0, "price": 45900}),
 ("โน๊ตบุ๊ค MSI Raider GE78 RTX 5090 24GB RAM 64GB SSD 2TB จอ 17 นิ้ว ฿129,000",
  {"gpu_key": "rtx5090", "vram": 24, "screen": 17.0, "ram": 64, "storage": 2048, "price": 129000}),
 ("HP Omen 16 RTX 5070 Ti Laptop GPU 12GB GDDR7 Ryzen 9 8945HX จอ OLED 16นิ้ว ราคา 64,900 บาท",
  {"gpu_key": "rtx5070ti", "vram": 12, "oled": True, "screen": 16.0, "price": 64900}),
 ("ASUS TUF Gaming A15 FA506NCR RTX 3050 4GB จอ 15.6 144Hz ฿21,888",
  {"gpu_key": "rtx3050", "vram": 4, "screen": 15.6, "price": 21888, "laptop": True}),
 ("Dell Precision 7680 RTX 4000 Ada 12GB i7-13850HX จอ 16 นิ้ว 4K OLED ฿59,000",
  {"gpu_key": "rtx4000ada", "vram": 12, "oled": True, "price": 59000}),
 ("การ์ดจอ RTX 3080 Ti 12GB ราคา ฿9,900", {"laptop": False}),
 ("Legion 5 RTX 3060 6GB จอแตก ฿8,900", {"gpu_key": "rtx3060", "flags": ["SCREEN-DMG"]}),
]

fails = 0
for text, want in SAMPLES:
    rec = specs.parse(text)
    print("\nTEXT:", text[:90])
    print("  ", {k: rec[k] for k in ("gpu_key","vram","cpu","screen","oled","ram","storage","price","flags","laptop")})
    for k, v in want.items():
        got = rec.get(k)
        if isinstance(v, list):
            if not all(x in (got or []) for x in v):
                print(f"   FAIL {k}: want {v} in {got}"); fails += 1
        elif k == "gpu_key" and got is not None and v is not None and got.startswith(v):
            continue
        elif got != v:
            print(f"   FAIL {k}: want {v!r} got {got!r}"); fails += 1
print(f"\n{'ALL PASS' if fails == 0 else str(fails) + ' FAILURES'} on {len(SAMPLES)} samples")
