#!/usr/bin/env python3
"""oled_site.py — build a focused page containing ONLY OLED notebooks with a dedicated RTX card.

Writes data/oled.html plus data/oled_focus.txt. Same rules as build_site.py's data source, but
the panel requirement is the whole point, so each listing records whether "OLED" appears in the
seller's title (strong) or only in the description (weaker, sometimes a comparison).
"""
import datetime, json, os

import harvest, report, oled_report

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_HTML = os.path.join(HERE, "data", "oled.html")
OUT_TXT = os.path.join(HERE, "data", "oled_focus.txt")

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>OLED + RTX — Thailand</title>
<style>
  :root { --bg:#111014; --panel:#191820; --panel2:#20202a; --line:#322f3d; --ink:#eee9f5;
          --dim:#9a95ad; --amber:#d9b26c; --violet:#9d8cff; --green:#7fb069; --red:#d1685f; }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--ink);
         font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif; }
  header { padding:26px 30px 16px; border-bottom:1px solid var(--line); }
  h1 { margin:0 0 5px; font-size:21px; font-weight:650; letter-spacing:.2px; }
  h1 span { color:var(--violet); }
  .sub { color:var(--dim); font-size:12.5px; }
  .stats { display:flex; gap:24px; flex-wrap:wrap; margin-top:14px; }
  .stat b { display:block; font-size:18px; color:var(--amber); font-variant-numeric:tabular-nums; }
  .stat span { font-size:10.5px; text-transform:uppercase; letter-spacing:.08em; color:var(--dim); }
  .bar { position:sticky; top:0; z-index:20; display:flex; gap:10px; flex-wrap:wrap;
         align-items:center; padding:12px 30px; background:rgba(17,16,20,.96);
         border-bottom:1px solid var(--line); backdrop-filter:blur(6px); }
  input[type=search], select { background:var(--panel2); color:var(--ink); border:1px solid var(--line);
         border-radius:8px; padding:9px 11px; font:inherit; font-size:13.5px; }
  input[type=search] { min-width:240px; flex:1 1 240px; }
  input[type=search]:focus, select:focus { outline:1px solid var(--violet); }
  .toggle { display:flex; align-items:center; gap:6px; font-size:12.5px; color:var(--dim);
            background:var(--panel2); border:1px solid var(--line); border-radius:8px;
            padding:8px 10px; cursor:pointer; user-select:none; }
  .toggle input { accent-color:var(--violet); }
  .toggle.on { color:var(--ink); border-color:var(--violet); }
  main { padding:20px 30px 70px; }
  .layout { display:grid; grid-template-columns:minmax(0,1fr) 390px; gap:22px; align-items:start; }
  @media (max-width:1080px) { .layout { grid-template-columns:minmax(0,1fr); } }
  .count { color:var(--dim); font-size:12.5px; margin-bottom:10px; }
  .grid { display:grid; gap:12px; }
  .card { background:var(--panel); border:1px solid var(--line); border-radius:12px;
          padding:15px 17px; cursor:pointer; transition:border-color .12s; }
  .card:hover { border-color:#4a4460; }
  .card.sel { border-color:var(--violet); box-shadow:0 0 0 1px var(--violet) inset; }
  .row1 { display:flex; justify-content:space-between; gap:14px; align-items:baseline; }
  .price { font-size:18.5px; font-weight:650; font-variant-numeric:tabular-nums; }
  .best { font-size:10.5px; color:#0f0d14; background:var(--amber); padding:2px 7px;
          border-radius:5px; margin-left:7px; font-weight:700; }
  .title { font-weight:550; margin:4px 0 9px; overflow:hidden; display:-webkit-box;
           -webkit-line-clamp:2; -webkit-box-orient:vertical; }
  .chips { display:flex; flex-wrap:wrap; gap:5px; }
  .chip { font-size:11px; padding:3px 7px; border-radius:6px; background:var(--panel2);
          border:1px solid var(--line); color:var(--dim); white-space:nowrap; }
  .chip.gpu { color:var(--amber); border-color:#4a3d28; background:#241d13; }
  .chip.oled { color:#c3b6ff; border-color:#3d3566; background:#1d1830; }
  .chip.weak { color:#c9a26a; border-color:#4a3d28; }
  .chip.bad { color:var(--red); border-color:#55332f; }
  .meta { margin-top:9px; font-size:11.5px; color:var(--dim); display:flex; gap:13px; flex-wrap:wrap; }
  aside { position:sticky; top:66px; display:grid; gap:12px; }
  .box { background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:15px; }
  .box h3 { margin:0 0 9px; font-size:11.5px; text-transform:uppercase; letter-spacing:.09em;
            color:var(--dim); font-weight:600; }
  canvas { width:100%; height:240px; display:block; }
  .detail .dtitle { font-weight:600; margin-bottom:6px; font-size:14px; }
  .detail p { font-size:12.5px; color:#d6d0e4; white-space:pre-wrap; margin:8px 0;
              max-height:210px; overflow:auto; }
  .btnrow { display:flex; gap:9px; margin-top:9px; flex-wrap:wrap; }
  .linkbtn { border:1px solid var(--line); background:var(--panel2); border-radius:7px;
             padding:6px 10px; cursor:pointer; font:inherit; font-size:12px; color:var(--ink);
             text-decoration:none; }
  .linkbtn:hover { border-color:var(--violet); }
  .tag { font-family:ui-monospace,monospace; font-size:10.5px; color:var(--dim); }
  .empty { color:var(--dim); padding:26px 0; }
  footer { color:var(--dim); font-size:11.5px; padding:0 30px 34px; }
</style>
</head>
<body>
<header>
  <h1>OLED <span>+</span> dedicated RTX — Thailand</h1>
  <div class="sub" id="sub"></div>
  <div class="stats" id="stats"></div>
</header>

<div class="bar">
  <input type="search" id="q" placeholder="model, GPU, CPU, province, seller text…">
  <select id="sort">
    <option value="price-asc">cheapest first</option>
    <option value="price-desc">dearest first</option>
    <option value="gpu">strongest GPU</option>
    <option value="vram">most VRAM</option>
    <option value="screen">largest screen</option>
  </select>
  <select id="gpu"><option value="">all GPUs</option></select>
  <label class="toggle" id="strictWrap"><input type="checkbox" id="strict"> title-confirmed OLED</label>
  <label class="toggle"><input type="checkbox" id="clean"> hide damaged</label>
  <label class="toggle"><input type="checkbox" id="big"> 16"+ only</label>
</div>

<main>
  <div class="layout">
    <div>
      <div class="count" id="count"></div>
      <div class="grid" id="cards"></div>
    </div>
    <aside>
      <div class="box">
        <h3>price × GPU class</h3>
        <canvas id="chart"></canvas>
        <div class="tag">click a dot to select · violet = 12 GB or more</div>
      </div>
      <div class="box detail" id="detail"><h3>selected</h3><div class="tag">pick a listing</div></div>
    </aside>
  </div>
</main>
<footer id="foot"></footer>

<script type="application/json" id="payload">__DATA__</script>
<script>
const D = JSON.parse(document.getElementById('payload').textContent);
const rows = D.rows, gen = D.generated;
const baht = n => '฿' + (n || 0).toLocaleString('en-US');
const el = id => document.getElementById(id);
let selected = null;

const prices = rows.map(r => r.price).sort((a,b)=>a-b);
el('sub').textContent = `${rows.length} listings with an OLED panel and a dedicated RTX GPU · ` +
  `${D.regions.join(', ')} · swept ${D.scanned} marketplace cards · built ${gen}`;
el('stats').innerHTML = [
  ['listings', rows.length],
  ['cheapest', baht(prices[0]||0)],
  ['median', baht(prices.length ? prices[Math.floor(prices.length/2)] : 0)],
  ['12 GB or more', rows.filter(r=>r.vram>=12).length],
  ['title-confirmed OLED', rows.filter(r=>r.oled_title).length],
  ['under ฿50k', rows.filter(r=>r.price<50000).length],
].map(([k,v])=>`<div class="stat"><b>${v}</b><span>${k}</span></div>`).join('');
el('foot').textContent = 'OLED claims come from the seller\'s own text — "title-confirmed" means the ' +
  'word appears in the listing title. Verify the panel in person: true black at an angle, no ' +
  'backlight bleed. GPU class figures are relative estimates, not benchmarks.';

const gpus = [...new Set(rows.map(r=>r.gpu))].sort((a,b)=>
  (rows.find(x=>x.gpu===b)?.gpu_idx||0) - (rows.find(x=>x.gpu===a)?.gpu_idx||0) || a.localeCompare(b));
el('gpu').innerHTML += gpus.map(g=>`<option value="${g}">${g}</option>`).join('');

['q','sort','gpu','strict','clean','big'].forEach(id =>
  el(id).addEventListener(id==='q'?'input':'change', render));
['strict','clean','big'].forEach(id =>
  el(id).addEventListener('change', () => el(id).closest('.toggle').classList.toggle('on', el(id).checked)));

function passes(r) {
  const t = el('q').value.trim().toLowerCase();
  if (t) {
    const hay = [r.title, r.desc, r.location, r.gpu, r.cpu, r.gpu_full].join(' ').toLowerCase();
    if (!hay.includes(t)) return false;
  }
  if (el('gpu').value && r.gpu !== el('gpu').value) return false;
  if (el('strict').checked && !r.oled_title) return false;
  if (el('clean').checked && (r.flags||[]).some(f=>['SCREEN-DMG','PARTS','FAULTY','REPAIRED','BATTERY','NO-CHARGER'].includes(f))) return false;
  if (el('big').checked && !(r.screen && r.screen >= 16)) return false;
  return true;
}
function sortRows(list) {
  const s = el('sort').value;
  const by = {
    'price-asc': (a,b)=>a.price-b.price,
    'price-desc': (a,b)=>b.price-a.price,
    'gpu': (a,b)=>(b.gpu_idx||0)-(a.gpu_idx||0),
    'vram': (a,b)=>(b.vram||0)-(a.vram||0),
    'screen': (a,b)=>(b.screen||0)-(a.screen||0),
  }[s];
  return list.sort(by);
}
function chipify(r) {
  const c = [];
  c.push(`<span class="chip gpu">${r.gpu} · ${r.vram} GB</span>`);
  if (r.tgp) c.push(`<span class="chip">${r.tgp} W</span>`);
  if (r.oled_title) c.push(`<span class="chip oled">OLED · stated in title</span>`);
  else c.push(`<span class="chip weak">OLED · in description only</span>`);
  if (r.screen) c.push(`<span class="chip">${r.screen}"</span>`);
  if (r.cpu) c.push(`<span class="chip">${r.cpu}</span>`);
  if (r.ram) c.push(`<span class="chip">${r.ram} GB RAM</span>`);
  if (r.storage) c.push(`<span class="chip">${r.storage>=1024?(r.storage/1024)+' TB':r.storage+' GB'}</span>`);
  (r.flags||[]).forEach(f => c.push(`<span class="chip ${['WARRANTY','NEW'].includes(f)?'':'bad'}">${f}</span>`));
  return c.join('');
}
function card(r) {
  const d = document.createElement('div');
  d.className = 'card' + (selected===r.id?' sel':'');
  d.innerHTML = `<div class="row1"><div class="price">${baht(r.price)}${r.best?'<span class="best">cheapest</span>':''}</div>
      <div class="tag">${r.source==='detail'?'description read':'card only'}</div></div>
    <div class="title">${r.title}</div><div class="chips">${chipify(r)}</div>
    <div class="meta"><span>${r.condition||'condition ?'}</span><span>${r.location||''}</span></div>`;
  d.onclick = () => { selected = r.id; render(); showDetail(r); };
  return d;
}
function showDetail(r) {
  el('detail').innerHTML = `<h3>selected</h3>
    <div class="dtitle">${r.title}</div>
    <div class="tag">${baht(r.price)} · ${r.gpu} ${r.vram} GB · ${r.screen?r.screen+'"':'screen ?'} · ${r.oled_title?'OLED in title':'OLED in description'}</div>
    <p>${(r.desc||'No full description captured for this listing.').replace(/</g,'&lt;')}</p>
    <div class="tag">${(r.flags||[]).join(' · ')}</div>
    <div class="btnrow"><a class="linkbtn" href="${r.url}" target="_blank" rel="noopener">open on facebook</a>
      <button class="linkbtn" onclick="navigator.clipboard.writeText('${r.url}')">copy link</button></div>`;
}

const cv = el('chart'), ctx = cv.getContext('2d');
let pts = [];
function drawChart(list) {
  const dpr = window.devicePixelRatio||1, W = cv.clientWidth||340, H = 240;
  cv.width = W*dpr; cv.height = H*dpr; cv.style.height = H+'px';
  ctx.setTransform(dpr,0,0,dpr,0,0); ctx.clearRect(0,0,W,H);
  const padL=34, padR=10, padT=16, padB=30;
  const data = list.filter(r=>r.price && r.gpu_idx);
  if (!data.length) { ctx.fillStyle='#6f6885'; ctx.font='12px system-ui';
    ctx.fillText('nothing to plot', padL, H/2); pts=[]; return; }
  const x0 = Math.min(...data.map(d=>d.price))*0.9, x1 = Math.max(...data.map(d=>d.price))*1.05;
  const y0 = Math.min(...data.map(d=>d.gpu_idx))-4, y1 = Math.max(...data.map(d=>d.gpu_idx))+4;
  const X = v => padL + (v-x0)/(x1-x0)*(W-padL-padR);
  const Y = v => H-padB - (v-y0)/(y1-y0)*(H-padT-padB);
  ctx.font='10px ui-monospace';
  for (let i=0;i<=4;i++){ const v=x0+(x1-x0)*i/4;
    ctx.strokeStyle='#2a2735'; ctx.beginPath(); ctx.moveTo(X(v),padT); ctx.lineTo(X(v),H-padB); ctx.stroke();
    ctx.fillStyle='#7d7794'; ctx.textAlign='center'; ctx.fillText('฿'+Math.round(v/1000)+'k', X(v), H-padB+13); }
  for (let i=0;i<=2;i++){ const v=y0+(y1-y0)*i/2;
    ctx.strokeStyle='#2a2735'; ctx.beginPath(); ctx.moveTo(padL,Y(v)); ctx.lineTo(W-padR,Y(v)); ctx.stroke();
    ctx.fillStyle='#7d7794'; ctx.textAlign='right'; ctx.fillText(Math.round(v), padL-5, Y(v)+3); }
  pts=[];
  data.forEach(r=>{ const x=X(r.price), y=Y(r.gpu_idx), sel=selected===r.id;
    pts.push({x,y,r});
    ctx.beginPath(); ctx.arc(x,y, sel?6:4, 0, Math.PI*2);
    ctx.fillStyle = sel ? '#d9b26c' : (r.vram>=12 ? '#9d8cff' : '#6f6885'); ctx.fill(); });
}
cv.addEventListener('click', ev => {
  const rect = cv.getBoundingClientRect();
  const mx = (ev.clientX-rect.left)*cv.width/rect.width, my = (ev.clientY-rect.top)*cv.height/rect.height;
  let best=null, bd=1e9;
  pts.forEach(p=>{ const d=(p.x-mx)**2+(p.y-my)**2; if(d<bd){bd=d;best=p;} });
  if (best && bd<800) { selected=best.r.id; render(); showDetail(best.r); }
});

function render() {
  const list = sortRows(rows.filter(passes));
  const floor = list.length ? Math.min(...list.map(r => r.price)) : 0;   // badge follows the filter, not position
  list.forEach(r => { r.best = r.price === floor; });
  el('count').textContent = `${list.length} listing${list.length===1?'':'s'}`;
  const box = el('cards'); box.innerHTML='';
  if (!list.length) box.innerHTML = '<div class="empty">Nothing matches.</div>';
  list.forEach(r => box.appendChild(card(r)));
  drawChart(list);
}
render();
</script>
</body>
</html>
"""


def collect():
    """OLED + RTX rows, cheapest of each duplicate, with OLED provenance."""
    rows, _ = report.build()
    hits = []
    for r in rows:
        if not r.get("price") or not r.get("laptop", True) or r.get("dead"):
            continue
        if not r.get("oled") or not oled_report.is_rtx(r):
            continue
        title = (r.get("title") or "")
        hits.append({
            "id": r["id"], "title": title, "price": r["price"],
            "gpu": r.get("gpu"), "gpu_full": r.get("gpu_key") or "",
            "gpu_idx": r.get("gpu_perf") or 0, "vram": r.get("vram"),
            "tgp": r.get("tgp"), "cpu": r.get("cpu"), "screen": r.get("screen"),
            "ram": r.get("ram"), "storage": r.get("storage"),
            "flags": r.get("flags") or [], "condition": r.get("condition"),
            "location": r.get("location"), "desc": (r.get("desc") or "")[:900],
            "url": r.get("url"), "source": r.get("source"),
            "oled_title": "oled" in title.lower(),
            "seen": r.get("first_seen"),
        })
    hits.sort(key=lambda r: r["price"])
    seen, out = set(), []
    for h in hits:
        fp = (h["gpu"], h["screen"], h["ram"], h["storage"], round(h["price"] / 3000))
        if fp in seen:
            continue
        seen.add(fp)
        out.append(h)
    return out


def main():
    rows = collect()
    cards = harvest.load_jsonl(harvest.CARDS)
    regions = sorted({c.get("region") for c in cards if c.get("region")} - {"watchlist"})
    payload = {"rows": rows, "generated":
               datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z"),
               "scanned": len(cards), "regions": regions or ["bangkok"]}
    html = HTML.replace("__DATA__", json.dumps(payload, ensure_ascii=False))
    os.makedirs(os.path.dirname(OUT_HTML), exist_ok=True)
    with open(OUT_HTML, "w") as f:
        f.write(html)

    lines = [f"OLED + dedicated RTX — Thailand — {len(rows)} listings", ""]
    for i, r in enumerate(rows, 1):
        prov = "title" if r["oled_title"] else "description only"
        lines.append(f"{i:>2}. ฿{r['price']:,}  {r['title'][:76]}")
        lines.append(f"    {r['gpu']} {r['vram']}GB | {r['cpu'] or 'CPU ?'} | "
                     f"{r['screen'] or '?'}\" | OLED ({prov}) | RAM {r['ram'] or '?'} | "
                     f"{r['condition'] or '?'} | {r['location'] or '?'}")
        lines.append(f"    {r['url']}")
    with open(OUT_TXT, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {OUT_HTML} and {OUT_TXT}: {len(rows)} OLED+RTX listings")


if __name__ == "__main__":
    main()
