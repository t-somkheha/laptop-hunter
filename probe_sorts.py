#!/usr/bin/env python3
"""Does sortBy change the result slice? Check price ordering + card count per sort."""
import asyncio, json, re
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
    base = "https://www.facebook.com/marketplace/bangkok/search/?query=laptop%20rtx&daysSinceListed=30&radius=500"
    sorts = ["", "&sortBy=creation_time_descend", "&sortBy=price_ascend", "&sortBy=price_descend",
             "&sortBy=distance_ascend"]
    async with fb.Browser() as b:
        for s in sorts:
            await b.navigate(base + s)
            await asyncio.sleep(6)
            cards = await b.js(CARDS)
            prices = []
            for c in cards:
                m = re.search(r"฿\s*([\d,]+)", c["text"])
                if m:
                    prices.append(int(m.group(1).replace(",", "")))
            print(f"sort={s or '(default)':<28} cards={len(cards):>3} "
                  f"price min={min(prices) if prices else 0:>7,} "
                  f"max={max(prices) if prices else 0:>7,} "
                  f"first3={prices[:3]} ids={[c['id'][-4:] for c in cards[:3]]}")

asyncio.run(main())
