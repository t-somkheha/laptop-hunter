#!/usr/bin/env python3
"""Build a minimal Firefox profile carrying only the Facebook session.

Copies cookies and NSS key material out of a real Firefox profile into a scratch profile, then
deletes every cookie that is not a Facebook one. The result is what the headless browser uses —
your live profile is only ever read, never locked or modified.

    SRC_PROFILE=/path/to/<id>.default-release OUT=${1:-.ffprofile} python3 make_profile.py
"""
import os, shutil, sqlite3, sys

HOME = os.path.expanduser("~")
SRC = os.environ.get("SRC_PROFILE", "")
if not SRC:
    base = os.path.join(HOME, ".mozilla", "firefox")
    cands = [os.path.join(base, d) for d in (os.listdir(base) if os.path.isdir(base) else [])
             if d.endswith(".default-release") or d.endswith(".default")]
    if not cands:
        sys.exit("no Firefox profile found — set SRC_PROFILE")
    SRC = max(cands, key=os.path.getmtime)
DST = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".ffprofile")

os.makedirs(DST, exist_ok=True)

# 1. cookies (copy + wal/shm so nothing unflushed is lost)
for suffix in ("", "-wal", "-shm"):
    p = os.path.join(SRC, "cookies.sqlite" + suffix)
    if os.path.exists(p):
        shutil.copy2(p, os.path.join(DST, "cookies.sqlite" + suffix))

# trim to facebook domains only
con = sqlite3.connect(os.path.join(DST, "cookies.sqlite"))
n_before = con.execute("SELECT count(*) FROM moz_cookies").fetchone()[0]
con.execute("DELETE FROM moz_cookies WHERE host NOT LIKE '%facebook%'")
con.commit()
n_after = con.execute("SELECT count(*) FROM moz_cookies").fetchone()[0]
con.close()
print(f"cookies: {n_before} -> {n_after} kept")

# 2. NSS key material (needed to decrypt any cookie stored with OS crypt)
for f in ("key4.db", "cert9.db", "pkcs11.txt"):
    p = os.path.join(SRC, f)
    if os.path.exists(p):
        shutil.copy2(p, os.path.join(DST, f))

# 3. minimal prefs
prefs = """// minimal automation profile for marketplace harvesting
user_pref("browser.shell.checkDefaultBrowser", false);
user_pref("browser.startup.homepage_override.mstone", "ignore");
user_pref("browser.startup.page", 0);
user_pref("browser.tabs.warnOnClose", false);
user_pref("datareporting.policy.dataSubmissionEnabled", false);
user_pref("toolkit.telemetry.enabled", false);
user_pref("app.update.enabled", false);
user_pref("browser.sessionstore.resume_from_crash", false);
user_pref("signon.rememberSignons", false);
user_pref("remote.prefs.recommended", true);
user_pref("dom.disable_beforeunload", true);
user_pref("browser.warnOnQuit", false);
user_pref("xpinstall.signatures.required", false);
user_pref("browser.tabs.loadInBackground", true);
user_pref("network.cookie.sameSite.noneRequiresSecure", true);
user_pref("browser.newtabpage.activity-stream.feeds.telemetry", false);
user_pref("browser.chrome.errorReporter.enabled", false);
"""
open(os.path.join(DST, "prefs.js"), "w").write(prefs)
print("profile at", DST)
for f in sorted(os.listdir(DST)):
    print("  ", f, os.path.getsize(os.path.join(DST, f)))
