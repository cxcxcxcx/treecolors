# Data sources and licenses

The **code** in this repository is MIT-licensed (see `LICENSE`). The **tree
records** are not owned by this project and remain subject to each publisher's
license and attribution requirements.

`data/raw/`, `data/output/`, and `web/trees.pmtiles` are intentionally not
committed. If you publish a derived tileset or map, keep the attribution links
shown in the app and check the terms of every source you redistribute.

## City inventories

| Area | Source | Terms to verify |
|---|---|---|
| Washington, DC | [DDOT UFA Street Trees](https://opendata.dc.gov/datasets/urban-forestry-street-trees), [NPS cherry trees](https://www.nps.gov/subjects/cherryblossom/index.htm) | DC Open Data CC BY 4.0; NPS public-domain/attribution |
| Arlington, VA | [Arlington County DPR Trees](https://gisdata-arlgis.opendata.arcgis.com/) | Arlington County open data terms |
| Montgomery County, MD | [MCDOT inventory](https://data.montgomerycountymd.gov/), [Montgomery Parks](https://montgomeryparks.org/), Gaithersburg, Bethesda BUP | county/city open data terms |
| Baltimore, MD | [Baltimore City Open Data](https://data.baltimorecity.gov/) / TreeBaltimore | Baltimore open data terms |
| Philadelphia, PA | [Philadelphia Tree Inventory](https://opendataphilly.org/datasets/philadelphia-tree-inventory/) | OpenDataPhilly terms |
| Richmond, VA | [Richmond Tree Inventory](https://www.rva.gov/public-works/) | City of Richmond terms |
| New York City, NY | [2015 Street Tree Census](https://data.cityofnewyork.us/Environment/2015-Street-Tree-Census-Tree-Data/uvpi-gqnh) | NYC Open Data terms |
| Boston, MA | [BPRD Trees](https://data.boston.gov/dataset/bprd-trees) | Analyze Boston terms |
| Seattle, WA | [SDOT Trees](https://data.seattle.gov/) | Seattle Open Data terms |
| Portland, OR | [Street Tree Inventory](https://www.portlandmaps.com/bps/) | Portland open data terms |
| Austin, TX | [Tree Inventory](https://data.austintexas.gov/) | Austin open data terms |
| Denver, CO | [Tree Inventory](https://data.colorado.gov/Natural-Resources/Tree-Inventory-Denver/wz8h-dap6) | Colorado/Denver open data terms |
| Toronto, ON | [Street Tree Data](https://open.toronto.ca/dataset/street-tree-data/) | Open Government Licence – Toronto |
| Montreal, QC | [Public Trees](https://donnees.montreal.ca/dataset/arbres) | CC BY 4.0 (Quebec) |
| Ottawa, ON | [Tree Inventory](https://open.ottawa.ca/) | City of Ottawa open data terms |
| Calgary, AB | [Public Trees](https://data.calgary.ca/Environment/Public-Trees/tfs4-3wwa) | Open Government Licence – Calgary |
| Edmonton, AB | [Trees](https://data.edmonton.ca/Environmental-Services/Trees/eecg-fc54) | Open Government Licence – Edmonton |
| Winnipeg, MB | [Tree Inventory](https://data.winnipeg.ca/) | City of Winnipeg open data terms |
| Mississauga, ON | [City Owned Tree Inventory](https://data.mississauga.ca/) | City of Mississauga open data terms |
| Hamilton, ON | [Public Tree Inventory](https://open.hamilton.ca/) | City of Hamilton open data terms |
| Bay Area / LA / San Diego / Vancouver | legacy `py/run_*.py` sources | see individual portal terms |

## Species annotations

`data/tree_info/species_info.json` and `species_aliases.json` contain
AI-assisted species traits (deciduous/evergreen, fall color, flowering, common
names). They are derived annotations, not a source of botanical authority. If
you redistribute them, attribute the project and review the applicable OpenAI
output terms for your jurisdiction.

## Third-party software

The app uses MapLibre GL JS, PMTiles, Leaflet, OpenStreetMap tiles, Python
`requests`, `pandas`, `geopandas`, `openai`, and `tippecanoe`/`pmtiles` CLIs.
Their own licenses apply; see the dependency lockfiles and upstream projects.
