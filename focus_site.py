#!/usr/bin/env python3
"""focus_site.py — OLED + dedicated RTX above 8 GB VRAM, as spec sheets with photographs.

    python3 focus_site.py

Reads the same pool as specsheet.py and keeps only rows that satisfy all three conditions:
an OLED panel stated by the seller, an NVIDIA RTX or AMD Radeon discrete card, and more than
8 GB of VRAM (so 12, 16 or 24 — the 8 GB cards are the thing being excluded).
"""
import datetime, json, os, re

import harvest, specsheet

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_HTML = os.path.join(HERE, "data", "focus.html")
OUT_TXT = os.path.join(HERE, "data", "focus.txt")
MIN_VRAM = 8          # strictly greater than this


def keep(r):
    if not r.get("price") or not r.get("vram"):
        return False
    if "PARTS" in (r.get("flags") or []):      # a desktop tower or a dead machine is not a laptop
        return False
    if r["vram"] <= MIN_VRAM:
        return False
    gpu = (r.get("gpu") or "").lower()
    if "rtx" not in gpu and "radeon" not in gpu:
        return False
    return (r.get("panel") or "").upper() == "OLED"


HTML = r"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>OLED + RTX over 8 GB — Thailand</title>
<style>
 :root{--bg:#0d0c11;--panel:#16151d;--panel2:#1e1d27;--line:#2d2a39;--ink:#efeaF6;--dim:#948fa6;
       --amber:#dcb46b;--violet:#a08cff;--green:#7fb069;--red:#d1685f}
 *{box-sizing:border-box}
 body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
 header{padding:26px 28px 15px;border-bottom:1px solid var(--line)}
 h1{margin:0 0 5px;font-size:21px;font-weight:660;letter-spacing:.2px}
 h1 em{color:var(--violet);font-style:normal}
 .sub{color:var(--dim);font-size:12.5px}
 .stats{display:flex;gap:26px;flex-wrap:wrap;margin-top:15px}
 .stat b{display:block;font-size:18px;color:var(--amber);font-variant-numeric:tabular-nums}
 .stat span{font-size:10.5px;text-transform:uppercase;letter-spacing:.08em;color:var(--dim)}
 .bar{position:sticky;top:0;z-index:20;display:flex;gap:9px;flex-wrap:wrap;align-items:center;
      padding:11px 28px;background:rgba(13,12,17,.97);border-bottom:1px solid var(--line)}
 input[type=search],select{background:var(--panel2);color:var(--ink);border:1px solid var(--line);
      border-radius:8px;padding:8px 10px;font:inherit;font-size:13px}
 input[type=search]{flex:1 1 240px;min-width:200px}
 main{padding:18px 28px 80px}
 .count{color:var(--dim);font-size:12.5px;margin-bottom:12px}
 .sheet{background:var(--panel);border:1px solid var(--line);border-radius:12px;margin-bottom:14px;
        display:grid;grid-template-columns:250px minmax(0,1fr);overflow:hidden}
 @media(max-width:860px){.sheet{grid-template-columns:1fr}}
 .shots{background:#0a0910;display:grid;gap:2px;align-content:start}
 .shots img{width:100%;height:auto;display:block}
 .shots .none{color:#57526a;font-size:11px;padding:20px 12px;text-align:center}
 .body{padding:15px 18px}
 .hdr{display:flex;justify-content:space-between;gap:12px;align-items:baseline;flex-wrap:wrap}
 .price{font-size:19.5px;font-weight:660;color:var(--amber);font-variant-numeric:tabular-nums}
 .name{font-weight:600;margin:3px 0 2px;font-size:14.5px}
 .tag{font-family:ui-monospace,monospace;font-size:10.5px;color:var(--dim)}
 .badge{display:inline-block;font-size:10.5px;padding:2px 7px;border-radius:5px;margin-left:6px;
        background:#1d1830;border:1px solid #3d3566;color:#c3b6ff}
 table{width:100%;border-collapse:collapse;margin-top:11px;font-size:13px}
 th{text-align:left;color:var(--dim);font-weight:500;width:104px;padding:4px 10px 4px 0;
    vertical-align:top;white-space:nowrap;font-size:11.5px;text-transform:uppercase;letter-spacing:.05em}
 td{padding:4px 0;border-bottom:1px solid #1f1d26;color:#dfdae9}
 tr:last-child td,tr:last-child th{border-bottom:none}
 .src{color:#6b6680;font-size:10.5px;margin-left:6px}
 .desc{margin-top:10px;font-size:12.5px;color:#c8c2d6;white-space:pre-wrap;max-height:100px;
       overflow:auto;border-left:2px solid #282534;padding-left:10px}
 .btnrow{margin-top:10px;display:flex;gap:8px;flex-wrap:wrap}
 .btn{border:1px solid var(--line);background:var(--panel2);border-radius:7px;padding:6px 10px;
      font:inherit;font-size:12px;color:var(--ink);text-decoration:none;cursor:pointer}
 .btn:hover{border-color:var(--violet)}
 .flag{color:var(--red)}
 .empty{color:var(--dim);padding:30px 0}
 footer{color:var(--dim);font-size:11.5px;padding:0 28px 32px;max-width:900px}
</style></head><body>
<header><h1>OLED <em>+</em> RTX, more than 8 GB</h1>
 <div class="sub" id="sub"></div><div class="stats" id="stats"></div></header>
<div class="bar">
 <input type="search" id="q" placeholder="model, GPU, CPU, province…">
 <select id="sort"><option value="price-asc">cheapest</option><option value="price-desc">dearest</option>
  <option value="vram">most VRAM</option><option value="pricepergb">best baht per GB</option></select>
 <select id="gpu"><option value="">all GPUs</option></select>
 <select id="vramsel"><option value="">any VRAM</option><option value="12">12 GB and up</option>
  <option value="16">16 GB and up</option></select>
 <select id="cond"><option value="ok">working machines</option><option value="">include faulty</option></select>
</div>
<main><div class="count" id="count"></div><div id="sheets"></div></main>
<footer id="foot"></footer>
<script type="application/json" id="payload">__DATA__</script>
<script>
const D=JSON.parse(document.getElementById('payload').textContent), R=D.rows,
      el=id=>document.getElementById(id), baht=n=>'฿'+(n||0).toLocaleString('en-US');
const gv=(v,u='')=>(v===null||v===undefined||v==='')?'not stated':(Array.isArray(v)?(v.length?v.join(', '):'not stated'):v+u);
el('sub').textContent=`${R.length} listings · OLED panel · dedicated RTX/Radeon · more than 8 GB VRAM · `+
 `${D.regions.join(', ')} · ${D.scanned} cards swept · built ${D.generated}`;
const prices=R.map(r=>r.price).sort((a,b)=>a-b);
el('stats').innerHTML=[['listings',R.length],['cheapest',baht(prices[0]||0)],
 ['median',baht(prices[Math.floor(prices.length/2)]||0)],['cheapest 5070 Ti',baht(Math.min(...R.filter(r=>/5070 ti/i.test(r.gpu||'')).map(r=>r.price).concat([0]).filter(Boolean))||0)],
 ['16 GB or more',R.filter(r=>r.vram>=16).length],['under ฿70k',R.filter(r=>r.price<70000).length]]
 .map(([k,v])=>`<div class="stat"><b>${v}</b><span>${k}</span></div>`).join('');
el('foot').textContent='Every specification is labelled and sourced from the seller\'s own words '+
 'unless marked "model spec", which came from a catalogue lookup of that model code and describes '+
 'the model rather than this exact unit. Verify RAM, storage and the panel in person — an OLED '+
 'shows true black at an angle and no backlight bleed.';
const gpus=[...new Set(R.map(r=>r.gpu))].sort();
el('gpu').innerHTML+=gpus.map(g=>`<option>${g}</option>`).join('');
['q','sort','gpu','vramsel','cond'].forEach(id=>el(id).addEventListener(id==='q'?'input':'change',render));
const faulty=r=>(r.flags||[]).some(f=>['PARTS','FAULTY','SCREEN-DMG'].includes(f));
function pass(r){const t=el('q').value.trim().toLowerCase();
 if(t&&![r.title,r.desc,r.location,r.gpu,r.cpu,r.model_key].join(' ').toLowerCase().includes(t))return false;
 if(el('gpu').value&&r.gpu!==el('gpu').value)return false;
 if(el('vramsel').value&&r.vram<+el('vramsel').value)return false;
 if(el('cond').value==='ok'&&faulty(r))return false;return true;}
const row=(k,v,src)=>`<tr><th>${k}</th><td>${v}${src?`<span class="src">${src}</span>`:''}</td></tr>`;
function sheet(r){const imgs=(r.images||[]).slice(0,2),
 shots=imgs.length?imgs.map(u=>`<img loading="lazy" src="${u}" alt="">`).join(''):'<div class="none">no photograph</div>',
 catSrc=r.catalog_source?'<span class="src">model spec</span>':'';
 return `<div class="sheet"><div class="shots">${shots}</div><div class="body">
  <div class="hdr"><div class="name">${r.title}${r.vram>=16?'<span class="badge">16 GB or more</span>':''}</div>
   <div class="price">${baht(r.price)}</div></div>
  <div class="tag">${r.model_key||'model unidentified'} · ${r.condition||'condition ?'} · ${r.location||''}</div>
  <table>
   ${row('CPU',gv(r.cpu))}
   ${row('GPU',`${gv(r.gpu)} — ${r.vram} GB VRAM${r.tgp?`, ${r.tgp} W`:''}`)}
   ${row('RAM',gv(r.ram,' GB'))}
   ${row('Storage',r.storage?(r.storage>=1024?`${r.storage/1024} TB`:`${r.storage} GB`):'not stated')}
   ${row('Display',[r.screen?r.screen+'"':'',r.resolution||'','OLED',r.refresh?r.refresh+' Hz':''].filter(Boolean).join(' · '),catSrc)}
   ${row('Battery',gv(r.battery,' Wh'),catSrc)}
   ${row('Weight',gv(r.weight,' kg'),catSrc)}
   ${row('Warranty',gv(r.warranty))}
   ${row('Flags',r.flags.length?`<span class="flag">${r.flags.join(', ')}</span>`:'none noted')}
  </table>
  <div class="desc">${(r.desc||'no description captured').replace(/</g,'&lt;')}</div>
  <div class="btnrow"><a class="btn" target="_blank" rel="noopener" href="${r.url}">open on facebook</a>
   <button class="btn" onclick="navigator.clipboard.writeText('${r.url}')">copy link</button></div>
 </div></div>`;}
function render(){const list=R.filter(pass), s=el('sort').value;
 const by={'price-asc':(a,b)=>a.price-b.price,'price-desc':(a,b)=>b.price-a.price,
  vram:(a,b)=>b.vram-a.vram||a.price-b.price,
  pricepergb:(a,b)=>(a.price/a.vram)-(b.price/b.vram)}[s];
 list.sort(by);
 el('count').textContent=`${list.length} listing${list.length===1?'':'s'}`;
 el('sheets').innerHTML=list.map(sheet).join('')||'<div class="empty">nothing matches</div>';}
render();
</script></body></html>
"""


def main():
    rows = [r for r in specsheet.build_rows() if keep(r)]
    rows.sort(key=lambda r: r["price"])
    cards = harvest.load_jsonl(harvest.CARDS)
    regions = sorted({c.get("region") for c in cards if c.get("region")} - {"watchlist"})
    payload = {"rows": rows, "scanned": len(cards), "regions": regions or ["bangkok"],
               "generated": datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")}
    os.makedirs(os.path.dirname(OUT_HTML), exist_ok=True)
    if not rows:
        print("no listings yet — run a sweep first (see README: sweep_focus.py, then harvest.py)")
        return
    with open(OUT_HTML, "w") as f:
        f.write(HTML.replace("__DATA__", json.dumps(payload, ensure_ascii=False)))
    with open(OUT_TXT, "w") as f:
        f.write(f"OLED + dedicated RTX, more than 8 GB VRAM — Thailand — {len(rows)} listings\n\n")
        for i, r in enumerate(rows, 1):
            f.write(f"{i:>2}. ฿{r['price']:,}  {r['title'][:74]}\n")
            f.write(f"    GPU {r['gpu']} {r['vram']}GB | {r['cpu'] or 'CPU ?'} | RAM {r['ram'] or '?'} | "
                    f"{r['storage'] and (str(r['storage']//1024)+'TB' if r['storage']>=1024 else str(r['storage'])+'GB') or '?'} | "
                    f"{r['screen'] or '?'}\" {r['resolution'] or ''} OLED {r['refresh'] or ''}Hz | "
                    f"{r['condition'] or '?'} | {r['location'] or '?'}\n    {r['url']}\n")
    print(f"{len(rows)} OLED+RTX>8GB listings -> {OUT_HTML} and {OUT_TXT}")


if __name__ == "__main__":
    main()
