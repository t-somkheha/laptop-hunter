#!/usr/bin/env python3
"""Open specific listings and dump the raw page text, to check location/seller/red flags."""
import asyncio, sys
import fb

IDS = sys.argv[1:] or ["2065711087410957"]


async def main():
    fb.start()
    async with fb.Browser() as b:
        for iid in IDS:
            await b.navigate(f"https://www.facebook.com/marketplace/item/{iid}/")
            await asyncio.sleep(6)
            txt = await b.text()
            print("=" * 30, iid)
            lines = [l.strip() for l in txt.split("\n") if l.strip()]
            keep = [l for l in lines if any(k in l for k in
                    ("Listed in", "Seller", "Joined", "rating", "km", "฿", "Condition",
                     "Location", "Today", "Member", "verified", "Map", "Seller details"))]
            print("\n".join(keep[:40]))
            print("---- body tail ----")
            print(txt[-1200:])

asyncio.run(main())
