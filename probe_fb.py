#!/usr/bin/env python3
"""Probe: can we read FB Marketplace search results with the Firefox profile's cookies?"""
import os, shutil, sqlite3, glob, sys, json, http.cookiejar

HOME = os.path.expanduser("~")
PROFILE = os.environ.get("SRC_PROFILE", os.path.join(HOME, ".mozilla", "firefox"))
SCRATCH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".probe")
os.makedirs(SCRATCH, exist_ok=True)

src = os.path.join(PROFILE, "cookies.sqlite")
for suffix in ("", "-wal", "-shm"):
    p = src + suffix
    if os.path.exists(p):
        shutil.copy2(p, os.path.join(SCRATCH, "cookies.sqlite" + suffix))

con = sqlite3.connect(os.path.join(SCRATCH, "cookies.sqlite"))
rows = con.execute(
    "SELECT host, name, length(value), expiry FROM moz_cookies WHERE host LIKE '%facebook%'"
).fetchall()
print("=== facebook-ish cookies ===")
for host, name, ln, exp in sorted(rows):
    print(f"{host:32s} {name:28s} len={ln:5d}")
names = {n for _, n, _, _ in rows}
print("\nhas c_user:", "c_user" in names, "| has xs:", "xs" in names, "| has datr:", "datr" in names)
con.close()

# Build a requests session with the cookies
import requests
jar = requests.cookies.RequestsCookieJar()
con = sqlite3.connect(os.path.join(SCRATCH, "cookies.sqlite"))
for host, name, value, path in con.execute(
    "SELECT host, name, value, path FROM moz_cookies WHERE host LIKE '%facebook%'"
):
    jar.set(name, value, domain=host.lstrip('.') if host.startswith('.') else host, path=path or "/")
con.close()

HDRS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:158.0) Gecko/20100101 Firefox/158.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Upgrade-Insecure-Requests": "1",
}
s = requests.Session()
s.cookies = jar
s.headers.update(HDRS)

urls = [
    "https://www.facebook.com/marketplace/bangkok/search/?query=rtx%204080%20laptop",
    "https://www.facebook.com/marketplace/bangkok/search/?query=laptop&sortBy=creation_time_descend&daysSinceListed=7",
]
for u in urls:
    try:
        r = s.get(u, timeout=30, allow_redirects=True)
        body = r.text
        out = os.path.join(SCRATCH, "probe_%d.html" % abs(hash(u)))
        open(out, "w").write(body)
        print(f"\n--- {u}\nstatus={r.status_code} final={r.url} bytes={len(body)}")
        for marker in ["marketplace_listing", "marketplace_search", "listing_price",
                       "ServerJS", "login_form", "__csr", "\"marketplace\""]:
            print(f"   marker {marker!r}: {body.count(marker)}")
        print("   saved:", out)
    except Exception as e:
        print("ERR", u, repr(e))
