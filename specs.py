#!/usr/bin/env python3
"""specs.py — laptop hardware knowledge base + listing text parser + bang-for-buck scoring.

VRAM figures for every >=12 GB entry were verified against spec sheets
(videocardz / hmc-tech / notebookcheck).  The perf index is a RELATIVE class index
(RTX 5090 Laptop = 100, i9-14900HX = 100), i.e. order-of-magnitude correct, not a
benchmark reading.
"""
import re

# ---------------------------------------------------------------- GPU table
# key -> (display name, vram_gb, perf_index)
GPUS = {
    "rtx5090":        ("RTX 5090 Laptop", 24, 100),
    "rtx5080":        ("RTX 5080 Laptop", 16, 82),
    "rtx5070ti":      ("RTX 5070 Ti Laptop", 12, 62),
    "rtx5070":        ("RTX 5070 Laptop", 8, 48),
    "rtx5060":        ("RTX 5060 Laptop", 8, 33),
    "rtx4090":        ("RTX 4090 Laptop", 16, 84),
    "rtx4080":        ("RTX 4080 Laptop", 12, 68),
    "rtx4070":        ("RTX 4070 Laptop", 8, 42),
    "rtx4060":        ("RTX 4060 Laptop", 8, 30),
    "rtx3080ti":      ("RTX 3080 Ti Laptop", 16, 60),
    "rtx3080":        ("RTX 3080 Laptop", 16, 54),   # 16 GB variant wins by default
    "rtx3070ti":      ("RTX 3070 Ti Laptop", 8, 38),
    "rtx3070":        ("RTX 3070 Laptop", 8, 34),
    "rtx3050ti":      ("RTX 3050 Ti Laptop", 4, 16),
    "rtx3050":        ("RTX 3050 Laptop", 4, 14),
    "rtx3060":        ("RTX 3060 Laptop", 6, 24),
    "rtx2080super":   ("RTX 2080 Super Laptop", 8, 28),
    "rtx2080":        ("RTX 2080 Laptop", 8, 26),
    "rtx2070":        ("RTX 2070 Laptop", 8, 22),
    "rtx2070super":   ("RTX 2070 Super Laptop", 8, 24),
    "rtx2060":        ("RTX 2060 Laptop", 6, 18),
    "rtx2050":        ("RTX 2050 Laptop", 4, 11),
    "rtx4050":        ("RTX 4050 Laptop", 6, 24),
    "rtx5050":        ("RTX 5050 Laptop", 8, 28),
    "gtx1660ti":      ("GTX 1660 Ti Laptop", 6, 20),
    "gtx1650ti":      ("GTX 1650 Ti Laptop", 4, 14),
    "gtx1650":        ("GTX 1650 Laptop", 4, 12),
    "gtx1080":        ("GTX 1080 Laptop", 8, 18),
    "gtx1070":        ("GTX 1070 Laptop", 8, 16),
    "gtx1060":        ("GTX 1060 Laptop", 6, 12),
    "gtx1050ti":      ("GTX 1050 Ti Laptop", 4, 8),
    "gtx1050":        ("GTX 1050 Laptop", 4, 7),
    "rtx5000ada":     ("RTX 5000 Ada Laptop", 16, 60),
    "rtx4000ada":     ("RTX 4000 Ada Laptop", 12, 44),
    "rtx3500ada":     ("RTX 3500 Ada Laptop", 12, 36),
    "rtx3000ada":     ("RTX 3000 Ada Laptop", 8, 26),
    "rtxa5500":       ("RTX A5500 Laptop", 16, 50),
    "rtxa4500":       ("RTX A4500 Laptop", 16, 40),
    "rtxa4000":       ("RTX A4000 Laptop", 8, 28),
    "rtxa3000":       ("RTX A3000 Laptop", 6, 20),
    "quadrortx5000":  ("Quadro RTX 5000 Laptop", 16, 26),
    "rtxpro5000":     ("RTX PRO 5000 Blackwell Laptop", 24, 98),
    "rtxpro4000":     ("RTX PRO 4000 Blackwell Laptop", 16, 66),
    "rx7900m":        ("Radeon RX 7900M", 16, 58),
    "rx6850mxt":      ("Radeon RX 6850M XT", 12, 42),
    "rx6800m":        ("Radeon RX 6800M", 12, 40),
    "rx6700m":        ("Radeon RX 6700M", 10, 28),
    "rx7600mxt":      ("Radeon RX 7600M XT", 8, 22),
    "rx7600m":        ("Radeon RX 7600M", 8, 20),
    "rx7700s":        ("Radeon RX 7700S", 8, 21),
    "rx7600s":        ("Radeon RX 7600S", 8, 18),
    "rx6800s":        ("Radeon RX 6800S", 8, 26),
    "rx6600m":        ("Radeon RX 6600M", 8, 19),
    "rx6600s":        ("Radeon RX 6600S", 4, 14),
    "rx6500m":        ("Radeon RX 6500M", 4, 11),
    "rx5600m":        ("Radeon RX 5600M", 6, 13),
    "rx5500m":        ("Radeon RX 5500M", 4, 9),
    "pro5600m":       ("Radeon Pro 5600M", 8, 15),
    "pro5500m":       ("Radeon Pro 5500M", 4, 9),
    "arca770m":       ("Intel Arc A770M", 16, 32),
    "arca730m":       ("Intel Arc A730M", 12, 24),
    "arca570m":       ("Intel Arc A570M", 8, 16),
}

# patterns tried in order; longer/more specific keys first
_GPU_PATTERNS = [
    (r"rtx\s*pro\s*5000", "rtxpro5000"), (r"rtx\s*pro\s*4000", "rtxpro4000"),
    (r"rtx\s*5000\s*ada", "rtx5000ada"), (r"rtx\s*4000\s*ada", "rtx4000ada"),
    (r"rtx\s*3500\s*ada", "rtx3500ada"), (r"rtx\s*3000\s*ada", "rtx3000ada"),
    (r"rtx\s*a\s*5500", "rtxa5500"), (r"rtx\s*a\s*4500", "rtxa4500"),
    (r"rtx\s*a\s*4000", "rtxa4000"), (r"rtx\s*a\s*3000", "rtxa3000"),
    (r"quadro\s*rtx\s*5000", "quadrortx5000"),
    (r"rtx\s*50\s*90", "rtx5090"), (r"rtx\s*50\s*80", "rtx5080"),
    (r"rtx\s*50\s*70\s*ti", "rtx5070ti"), (r"rtx\s*50\s*70", "rtx5070"),
    (r"rtx\s*50\s*60", "rtx5060"),
    (r"rtx\s*40\s*90", "rtx4090"), (r"rtx\s*40\s*80", "rtx4080"),
    (r"rtx\s*40\s*70", "rtx4070"), (r"rtx\s*40\s*60", "rtx4060"),
    (r"rtx\s*30\s*60", "rtx3060"),
    (r"rtx\s*30\s*50\s*ti", "rtx3050ti"), (r"rtx\s*30\s*50", "rtx3050"),
    (r"rtx\s*30\s*80\s*ti", "rtx3080ti"), (r"rtx\s*30\s*80", "rtx3080"),
    (r"rtx\s*30\s*70\s*ti", "rtx3070ti"), (r"rtx\s*30\s*70", "rtx3070"),
    (r"rtx\s*20\s*80\s*super", "rtx2080super"), (r"rtx\s*20\s*80", "rtx2080"),
    (r"rtx\s*20\s*70", "rtx2070"),
    (r"rtx\s*40\s*50", "rtx4050"), (r"rtx\s*50\s*50", "rtx5050"),
    (r"gtx\s*16\s*60\s*ti", "gtx1660ti"), (r"gtx\s*16\s*50\s*ti", "gtx1650ti"),
    (r"gtx\s*16\s*50", "gtx1650"), (r"gtx\s*10\s*80", "gtx1080"), (r"gtx\s*10\s*70", "gtx1070"),
    (r"gtx\s*10\s*60", "gtx1060"), (r"gtx\s*10\s*50\s*ti", "gtx1050ti"),
    (r"gtx\s*10\s*50", "gtx1050"),
    (r"(?:radeon\s*)?rx\s*67\s*00\s*m", "rx6700m"), (r"(?:radeon\s*)?rx\s*55\s*00\s*m", "rx5500m"),
    (r"rtx\s*20\s*70\s*super", "rtx2070super"), (r"rtx\s*20\s*60", "rtx2060"),
    (r"rtx\s*20\s*50", "rtx2050"),
    (r"(?:radeon\s*)?rx\s*77\s*00\s*s", "rx7700s"), (r"(?:radeon\s*)?rx\s*76\s*00\s*xt", "rx7600mxt"),
    (r"(?:radeon\s*)?rx\s*76\s*00\s*s", "rx7600s"), (r"(?:radeon\s*)?rx\s*76\s*00\s*m", "rx7600m"),
    (r"(?:radeon\s*)?rx\s*68\s*00\s*s", "rx6800s"), (r"(?:radeon\s*)?rx\s*66\s*00\s*m", "rx6600m"),
    (r"(?:radeon\s*)?rx\s*66\s*00\s*s", "rx6600s"), (r"(?:radeon\s*)?rx\s*65\s*00\s*m", "rx6500m"),
    (r"(?:radeon\s*)?rx\s*56\s*00\s*m", "rx5600m"), (r"(?:radeon\s*)?rx\s*55\s*00\s*m", "rx5500m"),
    (r"radeon\s*pro\s*56\s*00", "pro5600m"), (r"radeon\s*pro\s*55\s*00", "pro5500m"),
    (r"rx\s*79\s*00\s*m", "rx7900m"), (r"rx\s*68\s*50\s*m", "rx6850mxt"),
    (r"rx\s*68\s*00\s*m", "rx6800m"), (r"rx\s*67\s*00\s*m", "rx6700m"),
    (r"rx\s*76\s*00\s*m", "rx7600mxt"),
    (r"arc\s*a\s*770\s*m", "arca770m"), (r"arc\s*a\s*730\s*m", "arca730m"),
    (r"arc\s*a\s*570\s*m", "arca570m"),
]
_GPU_COMPILED = [(re.compile(p), k) for p, k in _GPU_PATTERNS]

# ---------------------------------------------------------------- CPU table
CPUS = {
    "14900hx": 100, "13980hx": 98, "13950hx": 96, "13900hx": 94, "12900hx": 86,
    "14700hx": 88, "14650hx": 84, "13800hx": 82, "13700hx": 84, "13650hx": 78,
    "12800hx": 76, "12650hx": 70,
    "7945hx3d": 104, "7945hx": 100, "7940hx": 96, "8945hx": 98, "7845hx": 92,
    "8945hs": 76, "8845hs": 76, "7940hs": 74, "7840hs": 72, "7735hs": 62,
    "7640hs": 60, "6800h": 62, "5800h": 46,
    "285h": 82, "185h": 78, "255h": 76, "155h": 68, "125h": 60,
    "14900h": 88, "14700h": 84, "13900h": 82, "13700h": 78, "13620h": 70,
    "13500h": 62, "12700h": 66, "12500h": 54, "11800h": 48, "10750h": 38,
}
_CPU_RE = re.compile(r"(?:i[3579]|ryzen\s*[3579]|ultra\s*[579]|core\s*ultra)?[\s\-]*"
                     r"(1[0-4]\d{3}[a-z]{0,3}|[5-9]\d{3}[a-z]{0,3})", re.I)

LAPTOP_MARKERS = [
    "laptop", "notebook", "โน้ตบุ๊ค", "โน้ตบุค", "แล็ปท็อป", "แลปทอป",
    "rog", "zephyrus", "strix", "tuf", "legion", "loq", "ideapad", "thinkpad", "yoga",
    "predator", "nitro", "aspire", "swift", "katana", "raider", "vector", "stealth",
    "cyborg", "sword", "creator", "prestige", "modern", "blade", "razer", "omen",
    "victus", "pavilion", "envy", "spectre", "vivo", "zenbook", "vivobook", "expertbook",
    "macbook", "xps", "alienware", "aorus", "gigabyte", "framework", "thinkbook",
]
# words that only ever appear on a notebook listing
STRONG_LAPTOP_MARKERS = [
    "laptop", "notebook", "โน้ตบุ๊ค", "โน้ตบุค", "แล็ปท็อป", "แลปทอป",
    "macbook", "zephyrus", "legion", "ideapad", "thinkpad", "predator helios",
    "katana", "cyborg", "sword", "zenbook", "vivobook", "expertbook", "thinkbook",
]
GPU_CARD_MARKERS = ["การ์ดจอ", "การ์ด จอ", "graphics card", "vga card", "การ์ดแสดงผล",
                    "gpu card", "external gpu", "egpu box"]
# text that proves the thing is a desktop tower or a handheld, not a notebook
NOT_A_LAPTOP_MARKERS = ["mainboard", "คอมเทพ", "คอมประกอบ", "พีซีประกอบ", "desktop pc",
                        "desktop computer", "pc set", "จอ monitor", "จอคอม",
                        "onexplayer", "gaming tablet", "handheld", "steam deck",
                        "rog ally", " legion go"]
DESKTOP_CPU_RE = re.compile(r"\b(?:9800x3d|7800x3d|9950x|7950x|14900k|14700k|13700k|"
                            r"12600k|ryzen\s*[3579]\s*\d{4}x3d)\b", re.I)


def _norm(t):
    return re.sub(r"\s+", " ", (t or "").lower())


def find_gpu(text):
    """Return (key, name, vram, perf) for the strongest GPU mentioned, or None."""
    t = _norm(text)
    for rx, key in _GPU_COMPILED:
        if rx.search(t):
            name, vram, perf = GPUS[key]
            # RTX 3080 laptop exists in 8 GB and 16 GB trim — honour an explicit 8 GB
            if key in ("rtx3080", "rtx3080ti") and re.search(
                    r"(?:rtx\s*3080\s*(?:ti)?[^0-9]{0,20})?8\s*gb", t) and not re.search(r"16\s*gb", t):
                return (key + "8", name + " (8 GB)", 8, perf - 8)
            return (key, name, vram, perf)
    return None


def explicit_vram(text):
    m = re.search(r"(\d{1,2})\s*gb\s*(?:gddr\s*\d?|vram)", _norm(text))
    if m:
        return int(m.group(1))
    m = re.search(r"vram\s*[:\-]?\s*(\d{1,2})\s*gb", _norm(text))
    return int(m.group(1)) if m else None


# generation x tier fallback, so an unlisted SKU is estimated rather than flattened to 40
_INTEL_GEN = {10: {9: 44, 7: 38, 5: 32, 3: 24}, 11: {9: 50, 7: 48, 5: 42, 3: 28},
              12: {9: 86, 7: 66, 5: 54, 3: 40}, 13: {9: 94, 7: 80, 5: 62, 3: 46},
              14: {9: 100, 7: 86, 5: 70, 3: 50}}
_RYZEN_GEN = {5: {9: 46, 7: 46, 5: 40, 3: 30}, 6: {9: 62, 7: 58, 5: 52, 3: 38},
              7: {9: 100, 7: 72, 5: 60, 3: 44}, 8: {9: 104, 7: 76, 5: 62, 3: 46}}
_ULTRA_GEN = {1: {9: 76, 7: 68, 5: 58}, 2: {9: 84, 7: 78, 5: 66}, 3: {9: 92, 7: 84, 5: 72}}


def _estimate_cpu(family, num):
    """family: 'i9' | 'ryzen9' | 'ultra9'; num: the model digits."""
    try:
        if family.startswith("i"):
            gen = int(num[:2]) if len(num) >= 4 else 0
            return _INTEL_GEN.get(gen, {}).get(int(family[1]))
        if family.startswith("ryzen"):
            gen = int(num[0])
            return _RYZEN_GEN.get(gen, {}).get(int(family[5:]))
        if family.startswith("ultra"):
            gen = int(num[0])
            return _ULTRA_GEN.get(gen, {}).get(int(family[5:]))
    except (ValueError, IndexError, KeyError):
        return None
    return None


def find_cpu(text):
    """Best mobile CPU mentioned. Patterns are anchored on the family token so the leading
    'i9' / 'ryzen 9' digit is never mistaken for part of the model number."""
    t = _norm(text)
    cands = []
    for rx, fam in ((r"\bi([3579])[\s\-]?(\d{4,5})([a-z]{0,2})\b", "i{}"),
                    (r"\bryzen\s*([3579])\s*(\d{4})([a-z]{0,3})\b", "ryzen{}"),
                    (r"\b(?:core\s*)?ultra\s*([579])\s*(\d{3})([a-z]{0,2})\b", "ultra{}")):
        for m in re.finditer(rx, t):
            num = m.group(2) + (m.group(3) or "")
            cands.append((num, m.group(0), fam.format(m.group(1))))
    best, best_score = None, -1
    for key, raw, family in cands:
        score = CPUS.get(key)
        if score is None:
            for cand in (key[:6], key[:5], key[:4]):
                if cand in CPUS:
                    score = CPUS[cand]
                    break
        if score is None:
            score = _estimate_cpu(family, key)
        if score and score > best_score:
            best, best_score = raw.strip(), score
    return (best, best_score) if best else (None, 40)


def find_tgp(text):
    """Total graphics power in watts, when the listing bothers to say. Laptop GPUs of the
    same name differ hugely by TGP, so it belongs in the score."""
    t = _norm(text)
    for rx in (r"tgp\s*[:=]?\s*(\d{1,3})\s*w", r"(\d{1,3})\s*w\s*tgp",
               r"graphics\s*power\s*[:=]?\s*(\d{1,3})"):
        m = re.search(rx, t)
        if m:
            w = int(m.group(1))
            if 35 <= w <= 250:
                return w
    return None


def tgp_factor(tgp):
    """Scale a class index by the power the GPU is actually allowed to draw.
    TGP is not linear in performance, but the band 60 W -> 175 W is worth roughly
    0.88 -> 1.05 on the same silicon."""
    if not tgp:
        return 1.0
    f = 0.80 + 0.25 * min(max(tgp, 45), 175) / 175.0
    return round(min(max(f, 0.80), 1.05), 3)


def find_screen(text):
    t = _norm(text)
    for rx in (r'(\d{2}(?:\.\d)?)\s*(?:inch|นิ้ว|"|”|″|\'\')',
               r'จอ\s*(\d{2}(?:\.\d)?)',
               r'(\d{2}(?:\.\d)?)\s*(?:hz)?\s*(?:inches|in\.)',
               r'\b(1[3-8])\s*(?:"|”)'):
        for m in re.finditer(rx, t):
            v = float(m.group(1))
            if 10 <= v <= 20:
                return v
    return None


def has_oled(text):
    t = _norm(text)
    return bool(re.search(r"\boled\b|amoled", t))


def find_ram(text):
    t = _norm(text)
    cands = [int(m.group(1)) for m in re.finditer(r"(?:rams?|memory|แรม)\s*[:\-]?\s*(\d{1,3})\s*gb", t)]
    cands += [int(m.group(1)) for m in re.finditer(r"(\d{1,3})\s*gb\s*(?:ddr\d|ram)", t)]
    cands += [int(m.group(1)) for m in re.finditer(r"(?:ddr\d)\s*(\d{1,3})\s*gb", t)]
    cands += [int(m.group(1)) for m in re.finditer(r"(\d{1,3})/(?:[0-9]{3,4})\s*ddr", t)]
    cands += [int(m.group(1)) for m in re.finditer(r"(\d{1,3})\s*gb\s*\(\s*\d{1,3}\s*gb\s*x\s*2", t)]
    valid = [c for c in cands if 4 <= c <= 256]
    return max(valid) if valid else None


def find_storage(text):
    t = _norm(text)
    nums = [int(m.group(1)) for m in re.finditer(
        r"(?:ssd|nvme|storage|hdd|ไดรฟ์)\s*[:\-]?\s*(\d{3,4})\s*(?:gb|tb)", t)]
    nums += [int(m.group(1)) * 1024 for m in re.finditer(
        r"(?:ssd|nvme|storage|hdd)\s*[:\-]?\s*(\d)\s*tb", t)]
    nums += [int(m.group(1)) * 1024 for m in re.finditer(r"\b(\d)\s*tb\b", t)]
    return max(nums) if nums else None


def find_price(text):
    t = text or ""
    m = re.search(r"฿\s*([\d,]{3,})", t)
    if not m:
        m = re.search(r"([\d,]{4,})\s*(?:บาท|thb|baht)", t, re.I)
    if not m:
        return None
    try:
        v = int(m.group(1).replace(",", ""))
    except ValueError:
        return None
    return v if 1000 <= v <= 500000 else None


def flags(text):
    t = _norm(text)
    out = []
    if re.search(r"จอแตก|จอเสีย|หน้าจอแตก|screen crack|broken screen", t): out.append("SCREEN-DMG")
    if re.search(r"ซ่อม|ซ่อมแล้ว|repair|repaired", t):                  out.append("REPAIRED")
    if re.search(r"อะไหล่|for parts|as[- ]is|ชำรุด|เปิดไม่ติด|จอไม่ติด|ไม่บูต|boot ไม่|"
                 r"no power|ไม่ติดเครื่อง|ซ่อมไม่ได้|เสียเครื่อง|อาการเสีย|dead laptop|"
                 r"gpu\s*chip|mainboard|motherboard|ชิ้นส่วน|cpu only|chip only|"
                 # desktop towers arrive wearing an OLED monitor and a huge GPU
                 r"good\s*pc|\bคอมเทพ|\b7950x\b|\b7800x3d\b|\b9800x3d\b|\b14900k\b|"
                 r"\b13700k\b|\b12900k\b|พีซีประกอบ|desktop\s*(?:pc|set)", t):
        out.append("PARTS")
    elif re.search(r"มีอาการ|แจ้งซ่อม|ต้องซ่อม|needs repair|faulty", t):
        out.append("FAULTY")
    if re.search(r"ไม่มีประกัน|no warranty|หมดประกัน", t):               out.append("NO-WARRANTY")
    if re.search(r"ประกัน(?:ศูนย์|เหลือ|ถึง)|warranty", t):              out.append("WARRANTY")
    if re.search(r"ไม่มีอะแดปเตอร์|ไม่มีcharger|no charger|ไม่มีสายชาร์จ", t): out.append("NO-CHARGER")
    if re.search(r"แบต(?:เสื่อม|บวม)|battery (?:swollen|degraded)", t):  out.append("BATTERY")
    if re.search(r"จอ\s*(?:\d{2})?\s*(?:ips|oled|amoled)", t):           pass
    if re.search(r"มือสอง|used|second", t):                              out.append("USED")
    if re.search(r"ใหม่|brand new|sealed", t):                           out.append("NEW")
    return out


def is_laptop(text):
    """True when the text describes a notebook, not a bare graphics card.

    Brand words alone are not enough (an 'RTX2080 ROG' card is not a laptop), so a brand
    must be accompanied by a notebook-class CPU or a screen size.
    """
    t = _norm(text)
    if any(m in t for m in GPU_CARD_MARKERS):
        return False
    if any(m in t for m in NOT_A_LAPTOP_MARKERS):
        return False
    if DESKTOP_CPU_RE.search(t) and not re.search(r"hx\b|h\b", t):
        return False
    if find_screen(t) is not None:
        return True
    if any(m in t for m in STRONG_LAPTOP_MARKERS):
        return True
    has_brand = any(m in t for m in LAPTOP_MARKERS)
    has_mobile_cpu = bool(re.search(r"i[3579][\s\-]?\d{4,5}|ryzen\s*[3579]|ultra\s*[579]", t))
    return has_brand and has_mobile_cpu


def parse(text):
    """Turn free listing text into a spec record."""
    gpu = find_gpu(text)
    cpu_name, cpu_perf = find_cpu(text)
    tgp = find_tgp(text)
    rec = {
        "gpu_key": gpu[0] if gpu else None,
        "gpu": gpu[1] if gpu else None,
        "vram": gpu[2] if gpu else explicit_vram(text),
        "gpu_perf": round(gpu[3] * tgp_factor(tgp), 1) if gpu else None,
        "tgp": tgp,
        "cpu": cpu_name,
        "cpu_perf": cpu_perf,
        "screen": find_screen(text),
        "oled": has_oled(text),
        "ram": find_ram(text),
        "storage": find_storage(text),
        "price": find_price(text),
        "flags": flags(text),
        "laptop": is_laptop(text),
    }
    return rec


def perf_score(gpu_perf, cpu_perf):
    """0-100 composite: GPU dominates for this use case."""
    if gpu_perf is None:
        return None
    cpu = cpu_perf if cpu_perf else 40
    return round(0.78 * min(gpu_perf, 105) + 0.22 * min(cpu, 105), 1)


def value_index(perf, price, rec):
    """Perf points per 10,000 baht, with modifiers. Higher is better."""
    if not perf or not price:
        return 0.0
    base = perf / (price / 10000.0)
    mult = 1.0
    if rec.get("oled"):
        mult *= 1.10
    scr = rec.get("screen")
    if scr:
        if 15.0 <= scr <= 16.5:
            mult *= 1.03
        elif scr >= 17.0:
            mult *= 0.97
        elif scr <= 14.5:
            mult *= 0.95
    ram = rec.get("ram")
    if ram:
        if ram >= 32:   mult *= 1.05
        elif ram >= 16: mult *= 1.0
        else:           mult *= 0.90
    f = set(rec.get("flags") or [])
    if "WARRANTY" in f:   mult *= 1.05
    if "PARTS" in f:      mult *= 0.30
    if "SCREEN-DMG" in f: mult *= 0.45
    if "REPAIRED" in f:   mult *= 0.85
    if "NO-CHARGER" in f: mult *= 0.93
    if "BATTERY" in f:    mult *= 0.90
    if not rec.get("vram"):
        mult *= 0.6
    return round(base * mult, 2)
