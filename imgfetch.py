#!/usr/bin/env python3
"""imgfetch.py — re-read item pages that were captured before photographs were recorded.

    FB_PORT=9222 FB_PROFILE=.ffprofile python3 imgfetch.py 0 3 400

Every record written before DETAIL_JS learned about `images` has none. This walks those ids,
lets the carousel load, and rewrites each record in place — price and description come along
fresh, which is no bad thing either.
"""
import asyncio, json, sys
import harvest


def needs_images(argv):
    have = {}
    for r in harvest.load_jsonl(harvest.DETAILS):
        have[r["id"]] = r
    only = None
    for a in argv:
        if a.startswith("--ids="):
            with open(a.split("=", 1)[1]) as f:
                only = [ln.strip() for ln in f if ln.strip()]
    cands = only if only else [c["id"] for c in harvest.load_jsonl(harvest.CARDS)
                               if harvest.card_is_candidate(c["card"])]
    todo = []
    for iid in cands:
        r = have.get(iid)
        if not r or not r.get("body"):
            continue
        if r.get("images") or r.get("og_image"):
            continue
        todo.append(iid)
    return todo, len(cands)


async def run(b, ids, pause=3.0):
    out = []
    for n, iid in enumerate(ids, 1):
        try:
            await b.navigate(f"https://www.facebook.com/marketplace/item/{iid}/")
            await asyncio.sleep(pause + (n % 3) * 0.6)
            d = await b.js(harvest.DETAIL_JS)
            d["id"] = iid
            d["fetched"] = harvest.now()
            out.append(d)
            if n % 20 == 0:
                print(f"    {n}/{len(ids)}")
        except Exception as e:
            print(f"    ! {iid}: {e}")
    return out


def main(argv):
    idx, total = 0, 1
    cap = None
    import re as _re
    for a in argv:
        if _re.fullmatch(r"\d+/\d+", a):
            i, n = a.split("/")
            idx, total = int(i), int(n)
        elif a.isdigit():
            cap = int(a)
    todo, ncands = needs_images(argv)
    todo = [t for i, t in enumerate(todo) if i % total == idx]
    if cap:
        todo = todo[:cap]
    print(f"{ncands} listings in scope, {len(todo)} pages need photographs (shard {idx}/{total})")
    if not todo:
        return

    async def go(b):
        fresh = await run(b, todo)
        if fresh:
            ids = {r["id"] for r in fresh}
            old = [r for r in harvest.load_jsonl(harvest.DETAILS) if r["id"] not in ids]
            with open(harvest.DETAILS, "w") as f:
                for r in old + fresh:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
        got = sum(1 for r in fresh if r.get("images") or r.get("og_image"))
        print(f"re-read {len(fresh)}, {got} carry photographs")

    asyncio.run(harvest.with_browser(go))


if __name__ == "__main__":
    main(sys.argv[1:])
