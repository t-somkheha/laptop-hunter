#!/usr/bin/env python3
"""Find the scroll container FB Marketplace uses, and whether a wheel action loads more cards."""
import asyncio, json
import fb

COUNT = "[...document.querySelectorAll('a[href*=\"/marketplace/item/\"]')].length"

SCROLLERS = r"""
(() => {
  const out = [];
  document.querySelectorAll('div, main, section').forEach(e => {
    const s = getComputedStyle(e);
    if (/(auto|scroll)/.test(s.overflowY) && e.scrollHeight > e.clientHeight + 100 && e.clientHeight > 200) {
      out.push({tag: e.tagName, cls: (e.className || '').toString().slice(0, 60),
                sh: e.scrollHeight, ch: e.clientHeight, st: e.scrollTop});
    }
  });
  return {docSH: document.documentElement.scrollHeight, bodySH: document.body.scrollHeight,
          inner: window.innerHeight, scrollY: window.scrollY, scrollers: out.slice(0, 6)};
})()
"""


async def main():
    fb.start()
    async with fb.Browser() as b:
        await b.navigate("https://www.facebook.com/marketplace/bangkok/search/?query=laptop%20rtx&sortBy=creation_time_descend&daysSinceListed=30&radius=500")
        await asyncio.sleep(6)
        print("start count:", await b.js(COUNT))
        info = await b.js(SCROLLERS)
        print(json.dumps(info, ensure_ascii=False)[:900])

        # attempt 1: window scroll
        await b.js_stmt("window.scrollTo(0, 800); return window.scrollY;")
        await asyncio.sleep(3)
        print("after window scrollY=800:", await b.js(COUNT), "scrollY:", await b.js("window.scrollY"))

        # attempt 2: wheel via BiDi input
        for i in range(6):
            await b.send("input.performActions", {"context": b.ctx, "actions": [{
                "type": "wheel", "id": "w1", "actions": [
                    {"type": "scroll", "x": 600, "y": 500, "deltaX": 0, "deltaY": 900,
                     "duration": 200, "origin": "viewport"}]}]})
            await asyncio.sleep(1.6)
        print("after 6 wheel actions:", await b.js(COUNT), "y:", await b.js("window.scrollY"),
              "sh:", await b.js("document.documentElement.scrollHeight"))

        # attempt 3: scroll the inner scroller
        res = await b.js_stmt("""
          let n = 0;
          document.querySelectorAll('div').forEach(e => {
            const s = getComputedStyle(e);
            if (/(auto|scroll)/.test(s.overflowY) && e.scrollHeight > e.clientHeight + 100) {
              e.scrollTop = e.scrollHeight; n++;
            }
          });
          return n;
        """)
        await asyncio.sleep(3)
        print("inner scrollers moved:", res, "count:", await b.js(COUNT))

        # attempt 4: keyboard End
        await b.send("input.performActions", {"context": b.ctx, "actions": [{
            "type": "key", "id": "k1", "actions": [
                {"type": "keyDown", "value": "\ue00f"}, {"type": "keyUp", "value": "\ue00f"}]}]})
        await asyncio.sleep(3)
        print("after End key:", await b.js(COUNT))

asyncio.run(main())
