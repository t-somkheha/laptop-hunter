#!/usr/bin/env python3
"""specsheet.py — one readable spec sheet per listing that has a discrete GPU.

    python3 specsheet.py            # build data/gpu.html + data/gpu.txt
    python3 specsheet.py --text     # terminal only

Every field is labelled and sourced: from the listing text (seller's own words), from the item
page, or from a model catalogue lookup when the seller said nothing. Nothing is guessed silently.
"""
import datetime, json, os, re, sys

import catalog, detailspec, harvest, report, specs

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_HTML = os.path.join(HERE, "data", "gpu.html")
OUT_TXT = os.path.join(HERE, "data", "gpu.txt")
IMG_DIR = os.path.join(HERE, "data", "img")

DISCRETE = ("rtx", "rx", "pro5", "arca", "quadro")


CHIP_WORDS = ("gpu chip", "การ์ดจอ", "mainboard", "motherboard", "ชิ้นส่วน",
              "เฉพาะ cpu", "เฉพาะการ์ดจอ", "chip only")


def is_discrete(rec):
    k = (rec.get("gpu_key") or "")
    if not k or not any(k.startswith(p) for p in DISCRETE):
        return False
    if k.startswith("rx") and rec.get("vram") is None:
        return False
    title = (rec.get("title") or "").lower()
    if any(w in title for w in CHIP_WORDS):        # a loose chip or card is not a notebook
        return False
    return True


def image_paths(iid, rec):
    """Local files first (offline-friendly), else the remote URLs."""
    out = []
    if os.path.isdir(IMG_DIR):
        for n in range(10):
            p = os.path.join(IMG_DIR, f"{iid}_{n}.jpg")
            if os.path.exists(p):
                out.append(f"img/{iid}_{n}.jpg")
                if len(out) == 2:      # the carousel repeats itself past this
                    break
    if out:
        return out, True
    urls = []
    if rec.get("og_image"):
        urls.append(rec["og_image"])
    urls += [u for u in (rec.get("images") or []) if u not in urls]
    return urls[:4], False


def build_rows():
    rows, _ = report.build()
    details = {d["id"]: d for d in harvest.load_jsonl(harvest.DETAILS)}
    out = []
    for r in rows:
        if not r.get("price") or not r.get("laptop", True):
            continue
        if not is_discrete(r):
            continue
        d = details.get(r["id"], {})
        # Facebook item pages carry recommendations for other listings, so the raw body is
        # contaminated. Parse the title first, then the listing's own description, never the body.
        head = detailspec.extract(r.get("title", ""), "", "")
        body_ = detailspec.extract(r.get("title", ""), r.get("desc", ""), "")
        extra = {k: (head.get(k) or body_.get(k)) for k in head}
        own_text = ((r.get("title") or "") + " " + (r.get("desc") or "")).lower()
        key = catalog.key_of(r.get("title", ""))
        cat = catalog.lookup(key)
        out.append({
            "id": r["id"], "title": r.get("title"), "price": r.get("price"),
            "gpu": r.get("gpu"), "vram": r.get("vram"), "tgp": r.get("tgp"),
            "cpu": extra.get("cpu_text") or r.get("cpu"),
            "ram": extra.get("ram_gb") or r.get("ram"),
            "storage": extra.get("storage_gb") or r.get("storage"),
            "screen": r.get("screen") or cat.get("screen"),
            "resolution": extra.get("resolution") or cat.get("resolution"),
            "panel": ("OLED" if "oled" in own_text else (extra.get("panel") or cat.get("panel"))),
            "refresh": extra.get("refresh") or cat.get("refresh"),
            "touch": extra.get("touch"),
            "battery": extra.get("battery_wh") or cat.get("battery"),
            "weight": cat.get("weight") or extra.get("weight_kg"),
            "os": extra.get("os"),
            "ports": extra.get("ports") or [],
            "keyboard": extra.get("keyboard"), "webcam": extra.get("webcam"),
            "warranty": extra.get("warranty"), "colour": extra.get("colour"),
            "condition": r.get("condition"), "location": r.get("location"),
            "flags": [f for f in (r.get("flags") or [])
                      if not (f == "USED" and "NEW" in (r.get("flags") or []))],
            "desc": (r.get("desc") or ""),
            "url": r.get("url"), "model_key": key, "catalog_source": cat.get("source"),
            "images": None,
        })
    # one sheet per machine: same title, same price, same province = the same listing reposted
    seen, unique = set(), []
    for row in out:
        fp = (re.sub(r"[^a-z0-9]", "", (row["title"] or "").lower())[:60],
              row["price"], (row["location"] or "")[:18])
        if fp in seen:
            continue
        seen.add(fp)
        unique.append(row)
    out = unique
    for row in out:
        d = details.get(row["id"], {})
        row["images"], row["images_local"] = image_paths(row["id"], d)
    out.sort(key=lambda r: r["price"] or 0)
    return out


def template_lines(r):
    """The readable template, in the order a person would ask the questions."""
    def g(v, unit="", fallback="not stated"):
        if v in (None, "", []):
            return fallback
        return f"{v}{unit}"

    disp = []
    if r["screen"]:
        disp.append(f'{r["screen"]}"')
    if r["resolution"]:
        disp.append(r["resolution"])
    if r["panel"]:
        disp.append(r["panel"])
    if r["refresh"]:
        disp.append(f'{r["refresh"]} Hz')
    if r["touch"]:
        disp.append("touch")
    stor = f'{r["storage"] / 1024:g} TB' if r["storage"] and r["storage"] >= 1024 else (
        f'{r["storage"]} GB' if r["storage"] else "")

    return [
        ("CPU", g(r["cpu"])),
        ("GPU", f'{g(r["gpu"])} — {g(r["vram"], " GB VRAM")}'
                + (f', {r["tgp"]} W' if r["tgp"] else "")),
        ("RAM", g(r["ram"], " GB")),
        ("Storage", g(stor)),
        ("Display", " · ".join(disp) if disp else "not stated"),
        ("Battery", g(r["battery"], " Wh")),
        ("Weight", g(r["weight"], " kg")),
        ("OS", g(r["os"])),
        ("Ports", ", ".join(r["ports"]) if r["ports"] else "not stated"),
        ("Keyboard", g(r["keyboard"])),
        ("Webcam", g(r["webcam"])),
        ("Warranty", g(r["warranty"])),
        ("Colour", g(r["colour"])),
        ("Condition", g(r["condition"])),
        ("Location", g(r["location"])),
        ("Price", f'฿{r["price"]:,}' if r["price"] else "not stated"),
        ("Flags", ", ".join(r["flags"]) if r["flags"] else "none noted"),
    ]


HTML = r"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Discrete-GPU laptops — Thailand</title>
<style>
 :root{--bg:#0f0e13;--panel:#17161e;--panel2:#1f1e28;--line:#2e2b3a;--ink:#eee9f5;--dim:#9691a8;
       --amber:#d9b26c;--violet:#9d8cff;--green:#7fb069;--red:#d1685f}
 *{box-sizing:border-box}
 body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
 header{padding:24px 28px 14px;border-bottom:1px solid var(--line)}
 h1{margin:0 0 4px;font-size:20px;font-weight:650}
 .sub{color:var(--dim);font-size:12.5px}
 .bar{position:sticky;top:0;z-index:20;display:flex;gap:9px;flex-wrap:wrap;align-items:center;
      padding:11px 28px;background:rgba(15,14,19,.97);border-bottom:1px solid var(--line)}
 input[type=search],select{background:var(--panel2);color:var(--ink);border:1px solid var(--line);
      border-radius:8px;padding:8px 10px;font:inherit;font-size:13px}
 input[type=search]{flex:1 1 230px;min-width:200px}
 main{padding:18px 28px 80px}
 .count{color:var(--dim);font-size:12.5px;margin-bottom:12px}
 .sheet{background:var(--panel);border:1px solid var(--line);border-radius:12px;margin-bottom:14px;
        display:grid;grid-template-columns:230px minmax(0,1fr);gap:0;overflow:hidden}
 @media(max-width:820px){.sheet{grid-template-columns:1fr}}
 .shots{background:#0c0b10;display:grid;gap:2px;align-content:start}
 .shots img{width:100%;height:auto;display:block;object-fit:cover}
 .shots .none{color:#5d5870;font-size:11px;padding:18px 12px;text-align:center}
 .body{padding:14px 17px}
 .hdr{display:flex;justify-content:space-between;gap:12px;align-items:baseline;flex-wrap:wrap}
 .price{font-size:19px;font-weight:650;color:var(--amber);font-variant-numeric:tabular-nums}
 .name{font-weight:600;margin:3px 0 2px}
 .tag{font-family:ui-monospace,monospace;font-size:10.5px;color:var(--dim)}
 table{width:100%;border-collapse:collapse;margin-top:11px;font-size:13px}
 th{text-align:left;color:var(--dim);font-weight:500;width:106px;padding:4px 10px 4px 0;
    vertical-align:top;white-space:nowrap;font-size:12px;text-transform:uppercase;letter-spacing:.05em}
 td{padding:4px 0;border-bottom:1px solid #201e29;color:#ded9ea}
 tr:last-child td,tr:last-child th{border-bottom:none}
 .src{color:#6f6a83;font-size:10.5px;margin-left:6px}
 .desc{margin-top:10px;font-size:12.5px;color:#c9c3d8;white-space:pre-wrap;max-height:110px;overflow:auto;
       border-left:2px solid #2a2735;padding-left:10px}
 .btnrow{margin-top:10px;display:flex;gap:8px;flex-wrap:wrap}
 .btn{border:1px solid var(--line);background:var(--panel2);border-radius:7px;padding:6px 10px;
      font:inherit;font-size:12px;color:var(--ink);text-decoration:none;cursor:pointer}
 .btn:hover{border-color:var(--violet)}
 .flag{color:var(--red)}
 footer{color:var(--dim);font-size:11.5px;padding:0 28px 30px}
</style></head><body>
<header><h1>Laptops with a discrete GPU — Thailand</h1>
 <div class="sub" id="sub"></div></header>
<div class="bar">
 <input type="search" id="q" placeholder="model, CPU, GPU, province…">
 <select id="sort"><option value="price-asc">cheapest</option><option value="price-desc">dearest</option>
  <option value="vram">most VRAM</option><option value="gpu">strongest GPU</option></select>
 <select id="gpu"><option value="">all GPUs</option></select>
 <select id="vendor"><option value="">all vendors</option><option value="nvidia">NVIDIA RTX</option>
  <option value="amd">AMD Radeon</option></select>
 <select id="cond"><option value="ok">working machines only</option>
  <option value="">include faulty / parts</option></select>
</div>
<main><div class="count" id="count"></div><div id="sheets"></div></main>
<footer id="foot"></footer>
<script type="application/json" id="payload">__DATA__</script>
<script>
const D=JSON.parse(document.getElementById('payload').textContent);
const R=D.rows, el=id=>document.getElementById(id), baht=n=>'฿'+(n||0).toLocaleString('en-US');
const gv=(v,u='')=> (v===null||v===undefined||v==='')?'not stated':(Array.isArray(v)?(v.length?v.join(', '):'not stated'):v+u);
el('sub').textContent=`${R.length} listings with a discrete NVIDIA RTX or AMD Radeon GPU · ${D.regions.join(', ')} · ${D.scanned} cards swept · built ${D.generated}`;
el('foot').textContent='Every field is labelled. Fields marked "model spec" came from a catalogue lookup of '+
 'that model when the seller stated nothing; they describe the model, not necessarily this exact unit. '+
 'Verify RAM, storage and panel in person.';
const chips=[...new Set(R.map(r=>r.gpu))].sort();
el('gpu').innerHTML+=chips.map(g=>`<option>${g}</option>`).join('');
['q','sort','gpu','vendor','cond'].forEach(id=>el(id).addEventListener(id==='q'?'input':'change',render));
function faulty(r){return (r.flags||[]).some(f=>['PARTS','FAULTY','SCREEN-DMG'].includes(f));}
function vendor(r){ return (r.gpu||'').toLowerCase().includes('radeon')?'amd':'nvidia'; }
function pass(r){const t=el('q').value.trim().toLowerCase();
 if(t&&![r.title,r.desc,r.location,r.gpu,r.cpu,r.model_key].join(' ').toLowerCase().includes(t))return false;
 if(el('gpu').value&&r.gpu!==el('gpu').value)return false;
 if(el('vendor').value&&vendor(r)!==el('vendor').value)return false;
 if(el('cond').value==='ok'&&faulty(r))return false;return true;}
function row(k,v,src){return `<tr><th>${k}</th><td>${v}${src?`<span class="src">${src}</span>`:''}</td></tr>`;}
function sheet(r){
 const imgs=(r.images||[]).slice(0,3);
 const shots=imgs.length?imgs.map(u=>`<img loading="lazy" src="${u}" alt="">`).join('')
                          :'<div class="none">no photograph captured</div>';
 const catSrc=r.catalog_source?'<span class="src">model spec</span>':'';
 return `<div class="sheet"><div class="shots">${shots}</div><div class="body">
  <div class="hdr"><div class="name">${r.title}</div><div class="price">${baht(r.price)}</div></div>
  <div class="tag">${r.model_key||'model unidentified'} · ${r.condition||'condition ?'} · ${r.location||''}</div>
  <table>
   ${row('CPU',gv(r.cpu))}
   ${row('GPU',`${gv(r.gpu)} — ${gv(r.vram,' GB')} VRAM${r.tgp?`, ${r.tgp} W`:''}`)}
   ${row('RAM',gv(r.ram,' GB'))}
   ${row('Storage',r.storage?(r.storage>=1024?`${r.storage/1024} TB`:`${r.storage} GB`):'not stated')}
   ${row('Display',[r.screen?r.screen+'"':'',r.resolution||'',r.panel||'',r.refresh?r.refresh+' Hz':'',r.touch?'touch':''].filter(Boolean).join(' · ')||'not stated',catSrc)}
   ${row('Battery',gv(r.battery,' Wh'),catSrc)}
   ${row('Weight',gv(r.weight,' kg'),catSrc)}
   ${row('OS',gv(r.os))}
   ${row('Ports',gv(r.ports))}
   ${row('Keyboard',gv(r.keyboard))}
   ${row('Warranty',gv(r.warranty))}
   ${row('Flags',r.flags.length?`<span class="flag">${r.flags.join(', ')}</span>`:'none noted')}
  </table>
  <div class="desc">${(r.desc||'no description captured').replace(/</g,'&lt;')}</div>
  <div class="btnrow"><a class="btn" target="_blank" rel="noopener" href="${r.url}">open on facebook</a>
   <button class="btn" onclick="navigator.clipboard.writeText('${r.url}')">copy link</button></div>
 </div></div>`;
}
function render(){
 const list=R.filter(pass);
 const s=el('sort').value, by={'price-asc':(a,b)=>a.price-b.price,'price-desc':(a,b)=>b.price-a.price,
   vram:(a,b)=>(b.vram||0)-(a.vram||0),gpu:(a,b)=>(b.vram||0)-(a.vram||0)||(b.price||0)-(a.price||0)}[s];
 list.sort(by);
 el('count').textContent=`${list.length} listing${list.length===1?'':'s'}`;
 el('sheets').innerHTML=list.map(sheet).join('')||'<div class="count">nothing matches</div>';
}
render();
</script></body></html>
"""


def main(argv):
    rows = build_rows()
    cards = harvest.load_jsonl(harvest.CARDS)
    regions = sorted({c.get("region") for c in cards if c.get("region")} - {"watchlist"})
    payload = {"rows": rows, "scanned": len(cards), "regions": regions or ["bangkok"],
               "generated": datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")}
    os.makedirs(os.path.dirname(OUT_HTML), exist_ok=True)
    with open(OUT_HTML, "w") as f:
        f.write(HTML.replace("__DATA__", json.dumps(payload, ensure_ascii=False)))
    with open(OUT_TXT, "w") as f:
        f.write(f"Laptops with a discrete GPU — Thailand — {len(rows)} listings\n\n")
        for r in rows:
            f.write(f"{'=' * 78}\n{r['title']}\n")
            for k, v in template_lines(r):
                f.write(f"  {k + ':':<11}{v}\n")
            f.write(f"  {'Link:':<11}{r['url']}\n")
    print(f"{len(rows)} GPU listings -> {OUT_HTML} and {OUT_TXT}")
    if "--text" in argv:
        for r in rows[:8]:
            print()
            for k, v in template_lines(r):
                print(f"  {k + ':':<11}{v}")


if __name__ == "__main__":
    main(sys.argv[1:])
