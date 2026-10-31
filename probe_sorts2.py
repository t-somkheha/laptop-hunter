#!/usr/bin/env python3
"""Retest the two price sorts with a longer wait — are they valid or transiently empty?"""
import asyncio, re
import fb

CARDS = r"""
(() => {
  const out = [], seen = new Set();
  document.querySelectorAll('a[href*="/marketplace/item/"]').forEach(a => {
    const m = (a.getAttribute('href') || '').match(/\/marketplace\/item\/(\d+)/);
    if (!m || seen.has(m[1])) return;
    seen.add(m[1]);
    const t = (a.innerText || '').split('\n').map(s => s.trim()).filter(Boolean);
    out.push({id: m[1], text: t.join(' | ')});
  });
  return out;
})()
"""


async def main():
    fb.start()
    base = ("https://www.facebook.com/marketplace/bangkok/search/?query=laptop%20rtx"
            "&daysSinceListed=30&radius=500")
    async with fb.Browser() as b:
        for s in ["&sortBy=price_ascend", "&sortBy=price_descend", "&sortBy=price_low_to_high"]:
            for attempt in range(2):
                await b.navigate(base + s)
                await asyncio.sleep(9)
                cards = await b.js(CARDS)
                prices = [int(m.group(1).replace(",", "")) for c in cards
                          for m in [re.search(r"฿\s*([\d,]+)", c["text"])] if m]
                print(f"{s} attempt {attempt}: cards {len(cards)} first {prices[:3]}")
                if cards:
                    break

asyncio.run(main())
