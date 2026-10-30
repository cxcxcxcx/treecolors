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
| New York City, NY | NYC 2015 Street Tree Census | ~652k |
| Boston, MA | BPRD Trees | ~52k |
| Seattle, WA | SDOT Trees | ~215k |
| Portland, OR | Street Tree Inventory | ~216k |
| Austin, TX | Tree Inventory | ~59k |
| Denver, CO | Denver Tree Inventory | ~301k |
| Toronto, ON | Street Tree Data | ~617k |
| Montreal, QC | Public Trees | ~330k |
| Ottawa, ON | Tree Inventory | ~287k |
| Calgary, AB | Public Trees | ~564k |
| Edmonton, AB | Trees | ~482k |
| Winnipeg, MB | Tree Inventory | ~306k |
| Mississauga, ON | City Owned Tree Inventory | ~413k |
| Hamilton, ON | Public Tree Inventory | ~280k |
| Bay Area / LA / San Diego / Vancouver | legacy `py/run_*.py` scripts | existing |

All metro inventories are fetched by the city registry in
`py/tree_pipeline/cities.py`. Adding a city is a data change: add a `CitySpec`
with its source URL and field mapping, then run the pipeline. ArcGIS, Socrata
and CSV sources are supported.

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
  species_stats.json             # species panel stats per city (tracked)
  sources.json                   # per-tree source links (tracked)
  trees.pmtiles                  # generated, git-ignored
```

## Project skills

Operational knowledge is captured for future agent sessions:

- `.opencode/skills/tree-map-pipeline/SKILL.md` — data sources, adapters,
  species resolution, QA, and tiling.
- `.opencode/skills/tree-map-deploy/SKILL.md` — canonical URLs, nginx, deploy,
  local Range server, and CDP verification.

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

## Live map

https://treecolors.botanisense.app/

## Deployment

`push.sh` syncs `web/` to the production host and bumps the service-worker
cache version. Large raw data and generated tiles stay out of git.
