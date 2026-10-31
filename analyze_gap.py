#!/usr/bin/env python3
"""analyze_gap.py — which GPU families did the queries actually cover, and which never got asked.

Reads every card on file, resolves the GPU the card names, and reports how many cards came from a
query that mentioned that family. Anything in the "never queried" column is invisible by
construction — no amount of ranking can recover a listing we never searched for.
"""
import ast, re
from collections import Counter, defaultdict

import harvest, specs

QUERY_SETS = ("sweep_gpu.py", "sweep_oled2.py", "sweep_all.py", "sweep_gap.py")


def all_queries():
    qs = set()
    for f in QUERY_SETS:
        try:
            tree = ast.parse(open(f).read())
        except FileNotFoundError:
            continue
        for node in tree.body:
            if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "QUERIES":
                qs |= {q.lower() for q in ast.literal_eval(node.value)}
    return qs


def family(gpu_key):
    """Coarse family label used to decide whether a query ever asked for it."""
    if not gpu_key:
        return ""
    m = re.match(r"(rtx|gtx|rx|pro|arca|quadro)(\d{2,4})", gpu_key)
    return f"{m.group(1)} {m.group(2)}" if m else gpu_key


def main():
    qs = all_queries()
    blob = " || ".join(qs)
    cards = harvest.load_jsonl(harvest.CARDS)
    fams = Counter()
    covered = Counter()
    never = Counter()
    for c in cards:
        rec = specs.parse(c.get("card", ""))
        fam = family(rec.get("gpu_key"))
        if not fam:
            continue
        fams[fam] += 1
        digits = fam.split()[-1]
        prefix = fam.split()[0]
        if re.search(rf"\b{prefix}\s*{digits[:2]}", blob) or fam in blob:
            covered[fam] += 1
        else:
            never[fam] += 1

    print(f"{len(cards)} cards on file, {sum(fams.values())} name a GPU")
    print(f"{len(qs)} distinct query strings across {len(QUERY_SETS)} sweeps\n")
    print(f"{'GPU family':<14}{'cards':>7}{'asked for':>11}{'NEVER ASKED':>13}")
    for fam, n in fams.most_common(28):
        print(f"{fam:<14}{n:>7}{covered[fam]:>11}{never[fam]:>13}")
    if never:
        print("\ninvisible by construction:",
              ", ".join(f"{k} ({v})" for k, v in never.most_common(12)))


if __name__ == "__main__":
    main()
