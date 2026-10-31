#!/usr/bin/env python3
"""imgsave.py — download the photographs for each listing into data/img/ so the sheet works offline.

    python3 imgsave.py            # every listing that has stored image urls
    python3 imgsave.py --missing  # only those with no local file yet
"""
import json, os, sys, time, urllib.request

import harvest

HERE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(HERE, "data", "img")
UA = ("Mozilla/5.0 (X11; Linux x86_64; rv:158.0) Gecko/20100101 Firefox/158.0")


def candidates():
    seen = {}
    for d in harvest.load_jsonl(harvest.DETAILS):
        urls = []
        if d.get("og_image"):
            urls.append(d["og_image"])
        urls += [u for u in (d.get("images") or []) if u not in urls]
        if urls:
            seen[d["id"]] = urls[:3]
    return seen


def main(argv):
    os.makedirs(IMG_DIR, exist_ok=True)
    todo = candidates()
    missing_only = "--missing" in argv
    saved = failed = skipped = 0
    for iid, urls in todo.items():
        for n, u in enumerate(urls):
            path = os.path.join(IMG_DIR, f"{iid}_{n}.jpg")
            if os.path.exists(path) and os.path.getsize(path) > 2000:
                skipped += 1
                continue
            if missing_only and os.path.exists(path):
                skipped += 1
                continue
            try:
                req = urllib.request.Request(u, headers={"User-Agent": UA, "Accept": "image/*"})
                with urllib.request.urlopen(req, timeout=25) as r, open(path, "wb") as f:
                    f.write(r.read())
                saved += 1
            except Exception as e:
                failed += 1
                if failed <= 6:
                    print(f"  ! {iid}_{n}: {str(e)[:90]}")
            time.sleep(0.15)
    n_files = len([f for f in os.listdir(IMG_DIR) if f.endswith(".jpg")])
    print(f"saved {saved}, skipped {skipped}, failed {failed}; {n_files} files in data/img")


if __name__ == "__main__":
    main(sys.argv[1:])
