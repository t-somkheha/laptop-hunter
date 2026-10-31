#!/usr/bin/env python3
"""detailspec.py — pull every specification a listing text will give up, as a labelled template.

Pure text work, no network. Anything this cannot find stays None so a later catalogue lookup can
fill it, and the page can show "not stated" rather than inventing a number.

    from detailspec import extract
    extract(title, desc, raw_body) -> dict
"""
import re

RES_MAP = [
    (r"\b3840\s*[x×]\s*2160\b|\b4k\b|uhd", "3840 × 2160 (4K UHD)"),
    (r"\b3456\s*[x×]\s*2160\b", "3456 × 2160 (3.5K)"),
    (r"\b3200\s*[x×]\s*2000\b|\b3\.2k\b", "3200 × 2000 (3.2K)"),
    (r"\b3200\s*[x×]\s*1800\b", "3200 × 1800"),
    (r"\b2880\s*[x×]\s*(?:1800|1620)\b|\b2\.8k\b|\b3k\b", "2880 × 1800 (2.8K / 3K)"),
    (r"\b2560\s*[x×]\s*1600\b|\bwqxga\b|\b2\.5k\b", "2560 × 1600 (WQXGA / 2.5K)"),
    (r"\b2560\s*[x×]\s*1440\b|\bqhd\b|\bwqhd\b", "2560 × 1440 (QHD)"),
    (r"\b1920\s*[x×]\s*1200\b|\bwuxga\b", "1920 × 1200 (WUXGA)"),
    (r"\b1920\s*[x×]\s*1080\b|\bfhd\b|full hd", "1920 × 1080 (FHD)"),
]

PANEL_MAP = [
    (r"mini[\s-]?led", "Mini-LED"), (r"\boled\b", "OLED"), (r"\bips\b", "IPS"),
    (r"\bva\b", "VA"), (r"\btn\b", "TN"), (r"\blcd\b", "LCD"),
]

STORE_MAP = [
    (r"\b(?:ssd|nvme|m\.2|storage|ความจุ|ไดรฟ์)\D{0,12}(\d+(?:\.\d+)?)\s*(tb|gb)\b", "any"),
]

PORTS = [
    ("Thunderbolt 4", r"thunderbolt\s*4|tb4"), ("Thunderbolt 3", r"thunderbolt\s*3|tb3"),
    ("USB-C", r"usb[\s-]?c|type[\s-]?c"), ("USB-A", r"usb[\s-]?[23]|usb[\s-]?a"),
    ("HDMI 2.1", r"hdmi\s*2\.1"), ("HDMI", r"\bhdmi\b"), ("RJ-45 Ethernet", r"rj[\s-]?45|lan port|ethernet"),
    ("SD card reader", r"sd card|card reader"), ("DisplayPort", r"displayport|\bmini[\s-]?dp\b"),
    ("3.5 mm audio", r"headphone|audio jack|3\.5\s*mm"),
]


def _first(patterns, text):
    for pat, label in patterns:
        if re.search(pat, text, re.I):
            return label
    return None


def _number(pat, text):
    m = re.search(pat, text, re.I)
    if not m:
        return None
    try:
        return float(m.group(1))
    except (TypeError, ValueError):
        return None


def cpu(text):
    m = re.search(r"\b(?:intel\s+)?core\s*(?:ultra)?\s*([3579])\s*-?\s*(\d{3,5}[a-z]{0,3})", text, re.I)
    if m:
        fam = re.search(r"ultra", text, re.I)
        return f"Core {('Ultra ' if fam else '')}{m.group(1)} {m.group(2).upper()}"
    m = re.search(r"\bi[3579]\s*-?\s*(\d{4,5}[a-z]{0,3})\b", text, re.I)
    if m:
        return "i" + text[m.start():m.end()].strip()[1:].replace(" ", "").upper()
    m = re.search(r"\bryzen\s*(ai\s*)?([3579])\s+(\d{3,4}[a-z]{0,3})", text, re.I)
    if m:
        return f"Ryzen {m.group(2)} {m.group(3).upper()}" + (" (AI)" if m.group(1) else "")
    m = re.search(r"\b(ultra)\s*([3579])\s+(\d{3}[a-z]{0,2})", text, re.I)
    if m:
        return f"Core Ultra {m.group(2)} {m.group(3).upper()}"
    return None


def storage(text):
    """Capacities only count when an SSD word sits next to them — "16 GB" alone is usually RAM."""
    pats = (r"(\d+(?:\.\d+)?)\s*(tb|gb)\b[^.\n]{0,14}(?:ssd|nvme|m\.2)",
            r"(?:ssd|nvme|m\.2)[^.\n]{0,14}(\d+(?:\.\d+)?)\s*(tb|gb)\b",
            r"(?:storage|ความจุ)[^.\n]{0,14}(\d+(?:\.\d+)?)\s*(tb|gb)\b")
    for pat in pats:
        m = re.search(pat, text, re.I)
        if not m:
            continue
        v, unit = float(m.group(1)), m.group(2).lower()
        gb = int(v * 1024) if unit == "tb" else int(v)
        if gb >= 120:
            return gb
    return None


RAM_OK = {4, 8, 12, 16, 24, 32, 48, 64, 96, 128}


def ram(text):
    for pat in (r"(?:ram|memory|แรม)[^\n]{0,14}?(\d{1,3})\s*gb",
                r"(\d{1,3})\s*gb\s*(?:ddr\d|ram)"):
        m = re.search(pat, text, re.I)
        if m and int(m.group(1)) in RAM_OK:
            return int(m.group(1))
    return None


def weight(text):
    for m in re.finditer(r"(\d(?:\.\d{1,2})?)\s*(?:kg|กก\.?|กิโลกรัม)", text, re.I):
        v = float(m.group(1))
        if 0.9 <= v <= 4.5:          # no laptop weighs six kilograms
            return v
    return None


def warranty(text):
    m = re.search(r"(?:ประกัน|warranty)[^\n]{0,40}?(\d{1,2})\s*(?:ปี|year|yr)", text, re.I)
    if m:
        return f"{m.group(1)} year(s)"
    m = re.search(r"(?:ประกัน|warranty)[^\n]{0,40}?(\d{1,2})\s*(?:เดือน|month)", text, re.I)
    if m:
        return f"{m.group(1)} month(s)"
    m = re.search(r"(?:ประกัน|warranty)[^\n]{0,30}?(\d{2})/(\d{4})", text, re.I)
    if m:
        return f"until {m.group(1)}/{m.group(2)}"
    if re.search(r"ประกัน(?:ศูนย์)?(?:ไทย)?|warranty", text, re.I):
        return "stated (period unclear)"
    return None


def battery(text):
    m = re.search(r"(\d{2,3})\s*wh", text, re.I)
    return int(m.group(1)) if m else None


def refresh(text):
    m = re.search(r"(\d{2,3})\s*hz", text, re.I)
    if not m:
        return None
    v = int(m.group(1))
    return v if 40 <= v <= 540 else None


def touch(text):
    if re.search(r"touchscreen|touch screen|จอ\s*ทัช|ทัชสกรีน", text, re.I):
        return "yes"
    return None


def os_name(text):
    if re.search(r"windows\s*11|win\s*11", text, re.I):
        return "Windows 11"
    if re.search(r"windows\s*10|win\s*10", text, re.I):
        return "Windows 10"
    if re.search(r"\bmacos\b|\bmac os\b", text, re.I):
        return "macOS"
    if re.search(r"dos\b|ฟรี dos|no os", text, re.I):
        return "FreeDOS / no OS"
    return None


def colour(text):
    m = re.search(r"(abyssal black|eclipse gray|glacier white|platinum white|storm grey|"
                  r"off[- ]?black|midnight black|moonlight white|obsidian|gunmetal)", text, re.I)
    if m:
        return m.group(1).title()
    for th, en in [("ดำ", "Black"), ("ขาว", "White"), ("เทา", "Grey"), ("เงิน", "Silver")]:
        if th in text:
            return en
    return None


def extract(title, desc, body=""):
    text = " \n ".join(x for x in (title, desc, body) if x)
    flat = re.sub(r"[ \t]+", " ", text)
    ports = [name for name, pat in PORTS if re.search(pat, flat, re.I)]
    return {
        "cpu_text": cpu(flat),
        "resolution": _first(RES_MAP, flat),
        "panel": _first(PANEL_MAP, flat),
        "refresh": refresh(flat),
        "touch": touch(flat),
        "ram_gb": ram(flat),
        "storage_gb": storage(flat),
        "weight_kg": weight(flat),
        "battery_wh": battery(flat),
        "os": os_name(flat),
        "colour": colour(flat),
        "warranty": warranty(flat),
        "ports": ports,
        "keyboard": ("RGB backlit" if re.search(r"rgb", flat, re.I)
                     else "backlit" if re.search(r"backlit|ไฟติด|เรืองแสง", flat, re.I) else None),
        "webcam": ("1080p" if re.search(r"1080p.{0,10}(?:webcam|camera)|fhd.{0,10}camera", flat, re.I)
                   else "yes" if re.search(r"webcam|กล้องหน้า", flat, re.I) else None),
        "audio": ("Hi-Res" if re.search(r"hi[\s-]?res", flat, re.I) else None),
        "fingerprint": ("yes" if re.search(r"fingerprint|สแกนนิ้ว", flat, re.I) else None),
        "included": ("charger" if re.search(r"charger|อะแดปเตอร์|ที่ชาร์จ", flat, re.I) else None),
    }
