#!/usr/bin/env python3
"""watch_snapshot.py — record the current card pool so a later run can tell what is new."""
import datetime, json, os, sys
import harvest

STATE = os.path.join(harvest.DATA, "watch_state.json")


def main():
    cards = harvest.load_jsonl(harvest.CARDS)
    ids = sorted({c["id"] for c in cards})
    state = {"ids": ids, "at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
             "cards": len(cards)}
    os.makedirs(harvest.DATA, exist_ok=True)
    with open(STATE, "w") as f:
        json.dump(state, f)
    print(f"snapshot: {len(ids)} unique ids from {len(cards)} cards at {state['at']}")


if __name__ == "__main__":
    main()
