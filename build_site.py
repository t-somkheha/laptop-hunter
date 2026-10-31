#!/usr/bin/env python3
"""site.py — build a single self-contained interactive HTML report from the harvest.

No CDN, no build step: open data/index.html straight off the disk.
"""
import datetime, json, os
import report, harvest

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data", "index.html")

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
  :root {
    --bg: #131110; --panel: #1c1917; --panel2: #241f1c; --line: #362f2a;
    --ink: #efe7dd; --dim: #a89b8d; --amber: #d8b06a; --green: #7fb069; --red: #d1685f;
    --mono: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
  }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--bg); color: var(--ink);
         font: 15px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
  header { padding: 28px 32px 18px; border-bottom: 1px solid var(--line); }
  h1 { margin: 0 0 6px; font-size: 22px; letter-spacing: .3px; font-weight: 650; }
  .sub { color: var(--dim); font-size: 13px; }
  .stats { display: flex; gap: 26px; flex-wrap: wrap; margin-top: 16px; }
  .stat b { display: block; font-size: 19px; color: var(--amber); font-variant-numeric: tabular-nums; }
  .stat span { font-size: 11px; text-transform: uppercase; letter-spacing: .09em; color: var(--dim); }
  .bar { position: sticky; top: 0; z-index: 20; display: flex; gap: 12px; flex-wrap: wrap;
         align-items: center; padding: 14px 32px; background: rgba(19,17,16,.96);
         border-bottom: 1px solid var(--line); backdrop-filter: blur(6px); }
  input[type=search], select {
    background: var(--panel2); color: var(--ink); border: 1px solid var(--line);
    border-radius: 8px; padding: 9px 11px; font: inherit; font-size: 14px; }
  input[type=search] { min-width: 260px; flex: 1 1 260px; }
  input[type=search]:focus, select:focus { outline: 1px solid var(--amber); }
  .toggle { display: flex; align-items: center; gap: 7px; font-size: 13px; color: var(--dim);
            background: var(--panel2); border: 1px solid var(--line); border-radius: 8px;
            padding: 8px 11px; cursor: pointer; user-select: none; }
  .toggle input { accent-color: var(--amber); }
  .toggle.on { color: var(--ink); border-color: var(--amber); }
  .range { display: flex; align-items: center; gap: 9px; font-size: 13px; color: var(--dim); }
  input[type=range] { accent-color: var(--amber); width: 150px; }
  main { padding: 22px 32px 80px; }
  .layout { display: grid; grid-template-columns: minmax(0,1fr) 380px; gap: 24px; align-items: start; }
  @media (max-width: 1100px) { .layout { grid-template-columns: minmax(0,1fr); } }
  .count { color: var(--dim); font-size: 13px; margin-bottom: 12px; }
  .cards { display: grid; gap: 14px; }
  .card { background: var(--panel); border: 1px solid var(--line); border-radius: 12px;
          padding: 16px 18px; cursor: pointer; transition: border-color .12s, transform .12s; }
  .card:hover { border-color: #4c4238; transform: translateY(-1px); }
  .card.sel { border-color: var(--amber); box-shadow: 0 0 0 1px var(--amber) inset; }
  .row1 { display: flex; justify-content: space-between; gap: 16px; align-items: baseline; }
  .price { font-size: 19px; font-weight: 650; font-variant-numeric: tabular-nums; white-space: nowrap; }
  .delta { font-size: 11px; padding: 2px 6px; border-radius: 5px; margin-left: 8px;
           border: 1px solid var(--line); font-variant-numeric: tabular-nums; }
  .delta.cheap { color: var(--green); border-color: #375030; }
  .delta.dear { color: var(--red); border-color: #55332f; }
  .title { font-weight: 550; margin: 4px 0 10px; overflow: hidden; display: -webkit-box;
           -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
  .chips { display: flex; flex-wrap: wrap; gap: 6px; }
  .chip { font-size: 11.5px; padding: 3px 8px; border-radius: 6px; background: var(--panel2);
          border: 1px solid var(--line); color: var(--dim); white-space: nowrap; }
  .chip.gpu { color: var(--amber); border-color: #4a3d28; background: #241d13; }
  .chip.oled { color: #9ec5ff; border-color: #2c3f57; background: #17202b; }
  .chip.bad { color: var(--red); border-color: #55332f; background: #2a1a18; }
  .chip.good { color: var(--green); border-color: #375030; background: #1a2318; }
  .meta { margin-top: 10px; font-size: 12px; color: var(--dim); display: flex; gap: 14px;
          flex-wrap: wrap; }
  .side { position: sticky; top: 74px; display: grid; gap: 14px; }
  .box { background: var(--panel); border: 1px solid var(--line); border-radius: 12px; padding: 16px; }
  .box h3 { margin: 0 0 10px; font-size: 13px; text-transform: uppercase; letter-spacing: .09em;
            color: var(--dim); font-weight: 600; }
  canvas { width: 100%; height: 260px; display: block; }
  .detail .dtitle { font-weight: 600; margin-bottom: 8px; }
  .detail p { font-size: 13px; color: #d6cabc; white-space: pre-wrap; margin: 8px 0;
              max-height: 220px; overflow: auto; }
  .detail a, .linkbtn { color: var(--amber); text-decoration: none; font-size: 13px; }
  .btnrow { display: flex; gap: 10px; margin-top: 10px; flex-wrap: wrap; }
  .linkbtn { border: 1px solid var(--line); background: var(--panel2); border-radius: 7px;
             padding: 6px 10px; cursor: pointer; font: inherit; font-size: 12.5px; }
  .linkbtn:hover { border-color: var(--amber); }
  .empty { color: var(--dim); padding: 30px 0; }
  footer { color: var(--dim); font-size: 12px; padding: 0 32px 40px; }
  .tag { font-family: var(--mono); font-size: 11px; color: var(--dim); }
</style>
</head>
<body>
<header>
  <h1>__TITLE__</h1>
  <div class="sub">__SUBTITLE__</div>
  <div class="stats" id="stats"></div>
</header>

<div class="bar">
  <input type="search" id="q" placeholder="search model, seller text, province…">
  <select id="sort">
    <option value="value">sort: bang for buck</option>
    <option value="perf">sort: raw performance</option>
    <option value="price-asc">sort: price low → high</option>
    <option value="price-desc">sort: price high → low</option>
    <option value="new">sort: newest listing</option>
  </select>
  <select id="gpu"><option value="">all GPUs</option></select>
  <label class="toggle" id="oledWrap"><input type="checkbox" id="oled"> OLED only</label>
  <label class="toggle" id="cleanWrap"><input type="checkbox" id="clean"> no damage flags</label>
  <label class="toggle"><input type="checkbox" id="sixteen"> 15–16" only</label>
  <label class="toggle" id="oledrtxWrap"><input type="checkbox" id="oledrtx"> OLED + RTX only</label>
  <label class="toggle"><input type="checkbox" id="miss"> include under-12 GB &amp; unknowns</label>
  <div class="range">max ฿ <b id="maxLabel"></b>
    <input type="range" id="max" min="0" max="100" value="100"></div>
</div>

<main>
  <div class="layout">
    <div>
      <div class="count" id="count"></div>
      <div class="cards" id="cards"></div>
    </div>
    <aside class="side">
      <div class="box">
        <h3>price vs performance</h3>
        <canvas id="chart" width="700" height="520"></canvas>
        <div class="tag" id="chartHint">click a dot to open that listing</div>
      </div>
      <div class="box detail" id="detail">
        <h3>selected listing</h3>
        <div class="tag">pick a card</div>
      </div>
    </aside>
  </div>
</main>
<footer id="foot"></footer>

<script type="application/json" id="payload">__DATA__</script>
<script>
const D = JSON.parse(document.getElementById('payload').textContent);
const rows = D.rows, med = D.medians, gen = D.generated;
const baht = n => '฿' + (n || 0).toLocaleString('en-US');
let selected = null;

// ---------- header stats
const el = id => document.getElementById(id);
const q = rows.filter(r => r.qual);
const prices = q.map(r => r.price).sort((a,b)=>a-b);
el('stats').innerHTML = [
  ['listings scanned', D.scanned],
  ['cleared 12 GB gate', q.length],
  ['OLED among them', q.filter(r=>r.oled).length],
  ['cheapest qualifier', baht(prices[0]||0)],
  ['median qualifier', baht(prices.length ? prices[Math.floor(prices.length/2)] : 0)],
].map(([k,v]) => `<div class="stat"><b>${v}</b><span>${k}</span></div>`).join('');
el('foot').innerHTML = `generated ${gen} · radii ${D.radius} km around Bangkok · ` +
  `performance indices are class estimates, not benchmarks · verify TGP and battery health ` +
  `with the seller before paying.`;

// ---------- GPU filter options, ordered by class index
const gpus = [...new Set(q.map(r=>r.gpu))].sort((a,b) =>
  (med[b]?.perf||0) - (med[a]?.perf||0) || a.localeCompare(b));
el('gpu').innerHTML += gpus.map(g=>`<option value="${g}">${g}</option>`).join('');

// ---------- filters
const maxPrice = Math.ceil((Math.max(...q.map(r=>r.price), 100000)) / 5000) * 5000;
el('max').max = maxPrice; el('max').value = maxPrice;
const syncMax = () => { el('maxLabel').textContent = baht(+el('max').value); };
syncMax();
el('max').addEventListener('input', () => { syncMax(); render(); });
['q','sort','gpu','oled','clean','sixteen','miss','oledrtx'].forEach(id =>
  el(id).addEventListener(id === 'q' ? 'input' : 'change', render));
['oled','clean','sixteen','miss','oledrtx'].forEach(id =>
  el(id).addEventListener('change', () => el(id).closest('.toggle').classList.toggle('on', el(id).checked)));

function passes(r) {
  const term = el('q').value.trim().toLowerCase();
  if (term) {
    const hay = (r.title + ' ' + (r.desc||'') + ' ' + (r.location||'') + ' ' +
                 (r.gpu||'') + ' ' + (r.cpu||'')).toLowerCase();
    if (!hay.includes(term)) return false;
  }
  if (el('gpu').value && r.gpu !== el('gpu').value) return false;
  if (el('oled').checked && !r.oled) return false;
  if (el('oledrtx').checked && !(r.oled && /rtx/i.test(r.gpu || ''))) return false;
  if (el('clean').checked && (r.flags||[]).some(f => ['SCREEN-DMG','PARTS','REPAIRED','BATTERY','NO-CHARGER','NO-WARRANTY'].includes(f))) return false;
  if (el('sixteen').checked && !(r.screen && r.screen >= 15 && r.screen <= 16.5)) return false;
  if (r.price > +el('max').value) return false;
  return true;
}

function sortRows(list) {
  const s = el('sort').value;
  const by = {
    'value': (a,b) => (b.value||0) - (a.value||0),
    'perf': (a,b) => (b.perf||0) - (a.perf||0),
    'price-asc': (a,b) => a.price - b.price,
    'price-desc': (a,b) => b.price - a.price,
    'new': (a,b) => String(b.first_seen||'').localeCompare(String(a.first_seen||'')),
  }[s];
  return list.sort(by);
}

function deltaBadge(r) {
  const m = med[r.gpu];
  if (!m || !m.price || (m.n || 0) < 3) return '';   // a "median" of two listings is noise
  const d = 100 * (r.price - m.price) / m.price;
  const cls = d < -3 ? 'cheap' : d > 3 ? 'dear' : '';
  const sign = d > 0 ? '+' : '';
  return `<span class="delta ${cls}" title="peer median ${baht(m.price)}">${sign}${d.toFixed(0)}% vs peers</span>`;
}

function chipify(r) {
  const c = [];
  if (r.gpu) c.push(`<span class="chip gpu">${r.gpu}${r.vram?` · ${r.vram} GB`:''}</span>`);
  if (r.dead) c.push(`<span class="chip bad">for parts / dead</span>`);
  else if (r.qual === false) c.push(`<span class="chip bad">${r.vram ? 'under 12 GB' : 'specs unknown'}</span>`);
  if (r.tgp) c.push(`<span class="chip">${r.tgp} W TGP</span>`);
  if (r.cpu) c.push(`<span class="chip">${r.cpu}</span>`);
  if (r.screen) c.push(`<span class="chip">${r.screen}"</span>`);
  if (r.oled) c.push(`<span class="chip oled">OLED</span>`);
  if (r.ram) c.push(`<span class="chip">RAM ${r.ram} GB</span>`);
  if (r.storage) c.push(`<span class="chip">${r.storage >= 1024 ? (r.storage/1024)+' TB' : r.storage+' GB'} SSD</span>`);
  (r.flags||[]).forEach(f => {
    const good = ['WARRANTY','NEW'].includes(f);
    c.push(`<span class="chip ${good?'good':'bad'}">${f}</span>`);
  });
  return c.join('');
}

function card(r) {
  const div = document.createElement('div');
  div.className = 'card' + (selected === r.id ? ' sel' : '');
  div.innerHTML = `
    <div class="row1"><div class="price">${baht(r.price)}${deltaBadge(r)}</div>
      <div class="tag">${r.perf ? 'perf ' + r.perf : ''} ${r.value ? '· value ' + r.value : ''}</div></div>
    <div class="title">${r.title || '(untitled)'}</div>
    <div class="chips">${chipify(r)}</div>
    <div class="meta"><span>${r.condition || 'condition ?'}</span><span>${r.location || ''}</span>
      <span>${r.source === 'detail' ? 'full description read' : 'card only'}</span></div>`;
  div.onclick = () => { selected = r.id; render(); showDetail(r); };
  return div;
}

function showDetail(r) {
  el('detail').innerHTML = `
    <h3>selected listing</h3>
    <div class="dtitle">${r.title || '(untitled)'}</div>
    <div class="tag">${baht(r.price)} · ${r.gpu || 'GPU ?'} ${r.vram ? '· ' + r.vram + ' GB' : ''}
      ${r.oled ? '· OLED' : ''} ${r.screen ? '· ' + r.screen + '"' : ''}</div>
    <p>${(r.desc || 'No description captured for this listing.').replace(/</g,'&lt;')}</p>
    <div class="tag">${(r.flags||[]).join(' · ') || ''}</div>
    <div class="btnrow">
      <a class="linkbtn" href="${r.url}" target="_blank" rel="noopener">open on facebook</a>
      <button class="linkbtn" onclick="navigator.clipboard.writeText('${r.url}')">copy link</button>
    </div>`;
}

function render() {
  let list = q.filter(passes);
  if (el('miss').checked) list = list.concat(rows.filter(r => !r.qual && passes(r)));
  list = sortRows(list);
  el('count').textContent = `${list.length} listing${list.length===1?'':'s'} match`;
  const box = el('cards');
  box.innerHTML = '';
  if (!list.length) box.innerHTML = '<div class="empty">Nothing matches these filters.</div>';
  list.forEach(r => box.appendChild(card(r)));
  drawChart(list);
}

// ---------- scatter: price vs performance
const cv = el('chart'), ctx = cv.getContext('2d');
let chartPts = [];
function drawChart(list) {
  const dpr = window.devicePixelRatio || 1;
  const W = cv.clientWidth || 340, H = 300;
  cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr);
  cv.style.height = H + 'px';
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, W, H);
  const padL = 34, padR = 12, padT = 26, padB = 38;
  const pts = list.filter(r => r.perf && r.price);
  if (!pts.length) {
    ctx.fillStyle = '#6f6459'; ctx.font = '13px system-ui';
    ctx.fillText('nothing to plot with these filters', padL, H / 2);
    chartPts = []; return;
  }
  const xs = pts.map(p => p.price), ys = pts.map(p => p.perf);
  const x0 = Math.min(...xs) * 0.9, x1 = Math.max(...xs) * 1.05;
  const y0 = Math.min(...ys) - 4, y1 = Math.max(...ys) + 4;
  const X = v => padL + (v - x0) / (x1 - x0) * (W - padL - padR);
  const Y = v => H - padB - (v - y0) / (y1 - y0) * (H - padT - padB);
  ctx.font = '10.5px ui-monospace'; ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const v = x0 + (x1 - x0) * i / 4, px = X(v);
    ctx.strokeStyle = '#2b2521';
    ctx.beginPath(); ctx.moveTo(px, padT); ctx.lineTo(px, H - padB); ctx.stroke();
    ctx.fillStyle = '#7b6f63'; ctx.textAlign = 'center';
    ctx.fillText('฿' + Math.round(v / 1000) + 'k', px, H - padB + 14);
  }
  for (let i = 0; i <= 3; i++) {
    const v = y0 + (y1 - y0) * i / 3, py = Y(v);
    ctx.strokeStyle = '#2b2521';
    ctx.beginPath(); ctx.moveTo(padL, py); ctx.lineTo(W - padR, py); ctx.stroke();
    ctx.fillStyle = '#7b6f63'; ctx.textAlign = 'right';
    ctx.fillText(Math.round(v), padL - 6, py + 3.5);
  }
  ctx.textAlign = 'left'; ctx.fillStyle = '#6f6459'; ctx.font = '10.5px system-ui';
  ctx.fillText('performance \u2192', padL, 14);
  ctx.fillStyle = '#8fa8c8'; ctx.fillText('\u25cf OLED', padL + 86, 14);
  ctx.fillStyle = '#8a7b6a'; ctx.fillText('\u25cf other', padL + 148, 14);
  chartPts = [];
  pts.forEach(p => {
    const x = X(p.price), y = Y(p.perf), sel = selected === p.id;
    chartPts.push({x, y, r: p});
    ctx.beginPath(); ctx.arc(x, y, sel ? 6.5 : 4.5, 0, Math.PI * 2);
    ctx.fillStyle = sel ? '#d8b06a' : (p.oled ? '#9ec5ff' : '#8a7b6a');
    ctx.fill();
    if (sel) { ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.5; ctx.stroke(); }
  });
}
cv.addEventListener('click', ev => {
  const rect = cv.getBoundingClientRect();
  const mx = (ev.clientX - rect.left) * cv.width / rect.width;
  const my = (ev.clientY - rect.top) * cv.height / rect.height;
  let best = null, bd = 1e9;
  chartPts.forEach(p => { const d = (p.x-mx)**2 + (p.y-my)**2; if (d < bd) { bd = d; best = p; } });
  if (best && bd < 900) { selected = best.r.id; render(); showDetail(best.r); }
});

// ?p=oledrtx opens the page already filtered to OLED + dedicated RTX
if (/[?&]p=oledrtx/.test(location.search)) {
  el('oledrtx').checked = true;
  el('miss').checked = true;
  el('oledrtx').closest('.toggle').classList.add('on');
  el('miss').closest('.toggle').classList.add('on');
}
render();
</script>
</body>
</html>
"""


def main():
    rows_raw, rejected = report.build()
    med = {}
    for r in rows_raw:
        if r.get("vram") and r["vram"] >= 12 and r.get("perf") and r.get("price"):
            m = med.setdefault(r["gpu"], {"price": [], "perf": []})
            m["price"].append(r["price"])
            m["perf"].append(r["perf"])
    import statistics
    medians = {k: {"price": statistics.median(v["price"]), "perf": statistics.median(v["perf"]),
                   "n": len(v["price"])} for k, v in med.items()}

    out_rows = []
    for r in rows_raw:
        out_rows.append({
            "id": r["id"], "title": r.get("title"), "price": r.get("price"),
            "gpu": r.get("gpu"), "vram": r.get("vram"), "tgp": r.get("tgp"),
            "cpu": r.get("cpu"), "screen": r.get("screen"), "oled": bool(r.get("oled")),
            "ram": r.get("ram"), "storage": r.get("storage"), "perf": r.get("perf"),
            "value": r.get("value"), "flags": r.get("flags") or [],
            "condition": r.get("condition"), "location": r.get("location"),
            "desc": (r.get("desc") or "")[:900], "url": r.get("url"),
            "source": r.get("source"), "first_seen": r.get("first_seen"),
            "qual": bool(r.get("vram") and r["vram"] >= 12 and r.get("perf")
                         and r.get("price") and not r.get("dead")),
            "dead": bool(r.get("dead")),
        })

    cards = harvest.load_jsonl(harvest.CARDS)
    payload = {
        "rows": out_rows,
        "medians": medians,
        "scanned": len(cards),
        "radius": 500,
        "generated": datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z"),
    }
    qual = [x for x in out_rows if x["qual"]]
    title = "Laptop hunt — Thailand"
    regions = sorted({c.get("region") for c in cards if c.get("region")})
    subtitle = (f"{len(cards)} listings swept across {len(regions) or 1} regions "
                f"({', '.join(regions)}) · {len(qual)} clear 12 GB VRAM · "
                f"ranked by performance per baht · data written {payload['generated']}")
    html = (HTML.replace("__DATA__", json.dumps(payload, ensure_ascii=False))
                .replace("__TITLE__", title).replace("__SUBTITLE__", subtitle))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        f.write(html)
    print(f"wrote {OUT} ({len(html)/1024:.0f} KB, {len(out_rows)} rows, {len(qual)} qualified)")


if __name__ == "__main__":
    main()
