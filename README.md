# laptop-hunter

A local toolkit that reads Facebook Marketplace listings for laptops in Thailand, extracts the
specifications from seller-written text, and renders them as an offline, self-contained page with
photographs and a labelled spec sheet per machine.

Built to answer one question honestly: *which used laptop here is worth the money, and what
exactly is inside it?*

Nothing runs in the cloud. No listing data leaves the machine. The browser it drives is a
throwaway copy of an existing Firefox profile.

---

## Why it is built this way

Facebook does not serve Marketplace to plain HTTP clients. Even holding a valid session, a
`requests`-style fetch returns Facebook's own 400 page — the client is fingerprinted, not rejected
for missing auth. Cookies alone are not enough.

So the harvester drives a **real headless Firefox** over the WebDriver BiDi protocol. A scratch
profile is built from an existing Firefox profile carrying only the Facebook cookies, so the live
browser is never locked, cloned wholesale, or modified.

Two consequences shaped everything else:

**There is a hard pagination wall.** A search page yields 24 cards and no more. Synthetic scrolling
does not wake the lazy loader; it wants trusted input. The way past it is to slice the query space:
each `minPrice`/`maxPrice` band, sort order and day-window returns a *different* 24-card window.
Price bands are the strongest lever.

**Recall is set by the query list, not by the parser.** A listing nobody searched for cannot be
ranked, deduplicated or enriched into existence. `analyze_gap.py` exists for this reason: it
resolves the GPU family of every card on file and checks whether any query ever asked for that
family. Families in the "never asked" column are invisible by construction.

---

## Verified behaviour (October 2026)

| thing | result |
|---|---|
| `&radius=500` on `/marketplace/bangkok/search/` | honoured, sidebar reads "Within 500 km" |
| `&radius` up to 2000 | accepted, but results stay clustered near the search city |
| `&sortBy=creation_time_descend`, `&sortBy=distance_ascend`, default | valid, different slices |
| `&sortBy=price_ascend` / `price_descend` | **invalid** — empty grid |
| deeper pagination by scrolling | does **not** load more; 24 cards per slice is the wall |
| `&minPrice=` / `&maxPrice=` | **valid** — each band returns a different 24-card set |
| `&daysSinceListed=1 / 7 / 30 / 90` | valid, different windows |
| `&itemCondition=new` / `used` | valid |
| item page | full description, condition, "Listed in <district>, <province>", photographs |
| regional marketplaces | `bangkok`, `chiangmai`, `phuket`, `khonkaen`, `songkhla` all work |
| `hatyai` slug | **broken** — silently redirects and returns California listings |

---

## Pipeline

```
make_profile.py      scratch Firefox profile (Facebook cookies only)
        |
sweep_*.py           query x price-band slicing across 5 regional marketplaces
        |
harvest.py           BiDi driver, card extraction, item-page reader
        |
specs.py             GPU/CPU/panel/RAM/storage knowledge base + text parser
detailspec.py        labelled field extraction (ports, weight, warranty, colour, …)
catalog.py           model-level fills from web lookups — cached, range-validated
        |
specsheet.py         readable template per listing + photographs
focus_site.py        filtered page: OLED + discrete GPU above N GB of VRAM
        |
data/*.html          one self-contained file, opens from file:// with no network
```

| file | purpose |
|---|---|
| `fb.py` | launch/stop headless Firefox, PID file, BiDi session self-healing |
| `bidi.py` | minimal WebDriver BiDi client (websocket) |
| `harvest.py` | sweep engine, candidate filter, item-page reader |
| `specs.py` | GPU table with verified VRAM, parser, performance and value indices |
| `detailspec.py` | second-pass extraction: resolution, refresh, ports, weight, warranty |
| `catalog.py` | model-code lookups, cached in `data/catalog.json` |
| `specsheet.py` | the labelled template and the per-listing page |
| `focus_site.py` | filtered page: OLED + discrete GPU above a VRAM floor |
| `build_site.py` | wider page over the whole pool |
| `report.py` | terminal ranking with peer-median comparison |
| `follow.py` | re-read named listing ids regardless of search results — the watchlist |
| `imgfetch.py` | add photographs to records captured before the reader kept them |
| `imgsave.py` | download photographs to `data/img/` for offline viewing |
| `watch_snapshot.py` / `new_listings.py` | snapshot the pool, then diff for genuinely new listings |
| `analyze_gap.py` | GPU families on file vs GPU families ever queried |
| `probe_titles.py` | search plain words, read what sellers actually write |
| `test_specs.py` | parser self-check against realistic Thai/English listing text |

---

## Setup

Requirements: Python 3.10+, Firefox with the Remote Agent available, `websockets`.

```bash
pip install websockets

# 1. build a scratch profile from your own Firefox profile
python3 make_profile.py .ffprofile

# 2. sweep and read item pages
FB_PORT=9222 FB_PROFILE=.ffprofile python3 sweep_focus.py 0 3
FB_PORT=9222 FB_PROFILE=.ffprofile python3 harvest.py --details-only --cap=250

# 3. photograph and render
python3 imgsave.py
python3 focus_site.py        # -> data/focus.html
```

Shard across three browsers to cut wall-clock roughly in three:

```bash
FB_PORT=9222 FB_PROFILE=.ffprofile  python3 sweep_focus.py 0 3 &
FB_PORT=9223 FB_PROFILE=.ffprofile2 python3 sweep_focus.py 1 3 &
FB_PORT=9224 FB_PROFILE=.ffprofile3 python3 sweep_focus.py 2 3 &
```

Sweep modules take `<index> <total>` and pick their own regions. `harvest.py` and `follow.py`
accept `--shard=i/n` and `--ids=file`.

---

## What the query sets look like, and why

Queries come in three shapes, because sellers describe machines in three ways:

1. **Silicon-led** — `rtx 5070 ti`, `rx 6800m`, `gtx 1650`
2. **Panel-led** — `oled 16 inch`, `จอ oled rtx`, `oled 240hz`
3. **Model-led** — `Legion Pro 5`, `Nitro V`, `TUF F15`, `Helios Neo 16S`

Thai wording matters as much as English. Sellers here write `โน้ตบุ๊คเกมมิ่ง` (gaming notebook) or
just the series name far more often than a full specification.

`probe_titles.py` is the honest way to maintain that list: search with plain category words, then
read the GPU names that appear in titles. That probe is what revealed `RTX 4050`, `RTX 5050` and the
entire GTX line had never been queried — roughly half the market was missing while the tool
reported itself healthy.

---

## Parsing rules learned the hard way

- **Item pages are contaminated.** Facebook appends recommendations for other listings. A Victus
  listing once parsed a desktop `i7-10700KF` and an OLED panel out of somebody else's advert.
  Parse the title first, then the seller's own description, **never** the raw page body.
- **Range guards are mandatory.** RAM only from a set of real capacities; storage only when an SSD
  word sits beside the number; weight only 0.9–4.5 kg; refresh only from actual panel rates;
  battery under 100 Wh. Without guards a parser cheerfully reports a 6 kg laptop and "16 GB" of
  storage that is really RAM.
- **A catalogue is not a source of truth for a series name.** "ASUS TUF Gaming" spans a dozen
  chassis with different panels, and a lookup against it quietly returns whichever ranks best.
  Catalogue fills are accepted only for keys carrying a real model code (`GU605M`, `PHN16S-71`,
  `15ACH6H`), and every such field is labelled `model spec` in the output.
- **A blank beats a confident wrong number.** Fields the seller never wrote say `not stated`.
- **The VRAM gate belongs in ranking, not discovery.** Refusing to open item pages for cards under
  12 GB once left 116 of 188 GPU listings with no specification at all.

## False positives worth excluding

Part-outs and desktop towers both masquerade convincingly: a bare RTX 3080 *chip* is not a laptop,
and a "Good PC RTX 4090 / Ryzen 9 7950X / 144 GB RAM" with a 4K OLED monitor arrives wearing a real
GPU and a real panel word. Desktop CPU SKUs (`7950X`, `7800X3D`, `9800X3D`, `14900K`, `13700K`,
`12900K`), `mainboard`, `คอมเทพ`, `พีซีประกอบ` and `ชิ้นส่วน` all force a parts flag; parts are
hidden by default.

## The watchlist

A clean sweep silently loses machines you already knew about — Facebook's matching is fussy enough
that a live, unchanged listing can fail every wording you try. Two 5070 Ti machines vanished from a
44-query sweep while still being for sale. `follow.py` re-reads named ids directly and is the
immune response. **Run it after every rebuild.**

---

## Scoring

```
perf  = 0.78 * GPU class index + 0.22 * CPU class index      (RTX 5090 Laptop = 100)
value = perf / (price / 10000)  x modifiers
```

Modifiers: OLED x1.10, 15–16" x1.03, 17"+ x0.97, ≤14.5" x0.95, RAM ≥32 GB x1.05, warranty x1.05,
repaired x0.85, no charger x0.93, dead battery x0.90, cracked screen x0.45, for-parts x0.30,
unknown VRAM x0.60.

Performance indices are **relative class estimates for ranking**, not benchmark readings. Sellers
who omit the TGP are hiding the difference between a full-power and a throttled version of the same
card: a 175 W RTX 4090 and a 60 W one are different machines.

---

## Output

- `data/focus.html` — self-contained page: photographs, a labelled spec sheet per machine, filters
  for vendor, GPU, VRAM floor and working condition, sorts for price, VRAM and baht-per-gigabyte.
  Opens from `file://` with no network and no CDN.
- `data/focus.txt` — the same information as plain text.
- `data/gpu.html` — wider version covering every listing with a discrete GPU.
- `data/index.html` — the original bang-for-buck ranking view.

---

## Caveats

- Prices, availability and panel claims come from sellers' own text. Photographs are sellers'
  images, cached locally for offline viewing only.
- Facebook image URLs expire; a fetch minutes after the page was read can return a 200-byte error
  page instead of a photograph, which is why `imgsave.py` discards files under 2 KB.
- Scraping Facebook may violate their terms of service. This is a personal research tool: it reads
  the same pages a logged-in user would see, at human pace, and writes nothing back.
- No listing should be paid for without seeing the machine.

## Licence

MIT — see `LICENSE`.
