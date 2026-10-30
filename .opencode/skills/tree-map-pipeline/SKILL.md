---
name: tree-map-pipeline
description: Operate and extend the Fall Color tree map at . — city registry, ArcGIS/Socrata/CSV fetchers, species resolution and GPT enrichment, QA files, species stats, and batched PMTiles builds. Use for adding a city, debugging missing species/coordinates, or understanding how the tree data is produced.
---

# Fall Color tree map pipeline

Project: `.`
Live map: `https://treecolors.botanisense.app/`

## Architecture

```text
py/tree_pipeline/
  cities.py      # CitySpec / SourceSpec registry (add a city here)
  sources.py     # ArcGIS / Socrata / CSV adapters -> normalized JSONL
  species.py     # name normalization + exact/base/alias lookup
  enrich.py      # GPT-4o fills missing species/aliases
  export.py      # dedupe, color assignment, GeoJSON + summary + QA
  web_assets.py  # web/species_stats.json + web/sources.json
  cli.py         # fetch / process / all / enrich / web-assets / tiles
```

Legacy Bay Area/LA/SD/Vancouver scripts remain in `py/run_*.py`. New cities
must go through `tree_pipeline`.

## Commands (run from `py/`)

```bash
python -m tree_pipeline list
python -m tree_pipeline fetch --city new_york_ny
python -m tree_pipeline process --city new_york_ny
python -m tree_pipeline all --city new_york_ny
python -m tree_pipeline enrich --all --dry-run
python -m tree_pipeline enrich --all
python -m tree_pipeline web-assets
python -m tree_pipeline tiles          # calls build_tiles.sh
```

Then from repo root:

```bash
./build_tiles.sh
./push.sh
```

`process --all` also calls `web_assets`; `fetch/process` are resumable because raw
JSONL is cached under `data/raw/<city>/`.

## Adding a city

1. Add a `CitySpec` + `SourceSpec` in `py/tree_pipeline/cities.py`.
2. Fetch, process, inspect `data/output/qa/<slug>.json`.
3. If `missing_species` is high, run enrichment, then process again.
4. Run `web-assets` (if not using `all`), then `./build_tiles.sh`.
5. Spot-check counts/bboxes; commit code + `data/tree_info/*.json` +
   `web/species_stats.json` + `web/sources.json`.

Fields that matter:

- `kind`: `arcgis` (default), `socrata`, `csv`.
- `species_fields` / `common_fields`: ordered candidates.
- `species_concat`: join fields, e.g. Calgary `genus` + `species`.
- `domain_field`: ArcGIS coded-value domain, e.g. Montgomery `ITEM`,
  Ottawa `SPECIES`.
- `lat_field`/`lng_field` or `point_field`.
- `invert_comma`, `split_dash`.
- `page_size`: must respect the server's `maxRecordCount`.
- `homepage`: source link shown in the popup.

## Source quirks (important)

- **DC**: use `Urban_Tree_Canopy/MapServer/23` (UFA, ~223k raw / ~201k kept).
  Do **not** use `.../MapServer/11` “DC Trees” for fall colors: ~1.8M of its
  1.99M records have `STATUS=estimated` (LiDAR + species imputation).
- **Montgomery MCDOT**: `ITEM` is a common-name code; its field *domain* maps
  `code -> "Scientific,Common"`. `fetch_domain_mapping` handles this.
  Its WAF rejects multi-clause SQL with `IS NOT NULL` / `<> ''`; keep `where`
  simple (`STATUS = 'Plant'`) and filter in Python.
- **Ottawa**: `SPECIES` is a common-name code with a 171-entry domain. The
  server is slow (~6 s per 1,000-row page). Fetching 304k rows sequentially
  takes ~30 min; a one-off 6-worker parallel fetch took ~17 min.
- **Mississauga**: `BOTNAME` is an 8-char code (`MANOOO`), `BOTDESC` is the
  common name. The exporter falls back to `common` when `raw` fails.
- **Austin**: names are comma-inverted (`Oak, Live (Southern)`); source sets
  `invert_comma=True`.
- **Seattle**: names contain backticks and truncated parentheses
  (`Prunus \`Kwanzan\` (Sato Zakura`). `species.py` strips both.
- **Portland**: layer maxRecordCount is **200**; `page_size=200`.
- **Toronto CSV**: `geometry` is a JSON `MultiPoint` string; `_point_from_value`
  handles the nested list.
- **Montreal CSV**: needs a browser UA and a Referer; `_download()` streams to a
  local CSV first because the connection can close mid-parse.
- **Socrata**: NYC `uvpi-gqnh` (`status='Alive'` -> 652k), Denver
  `wz8h-dap6`, Calgary `tfs4-3wwa` (`point`), Edmonton `eecg-fc54`,
  Winnipeg `hfwk-jp4h` (`point`).
- **ArcGIS pagination**: servers may return fewer than requested (Portland 200,
  Ottawa 1000). `_fetch_arcgis` continues on `exceededTransferLimit`.
- **Bboxes**: if `outside_bbox` is large, the bbox is too tight, not the data.
  Mississauga and Hamilton needed expansion; check raw min/max if `kept` drops.

## Species resolution

`SpeciesResolver` builds three indexes from `data/tree_info/species_info.json`:

- `exact_full`: cultivar words preserved (`ulmus frontier`)
- `exact_base`: base species/genus only (`acer rubrum`, `ulmus`)
- `alias`: every `common_names` entry

Inputs are normalized for cultivars, parentheses, `spp./var./ssp.`, hybrid `x`,
comma inversion, `SCIENTIFIC - COMMON`, backticks/missing parentheses.
Cultivar keys must not hijack genus fallback (this was a real bug).

`enrich.py` only asks GPT-4o for **species traits**, never locations. It
collects unresolved names (preferring a useful common name over a code),
batches 20, writes new entries to `species_info.json`, and aliases to
`species_aliases.json`. Current KB: ~2,300 species / ~1,500 aliases.

## QA / outputs

- `data/output/qa/<slug>.json`: raw/kept/deduped/outside/invalid/missing,
  missing top, all species counts+colors, bbox.
- `data/output/geojson/trees_<slug>.geojson`: features carry `species`, `city`,
  `source_key`, color, traits, explanation.
- `web/species_stats.json`: per-city bbox/total/all species — powers the panel.
- `web/sources.json`: `by_key` (new), `by_city`, `legacy` bboxes (old GeoJSON).
- `data/raw/` and `data/output/` are git-ignored; `data/tree_info/species_info.json`
  and `species_aliases.json` are tracked.

## Tiles / build gotchas

`build_tiles.sh` batches 4 GeoJSON files, tiles with `-z 12
--drop-densest-as-needed --maximum-tile-bytes=1500000`, merges with
`tile-join --no-tile-size-limit`, then converts to PMTiles.

- One `trees` layer, no city selector; details stay in tiles.
- `tile-join` may drop `metadata.bounds`; the frontend falls back to
  `pm.getHeader()` for the extent.
- Current all-city build is ~72 MB PMTiles. Memory is the constraint; do not
  switch back to a single tippecanoe run without checking `free -h`.
- `data/output/geojson/trees_oakland.geojson` is excluded (bad coordinates).

## Git / workspace hygiene

- `promo/` is user work and remains untracked; do not commit it.
- Generated `data/raw`, `data/output`, `web/trees.pmtiles` stay ignored.
- Track `data/tree_info/*.json`, `web/species_stats.json`, `web/sources.json`.
