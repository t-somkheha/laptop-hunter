#!/usr/bin/env python3
"""Attach to the running remote agent and check: are we logged into Facebook?"""
import asyncio, json, itertools
import websockets


async def main():
    ws = await websockets.connect("ws://127.0.0.1:9222/session",
                                  max_size=200 * 1024 * 1024, ping_interval=None)
    ids = itertools.count(1)

    async def send(method, params=None):
        mid = next(ids)
        await ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        while True:
            msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=90))
            if msg.get("id") == mid:
                if msg.get("type") == "error":
                    raise RuntimeError(f"{method}: {msg.get('error')}")
                return msg.get("result", {})

    try:
        r = await send("session.new", {"capabilities": {}})
        print("session.new:", json.dumps(r)[:200])
    except Exception as e:
        print("session.new failed (may already exist):", e)

    tree = await send("browsingContext.getTree")
    ctx = tree["contexts"][0]["context"]
    print("context:", ctx)

    await send("browsingContext.navigate",
               {"context": ctx, "url": "https://www.facebook.com/marketplace/bangkok/",
                "wait": "complete"})
    await asyncio.sleep(6)

    async def js(expr):
        res = await send("script.evaluate", {"expression": expr,
                                            "target": {"context": ctx},
                                            "awaitPromise": True,
                                            "resultOwnership": "none"})
        return res.get("result", {}).get("value")

    print("title:", await js("document.title"))
    print("url:", await js("location.href"))
    print("login-ish:", await js("""(() => {
        const b = document.body ? document.body.innerText.slice(0, 300) : '';
        return {bodyHead: b.replace(/\\s+/g,' '), hasLoginForm: !!document.querySelector('input[name=email]'),
                hasMarketplaceNav: !!document.querySelector('a[href*="/marketplace"]')};
    })()"""))
    await ws.close()

asyncio.run(main())
