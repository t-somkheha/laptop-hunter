#!/usr/bin/env python3
"""fb.py — control a headless Firefox that carries Jinshi's Facebook session.

Firefox's Remote Agent (--remote-debugging-port) speaks WebDriver BiDi. One session
at a time is allowed, so every entry point creates a session and ends it on exit.
"""
import asyncio, itertools, json, os, subprocess, sys, time, urllib.request
import websockets

HERE = os.path.dirname(os.path.abspath(__file__))
# A second worker runs on another port with its own profile copy: FB's 24-cards-per-slice
# wall makes query count the only lever on coverage, so the sweep is split across both.
PORT = int(os.environ.get("FB_PORT", "9222"))
PROFILE = os.path.join(HERE, os.environ.get("FB_PROFILE", ".ffprofile"))
PIDFILE = os.path.join(HERE, f".ff-{PORT}.pid")
LOGFILE = os.path.join(HERE, f".ff-{PORT}.log")
FIREFOX = "/usr/bin/firefox"


def _port_alive():
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{PORT}/session", timeout=2)
        return True
    except urllib.error.HTTPError:
        return True          # responds, just not to GET /session — agent is up
    except Exception:
        return False


def start(force=False):
    """Launch the headless instance if it is not already listening. Returns True if we started it."""
    if _port_alive():
        return False
    if force:
        stop()
    if not os.path.exists(os.path.join(PROFILE, "cookies.sqlite")):
        raise SystemExit("no profile — run make_profile.py first")
    env = dict(os.environ, MOZ_HEADLESS="1")
    log = open(LOGFILE, "ab")
    p = subprocess.Popen(
        [FIREFOX, "--profile", PROFILE, "--remote-debugging-port", str(PORT),
         "--no-remote", "--headless", "about:blank"],
        stdout=log, stderr=log, env=env, start_new_session=True,
    )
    open(PIDFILE, "w").write(str(p.pid))
    for _ in range(40):
        time.sleep(0.5)
        if _port_alive():
            return True
    raise SystemExit("firefox remote agent did not come up; see " + LOGFILE)


def stop():
    pid = None
    if os.path.exists(PIDFILE):
        try:
            pid = int(open(PIDFILE).read().strip())
        except ValueError:
            pid = None
    if pid:
        try:
            os.kill(pid, 15)
            for _ in range(20):
                time.sleep(0.25)
                os.kill(pid, 0)
        except ProcessLookupError:
            pass
        except PermissionError:
            pass
    if os.path.exists(PIDFILE):
        os.remove(PIDFILE)

    # A pidfile goes stale if the browser was started by an older version of this script,
    # or if a different worker owns the port. Find the real owner by its command line.
    marker = f"--remote-debugging-port {PORT}"
    killed = 0
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        try:
            with open(f"/proc/{entry}/cmdline", "rb") as f:
                cmd = f.read().replace(b"\0", b" ").decode("utf-8", "ignore")
        except (OSError, IOError):
            continue
        if marker in cmd and "firefox" in cmd and f"--profile {PROFILE}" in cmd:
            try:
                os.kill(int(entry), 15)
                killed += 1
            except (ProcessLookupError, PermissionError):
                pass
    if killed:
        for _ in range(24):
            time.sleep(0.25)
            if not _port_alive():
                break
    return killed


class Browser:
    """Attach, create one session, run coroutines with .js()/.navigate()."""

    def __init__(self):
        self.ws = None
        self.ids = itertools.count(1)
        self.ctx = None

    async def __aenter__(self):
        self.ws = await websockets.connect(f"ws://127.0.0.1:{PORT}/session",
                                           max_size=256 * 1024 * 1024, ping_interval=None)
        await self.send("session.new", {"capabilities": {}})
        tree = await self.send("browsingContext.getTree")
        self.ctx = tree["contexts"][0]["context"]
        return self

    async def __aexit__(self, *exc):
        try:
            await self.send("session.end", {})
        except Exception:
            pass
        try:
            await self.ws.close()
        except Exception:
            pass

    async def send(self, method, params=None, timeout=120):
        mid = next(self.ids)
        await self.ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        while True:
            msg = json.loads(await asyncio.wait_for(self.ws.recv(), timeout=timeout))
            if msg.get("id") == mid:
                if msg.get("type") == "error":
                    raise RuntimeError(f"{method}: {msg.get('error')}")
                return msg.get("result", {})

    async def navigate(self, url, wait="none"):
        """wait='none' — FB keeps sockets open for its own polling, so 'complete' never
        arrives promptly. Sleep explicitly after calling this instead."""
        await self.send("browsingContext.navigate", {"context": self.ctx, "url": url, "wait": wait})

    async def js(self, expr, timeout=120):
        return await self._eval("JSON.stringify((%s))" % expr.strip(), timeout)

    async def js_stmt(self, stmts, timeout=120):
        """Evaluate a statement block (use for scrolling, loops, multi-step DOM work)."""
        return await self._eval("JSON.stringify((() => { %s })())" % stmts.strip(), timeout)

    async def _eval(self, wrapped, timeout=120):
        res = await self.send("script.evaluate", {
            "expression": wrapped, "target": {"context": self.ctx},
            "awaitPromise": True, "resultOwnership": "none"}, timeout=timeout)
        if res.get("type") == "exception":
            raise RuntimeError("JS: " + json.dumps(res.get("exception"))[:400])
        val = res.get("result", {}).get("value")
        if isinstance(val, str):
            try:
                return json.loads(val)
            except Exception:
                return val
        return val

    async def text(self):
        return await self.js("document.body ? document.body.innerText : ''")
