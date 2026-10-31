#!/usr/bin/env python3
"""Bigger viewport + incremental scrolling of FB's inner grid container."""
import asyncio, json
import fb

COUNT = "[...document.querySelectorAll('a[href*=\"/marketplace/item/\"]')].length"

STEP = r"""
(() => {
  const boxes = [];
  document.querySelectorAll('div').forEach(e => {
    const s = getComputedStyle(e);
    if (/(auto|scroll)/.test(s.overflowY) && e.scrollHeight > e.clientHeight + 100) boxes.push(e);
  });
  if (!boxes.length) return {moved: 0};
  const el = boxes[0];
  const before = el.scrollTop;
  el.scrollTop = Math.min(before + %d, el.scrollHeight);
  el.dispatchEvent(new Event('scroll', {bubbles: true}));
  return {moved: el.scrollTop - before, top: el.scrollTop, sh: el.scrollHeight, ch: el.clientHeight};
})()
"""


async def main():
    fb.start()
    async with fb.Browser() as b:
        try:
            await b.send("browsingContext.setViewport",
                         {"context": b.ctx, "viewport": {"width": 1500, "height": 1300}})
            print("viewport set")
        except Exception as e:
            print("setViewport failed:", e)
            try:
                await b.send("browsingContext.setWindowRect",
                             {"context": b.ctx, "width": 1500, "height": 1300})
                print("window rect fallback ok")
            except Exception as e2:
                print("setWindowRect failed:", e2)
        await b.navigate("https://www.facebook.com/marketplace/bangkok/search/?query=laptop%20rtx&sortBy=creation_time_descend&daysSinceListed=30&radius=500")
        await asyncio.sleep(7)
        print("inner:", await b.js("window.innerHeight"), "count:", await b.js(COUNT))
        for i in range(24):
            r = await b.js(STEP % 500)
            await asyncio.sleep(0.9)
            if i % 4 == 0:
                print(f"  step {i}: {r} count={await b.js(COUNT)}")
        print("final count:", await b.js(COUNT))

asyncio.run(main())
