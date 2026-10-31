#!/usr/bin/env python3
"""Which extra search parameters slice the result set? Each valid one is a new 24-card window."""
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
  const side = document.body.innerText.split('\n').filter(l => /Within|km/.test(l)).slice(0, 3);
  return {cards: out, side};
})()
"""

BASE = "https://www.facebook.com/marketplace/bangkok/search/?query=laptop%20rtx&radius=500"

CASES = {
    "minmax_50_80k": BASE + "&minPrice=50000&maxPrice=80000",
    "min_60k": BASE + "&minPrice=60000",
    "days90": BASE + "&daysSinceListed=90",
    "days1": BASE + "&daysSinceListed=1",
    "cond_used": BASE + "&itemCondition=used",
    "cond_new": BASE + "&itemCondition=new",
    "exact_false": BASE + "&exact=false",
    "minmax_100_200k": BASE + "&minPrice=100000&maxPrice=200000",
}


async def main():
    fb.start()
    async with fb.Browser() as b:
        for label, url in CASES.items():
            await b.navigate(url)
            await asyncio.sleep(7)
            d = await b.js(CARDS)
            cards = d.get("cards") or []
            prices = [int(m.group(1).replace(",", "")) for c in cards
                      for m in [re.search(r"฿\s*([\d,]+)", c["text"])] if m]
            print(f"{label:<18} cards={len(cards):>3} price min={min(prices) if prices else 0:>8,} "
                  f"max={max(prices) if prices else 0:>8,} sample={prices[:4]} ids={[c['id'][-4:] for c in cards[:3]]}")

asyncio.run(main())
