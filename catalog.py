#!/usr/bin/env python3
"""catalog.py — model-level specifications, cached on disk, for the fields sellers never state.

Only model-invariant facts are taken from a catalogue: panel type, resolution, refresh rate,
weight, battery, port layout, OS family. RAM, storage, CPU and GPU are configuration choices and
must come from the listing itself — filling those from a press release would be inventing.

    from catalog import key_of, merge, lookup
    key_of("ASUS ROG Zephyrus G16 GU605M RTX 4060")   -> 'asus zephyrus g16 gu605m'
    merge(key, page_text, url)                        -> fills and saves
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "data", "catalog.json")

BRANDS = ["asus", "acer", "lenovo", "hp", "dell", "msi", "razer", "gigabyte", "aorus",
          "alienware", "samsung", "lg", "huawei", "xiaomi", "apple", "toshiba", "fujitsu",
          "honor", "realme", "infinity", "colorful", "thunderobot", "hasee", "maibenben"]

SERIES = [
    "zephyrus g14", "zephyrus g16", "zephyrus duo", "zephyrus m16", "strix scar", "strix g16",
    "strix g17", "tuf gaming", "tuf dash", "proart studiobook", "proart p16", "vivobook pro",
    "zenbook pro", "rog flow", "rog ally",
    "predator helios neo", "predator helios", "predator triton", "nitro v", "nitro 5", "swift x",
    "legion pro 7", "legion pro 5", "legion slim 5", "legion 9", "legion 7", "legion 5",
    "loq", "ideapad pro", "yoga pro", "thinkpad p16", "thinkpad p1",
    "omen transcend", "omen 16", "omen 17", "omen 15", "victus", "spectre x360", "envy",
    "raider ge78", "raider ge68", "vector 16", "stealth 16", "stealth 15", "katana 15",
    "katana a15", "titan 18", "creator z16", "prestige 16", "sword 16",
    "blade 16", "blade 14", "blade 15",
    "aorus 16x", "aorus 15", "aero 16",
    "alienware m16", "alienware m18", "alienware x16",
    "xps 15", "xps 16", "xps 17", "precision 5680", "precision 7680", "precision 7780",
    "galaxy book", "gram",
]

# model codes that pin down the chassis (used when no series name is written)
CODE = re.compile(r"\b([a-z]{2,4}\d{3}[a-z]{0,3}(?:-\d{2}[a-z0-9]{0,2})?|\d{2}[a-z]{3}\d{1,2}[a-z]{0,2})\b", re.I)

FIELDS = {
    "resolution": [r"(\d{4})\s*[x×]\s*(\d{3,4})",
                   r"\b(1920|2560|2880|3200|3456|3840)\s*[x×]\s*(1080|1200|1440|1600|1620|1800|2000|2160)"],
    "panel": [r"\b(OLED|Mini-?LED|IPS|VA|TN)\b"],
    "refresh": [r"(\d{2,3})\s*Hz"],
    "weight": [r"(\d(?:\.\d{1,2})?)\s*kg"],
    "battery": [r"(\d{2,3})\s*Wh"],
    "screen": [r"(\d{2}(?:\.\d)?)[\s-]*(?:inch|\"|”|นิ้ว)"],
}


def load():
    if not os.path.exists(PATH):
        return {}
    try:
        with open(PATH) as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def save(cat):
    os.makedirs(os.path.dirname(PATH), exist_ok=True)
    with open(PATH, "w") as f:
        json.dump(cat, f, ensure_ascii=False, indent=1)


def key_of(title):
    """Best-effort model identity: brand + series + (model code or chassis size).

    A bare series name is not an identity — "HP Victus" covers 15-inch, 16-inch and 16.1-inch
    chassis with different panels. Prefer a model code when the seller wrote one, otherwise
    anchor on the screen size the title mentions.
    """
    raw = title or ""
    low = " " + re.sub(r"[^a-z0-9\.\" -]+", " ", raw.lower()) + " "
    brand = next((b for b in BRANDS if f" {b} " in low or low.startswith(f" {b}")), "")
    series = next((s for s in SERIES if s in low), "")

    code = ""
    m = re.search(r"\b([a-z]{1,4}-?\d{3,4}[a-z]{0,3}(?:-[a-z0-9]{2,6}){0,2})\b", raw, re.I)
    if m and re.search(r"[a-z]", m.group(1), re.I) and re.search(r"\d", m.group(1)):
        code = m.group(1).lower()

    size = ""
    s = re.search(r'\b(1[3-9](?:\.\d)?)\s*(?:"|”|inch|นิ้ว|Inch)', raw, re.I)
    if s:
        size = s.group(1)
    elif re.search(r"\b(1[3-9])\s*(?:inch|นิ้ว)\b", raw, re.I):
        size = re.search(r"\b(1[3-9])\s*(?:inch|นิ้ว)", raw, re.I).group(1)

    parts = [brand, series]
    if code:
        parts.append(code)
    elif size:
        parts.append(f"{size}in")
    if not series and not code:
        return ""
    return " ".join(p for p in parts if p).strip()


VALID = {
    "screen": (11.0, 18.5),
    "weight": (0.9, 4.5),
    "battery": (30, 100),
    "refresh": (50, 540),
}
REFRESH_OK = {60, 75, 90, 120, 144, 165, 240, 300, 360, 480, 500, 540}


def _plausible(field, value, key, text):
    """A catalogue value must be physically sane AND supported by the page's own words."""
    if field in VALID:
        lo, hi = VALID[field]
        if not (lo <= float(value) <= hi):
            return False
    if field == "refresh" and int(value) not in REFRESH_OK:
        return False
    if field == "battery" and not re.search(rf"{value}\s*Wh", text, re.I):
        return False
    if field == "weight" and not re.search(rf"{str(value)[:4]}\s*kg", text, re.I):
        return False
    # the page has to actually be about this machine
    for tok in [t for t in key.split() if len(t) > 2][:2]:
        if tok not in text.lower():
            return False
    return True


CODE_TOKEN = re.compile(r"[a-z]{1,4}-?\d{3,}")


def merge(key, text, url=""):
    """Extract model-invariant fields from a spec page and cache them under `key`.

    A series name alone is not enough to hang specifications on: "asus tuf gaming" covers a
    dozen chassis with different panels, and a lookup against that name quietly returns
    whichever one ranks best. Only keys carrying a real model code may be filled.
    """
    if not key or not text:
        return None
    if not CODE_TOKEN.search(key):
        return None
    cat = load()
    got = {}
    for field, pats in FIELDS.items():
        for pat in pats:
            m = re.search(pat, text, re.I)
            if not m:
                continue
            if field == "resolution":
                got[field] = f"{m.group(1)} × {m.group(2)}"
            elif field == "panel":
                got[field] = m.group(1).upper().replace("MINILED", "Mini-LED")
            elif field == "refresh":
                v = int(m.group(1))
                if not (40 <= v <= 540):
                    continue
                got[field] = v
            elif field == "screen":
                got[field] = float(m.group(1))
            else:
                got[field] = float(m.group(1)) if field == "weight" else int(m.group(1))
            if not _plausible(field, got[field], key, text):
                got.pop(field, None)
                continue
            break
    if not got:
        return None
    entry = cat.get(key, {})
    entry.update(got)
    entry["source"] = url
    entry["key"] = key
    cat[key] = entry
    save(cat)
    return entry


def lookup(key):
    return load().get(key, {}) if key else {}


if __name__ == "__main__":
    import sys
    cat = load()
    print(f"{len(cat)} model entries cached at {PATH}")
    for k, v in list(cat.items())[:15]:
        print(" ", k, "->", {f: v[f] for f in ("screen", "resolution", "panel", "refresh",
                                               "weight", "battery") if f in v})
