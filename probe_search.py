#!/usr/bin/env python3
"""Probe: card DOM shape, radius param behaviour, item-page detail fields."""
import asyncio, json, sys
import fb

EXTRACT = r"""
(() => {
  const items = [], seen = new Set();
  document.querySelectorAll('a[href*="/marketplace/item/"]').forEach(a => {
    const m = a.getAttribute('href').match(/\/marketplace\/item\/(\d+)/);
    if (!m) return;
    const id = m[1];
    const t = (a.innerText || '').split('\n').map(s => s.trim()).filter(Boolean);
    if (!t.length) return;
    if (seen.has(id)) return;
    seen.add(id);
    items.push({id, text: t});
  });
  const side = document.body.innerText.split('\n')
      .filter(l => /Within|Bangkok|km/.test(l)).slice(0, 8);
  return {count: items.length, items: items.slice(0, 6), side,
          url: location.href};
})()
"""


async def main():
    fb.start()
    queries = {
        "A_default": "https://www.facebook.com/marketplace/bangkok/search/?query=rtx%20laptop&sortBy=creation_time_descend&daysSinceListed=7",
        "B_radius500": "https://www.facebook.com/marketplace/bangkok/search/?query=rtx%20laptop&sortBy=creation_time_descend&daysSinceListed=7&radius=500",
        "C_radius500km": "https://www.facebook.com/marketplace/bangkok/search/?query=rtx%20laptop&sortBy=creation_time_descend&daysSinceListed=7&radius=500km",
    }
    async with fb.Browser() as b:
        for label, url in queries.items():
            await b.navigate(url)
            await asyncio.sleep(6)
            for _ in range(2):
                await b.js_stmt("window.scrollBy(0, document.body.scrollHeight); return 1;")
                await asyncio.sleep(2.5)
            d = await b.js(EXTRACT)
            print(f"\n===== {label}: {d['count']} cards")
            print("  url:", d["url"][:140])
            print("  side:", d["side"])
            for it in d["items"][:4]:
                print("   ", it["id"], "|", " / ".join(it["text"][:4])[:130])

        # item page detail
        d = await b.js(EXTRACT)
        if d["count"]:
            iid = d["items"][0]["id"]
            await b.navigate(f"https://www.facebook.com/marketplace/item/{iid}/")
            await asyncio.sleep(6)
            body = await b.text()
            print(f"\n===== item {iid} body (first 1400 chars)")
            print(body[:1400])
            extra = await b.js("""(() => {
              const meta = [...document.querySelectorAll('div,span')]
                .map(e => e.innerText || '')
                .filter(t => t && t.length < 200 && /฿|บาท|km|Bangkok|Used|New|Condition/.test(t))
                .slice(0, 25);
              return [...new Set(meta)];
            })()""")
            print("\nfragments:", json.dumps(extra, ensure_ascii=False)[:1200])

asyncio.run(main())
