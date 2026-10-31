#!/usr/bin/env python3
"""laptops.py — bang-for-buck laptop hunter for Facebook Marketplace (Bangkok, 500 km).

    python3 laptops.py harvest [--quick] [--limit=N]   # scrape cards + item pages
    python3 laptops.py report  [--top=N]               # rank what is on file
    python3 laptops.py site                            # build data/index.html
    python3 laptops.py watch                           # harvest, then report new finds only
    python3 laptops.py stop                            # kill the headless browser
"""
import asyncio, json, os, sys
import fb, harvest, report

DATA = harvest.DATA
LAST_REPORT = os.path.join(DATA, "last_report_ids.json")


def do_report(top=30, only_ids=None):
    rows, rejected = report.build()
    txt = report.render(rows, rejected, top=top, only_ids=only_ids)
    os.makedirs(DATA, exist_ok=True)
    with open(report.OUT_TXT, "w") as f:
        f.write(txt + "\n")
    print(txt)
    print("\nwritten to", report.OUT_TXT)
    qual = [r for r in rows if r.get("vram") and r["vram"] >= 12 and r.get("perf")]
    with open(LAST_REPORT, "w") as f:
        json.dump({"ids": [r["id"] for r in qual],
                   "when": harvest.now()}, f, indent=1)
    return qual


def main(argv):
    cmd = argv[0] if argv else "report"
    args = argv[1:]
    top = 30
    for a in args:
        if a.startswith("--top="):
            top = int(a.split("=", 1)[1])
    if cmd == "harvest":
        asyncio.run(harvest.main(args))
    elif cmd == "report":
        do_report(top=top)
    elif cmd == "site":
        import build_site
        build_site.main()
    elif cmd == "watch":
        seen = set()
        if os.path.exists(LAST_REPORT):
            seen = set(json.load(open(LAST_REPORT)).get("ids", []))
        asyncio.run(harvest.main(["--limit=120"] + args))
        rows, rejected = report.build()
        fresh = [r["id"] for r in rows
                 if r.get("vram") and r["vram"] >= 12 and r.get("perf") and r["id"] not in seen]
        print(f"\n{len(fresh)} new qualifying listings since the last report")
        do_report(top=top, only_ids=fresh or None)
    elif cmd == "stop":
        fb.stop()
        print("headless browser stopped")
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
