#!/usr/bin/env python3
"""Can we widen beyond Bangkok? Test radius limits and regional marketplace slugs."""
import asyncio, re
import fb

COUNT = "[...document.querySelectorAll('a[href*=\"/marketplace/item/\"]')].length"
SIDE = """(() => document.body.innerText.split('\\n').filter(l => /Within|km|·/.test(l)).slice(0,4))()"""

CITY = r"""
(() => {
  const out = [];
  document.querySelectorAll('a[href*="/marketplace/item/"]').forEach(a => {
    const t = (a.innerText||'').split('\n').map(s=>s.trim()).filter(Boolean);
    const tail = t.slice(-1)[0] || '';
    if (tail) out.push(tail);
  });
  return [...new Set(out)].slice(0, 5);
})()
"""

CASES = [
    ("bangkok r500", "https://www.facebook.com/marketplace/bangkok/search/?query=oled%20rtx&radius=500"),
    ("bangkok r1000", "https://www.facebook.com/marketplace/bangkok/search/?query=oled%20rtx&radius=1000"),
    ("bangkok r2000", "https://www.facebook.com/marketplace/bangkok/search/?query=oled%20rtx&radius=2000"),
    ("chiangmai", "https://www.facebook.com/marketplace/chiangmai/search/?query=oled%20rtx&radius=500"),
    ("phuket", "https://www.facebook.com/marketplace/phuket/search/?query=oled%20rtx&radius=500"),
    ("hatyai", "https://www.facebook.com/marketplace/hatyai/search/?query=oled%20rtx&radius=500"),
    ("khonkaen", "https://www.facebook.com/marketplace/khonkaen/search/?query=oled%20rtx&radius=500"),
]


async def main():
    fb.start()
    async with fb.Browser() as b:
        for label, url in CASES:
            try:
                await b.navigate(url)
            except Exception as e:
                print(f"{label:<16} NAV FAIL {e}")
                continue
            await asyncio.sleep(7)
            try:
                n = await b.js(COUNT)
                side = await b.js(SIDE)
                cities = await b.js(CITY)
                print(f"{label:<16} cards={n:<4} side={side[:2]} cities={cities}")
                print(f"{'':16} final_url={await b.js('location.href')[:110]}")
            except Exception as e:
                print(f"{label:<16} ERR {e}")

asyncio.run(main())
