#!/usr/bin/env python3
"""Verify the southern marketplace slug and whether a 2000 km radius really reaches far cities."""
import asyncio
import fb

SIDE = """(() => document.body.innerText.split('\\n').filter(l => /Within/.test(l)).slice(0,2))()"""
CITIES = r"""
(() => {
  const out = [];
  document.querySelectorAll('a[href*="/marketplace/item/"]').forEach(a => {
    const t = (a.innerText||'').split('\n').map(s=>s.trim()).filter(Boolean);
    if (t.length) out.push(t[t.length-1]);
  });
  return [...new Set(out)].slice(0, 6);
})()
"""
CASES = [
    ("songkhla", "https://www.facebook.com/marketplace/songkhla/search/?query=oled%20rtx&radius=500"),
    ("hat-yai", "https://www.facebook.com/marketplace/hat-yai/search/?query=oled%20rtx&radius=500"),
    ("bangkok r2000 newest", "https://www.facebook.com/marketplace/bangkok/search/?query=oled%20rtx&radius=2000&sortBy=creation_time_descend"),
]


async def main():
    fb.start()
    async with fb.Browser() as b:
        for label, url in CASES:
            await b.navigate(url)
            await asyncio.sleep(7)
            side = await b.js(SIDE)
            cities = await b.js(CITIES)
            href = await b.js("location.href")
            print(f"{label:<22} side={side} cities={cities}")
            print(f"{'':22} url={href[:100]}")

asyncio.run(main())
