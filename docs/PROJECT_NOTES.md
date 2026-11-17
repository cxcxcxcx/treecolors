# TreeColors — project notes

Everything learned building `treecolors.botanisense.app`: what the system is,
why it is shaped this way, and which mistakes not to repeat. Read this before
touching the map; read `docs/DATA_SOURCES.md` before quoting any number.

## What it is

One PMTiles vector file with every mapped street tree in North America, coloured
by species group — evergreen / ginkgo / turns in autumn / deciduous but muted.
Click any tree → species, a botanical plate, Wikipedia photos and the source
inventory record. No per-city selector, no account.

Current shape (2026-11): **40 cities, 6.64M trees, 1,773 species keys**, 298
botanical plates, 315 leaf thumbnails, `web/trees.pmtiles` ≈ 77 MB.

## Architecture

```
data/raw/<city>/*.jsonl          city inventories (cached fetches)
data/output/geojson/*.geojson    one file per city: kept trees + colour
data/output/qa/<city>.json       pipeline report for cities in the config
data/output/qa/derived/          reports reconstructed from GeoJSON (legacy CA)
web/trees.pmtiles                tiles built from the GeoJSON (build_tiles.sh)
web/species_stats.json           per-city species counts + plate/leaf/key
web/sources.json                 per-tree link back to the publisher
web/plates/, web/leaves/         artwork, keyed by slug(canonical species key)
```

Pipeline: `python3 -m tree_pipeline process --all` → `web-assets` →
`./build_tiles.sh` → `./push.sh` (rsync). Details and ground-truth rules:
`docs/DATA_SOURCES.md`.

## Product decisions worth keeping

- **PMTiles + one layer.** No city picker; the map is the index.
- **Species colours are deterministic** (`deterministic_color`). Ginkgo is a
  single literal `orange`; red/brown/green ranges are hashes within a hue band.
  The legend must match the data, not a designer's gradient.
- **One species, one colour, in every city** (user, 2026-11-15: the same tree in
  two colours is badly confusing). `species_color()` hashes the binomial, so
  spelling, case and cultivar never change the colour; the category comes from
  the *current* KB, never from whatever an old export stored. After any KB edit:
  `scripts/recolor_geojson.py --sync-traits` → `web-assets` → `build_tiles.sh`
  (→ `export_guides.py` for the botanisense.app guides).
- **Categories mean what the leaves do in autumn.** red = colours before
  dropping (red, purple *or* yellow); orange = ginkgo; brown = deciduous but no
  real autumn display (drawn very dark, near black); green = keeps its leaves.
  - *Purple-leaf plum* (`prunus cerasifera` and cultivars) is **brown**, not
    red (decided 2026-11-15). It is purple from spring to fall, so it is not an
    autumn colour, and counting it added ~7 points to SF's "turning" share and
    skewed Santa Clara. It is deciduous, so it is never green. A separate
    "coloured all year" category (purple plum, copper beech, 'Forest Pansy'
    redbud, 'Crimson King' maple) was considered and left for later: it needs a
    KB field, a legend row and stats changes, for ~50k plums out of 6.64M trees.
  - *Chinese elm / lacebark elm* (`ulmus parvifolia` and cultivars) is
    **green** (user, 2026-11-15). In cold climates it is deciduous with yellow
    to purplish-red fall colour (NCSU; commit 0c935d1 had set it red), but in
    the mild California climates most of our content covers it keeps its
    leaves through winter, and there is one category per species, not per
    climate. As red it had pushed SF from ~16% to 18% (32k trees across all
    cities). Revisit if a cold-climate city guide (e.g. Calgary) needs it.
- **Artwork covers the head, not the tail.** 298 plates cover ~95% of trees;
  missing artwork is normal and the UI hides the block.
- **Bottom sheet, not anchored popup.** A fixed sheet cannot be clipped by the
  viewport, works the same on mobile, and leaves the tree visible via a pan.
- **The list and the map share one filter.** Typing in the search dims
  non-matching trees and ignores clicks on them; otherwise the list lies.
- **"You are here" is a control, not a decoration.** The dot is 18px but its
  button is 44px, and tapping it re-reads the GPS (`maximumAge` 30 s, not the
  10 min the startup locate accepts). After the first fix a
  `watchPosition` keeps the dot current without moving the camera.
- **Navigation is one icon, not a text block.** The tree sheet has a single
  round map button to the right of the common/botanical name pair; it hands
  the pin to the system's map (`geo:` on Android so the OS offers its
  chooser, Apple Maps on iOS, the Google Maps web app on desktop). We never
  build directions and never ask the visitor to pick a platform. It only
  appears when the sheet was opened from a tree with coordinates — a
  species-list row has no pin.
- **Locate lives on the map, not in the legend.** It is a MapLibre control
  stacked under the zoom buttons (top-right); collapsing the legend must
  never hide it. The species panel starts at 148px so it clears that stack.
- **The compass stays, and it must say when it matters.** Two fingers rotate
  the map, so reset-to-north is a real action. MapLibre's stock needle is
  grey whether you are upright or rotated 40° — an invisible state change.
  Tint it (needle + button background) whenever `map.getBearing() != 0` and
  keep the label "Map faces north" / "Map is rotated — tap to face north".
  Do not remove it on the grounds that north is usually up.
- **Install is visible whenever the app is not installed.** Do not gate it on
  `beforeinstallprompt`: Safari and Firefox never fire it, and Chromium fires
  it only after engagement heuristics, which made the button vanish on
  iPhones and on first visits. Where the event exists we open the native
  dialog; otherwise the click explains Share → Add to Home Screen (iOS),
  File → Add to Dock (desktop Safari), or the browser menu.
- **Locating must not stare at a blank map.** After `flyTo`, zoom out until the
  viewport holds a few thousand mapped trees — but wait for the tiles first, and
  require two consecutive empty reads so a slow tile cannot trigger a zoom-out.

## UI principles

1. Product name first, status second, actions last. The legend's footer holds
   About · BotaniSense on the left and install on the right. Locate is a map
   control (above) — the footer is not the place for a primary action.
2. One consistent bottom bar on promo art: TreeColors plate left, quiet
   `by BotaniSense` + slogan right. Only the product gets a highlight.
3. Headlines must not carry "map" — it is visibly a map. Do not sell city counts.
4. Numbers on an image must come from `web/species_stats.json`, never typed by
   hand; they go stale otherwise.
5. Anything that changes layout needs a browser check: `python3 tests/ui/check_ui.py`
   (10 assertions, headless Chrome, exits non-zero).

## Copy principles (EN + zh)

- Lead with the job: "same bay, three times the colour", not "we built a map".
- Give the contrast, not the feature list: 15% vs 50% is the argument.
- Define loaded words once ("a tree *turns* when its leaves go red, purple or
  yellow before falling").
- City names stay in English in the Chinese copy; the surrounding prose is
  Chinese.
- 小红书 cannot carry links → the full domain must be legible in the image and
  repeated in the caption. No slide-by-slide narration; describe the tool, then
  what changed this year.
- Mention the BotaniSense app in one sentence (organises plant photos, in the
  app stores) — no more.

## Things that bit us

| Symptom | Cause | Fix |
|---|---|---|
| Map looked empty after locating | zoomed to z13 before tiles loaded, counted 0 features | wait for `sourcedata`, two empty reads before stepping back |
| Freeze when zooming out | `queryRenderedFeatures` over the whole viewport at z7 | count rendered features only at z≥10, else use city totals |
| Same species, two colours | KB keyed by common name *and* binomial | `merge_duplicate_keys.py`, then rebuild tiles |
| Same species, different colour per city | old exports hashed the raw inventory name ("PISTACIA CHINENSIS" ≠ "Pistacia chinensis"), and old cities kept categories from an older KB | `species_color()` hashes the binomial; `scripts/recolor_geojson.py --sync-traits`, `web-assets`, rebuild tiles |
| `merge_duplicate_keys.py` missed "chinese pistache" | genus list needed ≥3 alias targets, so Pistacia/Sequoia weren't genera | any alias-target head is a genus, minus `NOT_GENERA`; binomial's traits win on merge |
| Plate showed a green tree for a species that turns | `fall_colors` read as "spectacular", not "changes" | prompt now always shows the real autumn state |
| Legend colours drifted from the map | reviewer replaced split swatches with gradients | keep the exact hex pairs, hard 50% stop |
| Preview URL served a stale image | Cloudflare 4 h cache on `/preview/` | new filename per revision, never overwrite |
| Page reloaded itself on first visit | `controllerchange` fires on first SW install | only reload when a controller already existed |
| Chrome/CDP timed out mid-check | box at ~1.5 GB free RAM | 1000×1000 captures, `--disable-dev-shm-usage`, check `free -h` |
| `.gitignore` swallowed `assets/icon/` | macOS template's bare `Icon` pattern | use `assets/iconography/` |

## Costs and batch workflow

Gemini `gemini-nano-banana-2.1`, Batch tier: 1K $0.0168, 2K $0.0252 per image.
One 3×3 sheet is one image, so nine species cost one call. 298 plates + 315
leaves cost roughly $2. Artwork runs go through `scripts/batch_plates.py`
(plan / submit / status / download, resumable state in `data/work/`).

## Where things live

- `scripts/` — pipeline helpers, artwork (`gen_plates`, `batch_plates`), icons
  (`build_icon_flower`), promo (`make_promo`).
- `docs/` — data ground truth, promo spec, this file.
- `assets/iconography/versions/` — every shipped icon with its source vector.
- `.opencode/skills/tree-map-pipeline/` — the in-repo operator runbook.
- Skills kept local to the maintainer (not in this repo): `treecolors-artwork`
  (artwork + data rules), `treecolors-promo` (images + copy), and
  `tree-map-deploy` (host topology, nginx, CDN). The deploy runbook is out of
  the repo on purpose — it names the production host — but `./push.sh` plus
  `.deploy.env` is enough for anyone else.
