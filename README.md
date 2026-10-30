# Fall Color Tree Map

Interactive map of individual street/park trees, colored by whether the species
is evergreen, deciduous, known for fall color, or a ginkgo. One PMTiles file
contains every city; there is no per-city selector.

## Cities

| Group | Source | Kept trees |
|---|---|---:|
| Washington, DC | DDOT UFA Street Trees + NPS Tidal Basin cherry trees | ~201k |
| Arlington, VA | Arlington County DPR Trees | ~29k |
| Montgomery County, MD | MCDOT street trees + Montgomery Parks + Gaithersburg + Bethesda BUP | ~106k |
| Baltimore, MD | Baltimore City Forestry / TreeBaltimore | ~113k |
| Philadelphia, PA | Philadelphia Parks & Recreation 2023 inventory | ~150k |
| Richmond, VA | Richmond Tree Inventory | ~77k |
| Bay Area / LA / San Diego / Vancouver | legacy `py/run_*.py` scripts | existing |

The East Coast batch is fetched by the city registry in
`py/tree_pipeline/cities.py`. Adding a city is a data change: add a `CitySpec`
with its ArcGIS layer URL and field mapping, then run the pipeline.

## Layout

```text
data/
  raw/<city>/<source>.jsonl      # fetched, normalized records (git-ignored)
  tree_info/species_info.json    # curated species trait knowledge base (tracked)
  tree_info/species_aliases.json # enrichment aliases (tracked)
  output/geojson/trees_*.geojson # one file per city
  output/summary/                # species + coordinate summaries
  output/qa/                     # per-city QA report
web/
  index.html                     # MapLibre frontend
  trees.pmtiles                  # generated, git-ignored
```

## Pipeline

Run from `py/`:

```bash
cd py

python -m tree_pipeline list
python -m tree_pipeline fetch --city washington_dc
python -m tree_pipeline process --city washington_dc
python -m tree_pipeline all --city washington_dc

# All configured cities
python -m tree_pipeline all --all

# Fill missing species with GPT-4o (offline annotation, not location prediction)
python -m tree_pipeline enrich --all
```

Then build the single tileset from the repository root:

```bash
./build_tiles.sh
```

`build_tiles.sh` auto-discovers every `data/output/geojson/trees_*.geojson`,
so adding a city does not require editing the shell script.

## Species / fall-color logic

`tree_data.build_geojson` / `tree_pipeline.export` look up each species in
`data/tree_info/species_info.json` and apply a fixed rule:

```text
Ginkgo                    -> orange
evergreen                 -> green
deciduous + fall_colors   -> red
deciduous                 -> brown
```

The knowledge base contains `deciduous`, `fall_colors`, `beautiful_flowers`,
`blooming_season`, Chinese common names, and a short explanation per species.
Names from city inventories are normalized first (cultivars, `spp.`, `var.`,
hybrid `x`, comma-inverted common names, `SCIENTIFIC - COMMON`). Missing
species are filled by the `enrich` command and cached for future runs.

## Deployment

`push.sh` syncs `web/` to the production host and bumps the service-worker
cache version. Large raw data and generated tiles stay out of git.
