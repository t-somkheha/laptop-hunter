#!/usr/bin/env python3
"""Minimal WebDriver-BiDi client for Firefox's Remote Agent (--remote-debugging-port)."""
import asyncio, json, urllib.request, itertools

import websockets


class BiDi:
    def __init__(self, url):
        self.url = url
        self.ws = None
        self.ids = itertools.count(1)
        self.pending = {}

    @classmethod
    async def attach(cls, port=9222, host="127.0.0.1"):
        req = urllib.request.Request(
            f"http://{host}:{port}/session",
            data=json.dumps({"capabilities": {"alwaysMatch": {"webSocketUrl": True}}}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            body = json.loads(urllib.request.urlopen(req, timeout=20).read())
            ws_url = body["value"]["capabilities"]["webSocketUrl"]
        except Exception:
            # fall back to the bare session endpoint
            ws_url = f"ws://{host}:{port}/session"
        obj = cls(ws_url)
        obj.ws = await websockets.connect(ws_url, max_size=200 * 1024 * 1024, ping_interval=None)
        return obj

    async def send(self, method, params=None):
        mid = next(self.ids)
        await self.ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        while True:
            raw = await asyncio.wait_for(self.ws.recv(), timeout=120)
            msg = json.loads(raw)
            if msg.get("id") == mid:
                if msg.get("type") == "error":
                    raise RuntimeError(f"{method} failed: {msg.get('error')}")
                return msg.get("result", {})

    async def navigate(self, url, wait="complete"):
        tree = await self.send("browsingContext.getTree")
        ctx = tree["contexts"][0]["context"]
        res = await self.send("browsingContext.navigate",
                              {"context": ctx, "url": url, "wait": wait})
        return ctx, res

    async def js(self, ctx, expr, await_promise=True):
        res = await self.send("script.evaluate", {
            "expression": expr,
            "target": {"context": ctx},
            "awaitPromise": await_promise,
            "resultOwnership": "none",
        })
        if res.get("type") == "exception":
            raise RuntimeError(f"JS threw: {res.get('exception')}")
        val = res.get("result", {})
        return val.get("value")

    async def close(self):
        if self.ws:
            await self.ws.close()
