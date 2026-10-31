#!/usr/bin/env python3
"""new_listings.py — diff the current pool against the last snapshot and report what is new.

    python3 new_listings.py            # show new finds, then advance the snapshot
    python3 new_listings.py --peek     # show without advancing

A "new" listing is a card id that did not exist at snapshot time. Its specs come from the
item page when one has been read; a new card without a detail page is reported as unverified
rather than guessed at.
"""
import datetime, json, os, sys
import harvest, report, specs

STATE = os.path.join(harvest.DATA, "watch_state.json")


def main(argv):
    peek = "--peek" in argv
    if not os.path.exists(STATE):
        print("no snapshot yet — run watch_snapshot.py first")
        return
    state = json.load(open(STATE))
    known = set(state["ids"])

    cards = harvest.load_jsonl(harvest.CARDS)
    fresh_ids = []
    seen = set()
    for c in cards:
        if c["id"] in seen or c["id"] in known:
            continue
        seen.add(c["id"])
        fresh_ids.append(c["id"])

    rows, rejected = report.build()
    by_id = {r["id"]: r for r in rows}
    fresh = [by_id[i] for i in fresh_ids if i in by_id]
    missing = [i for i in fresh_ids if i not in by_id]

    rtx = __import__("oled_report")
    oled_hits = [r for r in fresh if r.get("oled") and r.get("price") and rtx.is_rtx(r)
                 and r.get("laptop", True) and not r.get("dead")]
    vram_hits = [r for r in fresh if r.get("vram") and r["vram"] >= 12 and r.get("perf")
                 and r.get("price") and not r.get("dead")]
    oled_hits.sort(key=lambda r: r["price"])
    vram_hits.sort(key=lambda r: r.get("value") or 0, reverse=True)

    print(f"snapshot taken {state['at']} with {len(known)} ids")
    print(f"now: {len(cards)} cards, {len(rows)} parsed, {len(fresh_ids)} unseen ids\n")

    print(f"NEW OLED + dedicated RTX: {len(oled_hits)}")
    for r in oled_hits:
        print(f"  ฿{r['price']:,}  {r['title'][:72]}")
        print(f"      {r['gpu']} {r['vram']}GB | {r['screen'] or '?'}\" OLED | "
              f"{r.get('location') or '?'} | {r.get('condition') or '?'}")
        print(f"      {r['url']}")

    print(f"\nNEW with VRAM >= 12 GB: {len(vram_hits)}")
    for r in vram_hits:
        print(f"  ฿{r['price']:,}  {r['gpu']} {r['vram']}GB | {r['title'][:60]} | {r['url']}")

    unverified = [i for i in fresh_ids if i in missing]
    print(f"\nnew ids without a readable spec: {len(unverified)}")
    for i in unverified[:12]:
        c = next((x for x in cards if x["id"] == i), None)
        if c:
            print(f"  {(c.get('card') or '')[:90]}")

    if not peek:
        new_state = {"ids": sorted({c["id"] for c in cards}),
                     "at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
                     "cards": len(cards)}
        json.dump(new_state, open(STATE, "w"))
        print(f"\nsnapshot advanced to {new_state['cards']} cards")


if __name__ == "__main__":
    main(sys.argv[1:])
