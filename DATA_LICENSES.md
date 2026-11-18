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
| Mountain View, CA | [City Tree Inventory](https://maps.mountainview.gov/arcgis/rest/services/Public/Trees/MapServer/0) (ArcGIS; vacant planting pits excluded) | City of Mountain View GIS terms |
| Milpitas, CA | [Street Tree Inventory](https://services8.arcgis.com/OPmRdssd8jj0bT5H/arcgis/rest/services/Trees/FeatureServer/0) (ArcGIS) | City of Milpitas GIS terms |
| Los Gatos, CA | [Tree Inventory](https://services.arcgis.com/NkcnS0qk4w2wasOJ/arcgis/rest/services/Los_Gatos_Tree_Inventory/FeatureServer/0) (ArcGIS; 2018 inventory, published by Santa Clara County) | Town of Los Gatos / Santa Clara County GIS terms |
| San Mateo, CA | [Street Tree Inventory](https://services2.arcgis.com/g26Y0m7OCdjU0ObA/arcgis/rest/services/Street_Trees/FeatureServer/0) (ArcGIS) | City of San Mateo Public Works GIS terms |
| Burlingame, CA | [Tree Inventory](https://services2.arcgis.com/yrktbS5Xw87hJQvs/arcgis/rest/services/WebMap_Burlingame_AllLayers_WFL1/FeatureServer/0) (ArcGIS; rows without a botanical name excluded) | City of Burlingame GIS terms |
| Brisbane, CA | [Tree Inventory](https://services9.arcgis.com/UGpGSV1ugL0pHSgX/arcgis/rest/services/Trees_PlanITGeo/FeatureServer/0) (ArcGIS; PlanITGeo inventory, rows with a blank scientific name excluded) | City of Brisbane GIS terms |
| Santa Clara, CA | [Street Trees](https://map.santaclaraca.gov/maps/rest/services/Lucity/StreetTrees/FeatureServer/0) and [Parkway Trees](https://map.santaclaraca.gov/maps/rest/services/Lucity/ParkwayTrees/FeatureServer/0) (ArcGIS/Lucity; `StatusCode = 2` "In Inventory" rows that carry a species name — trees marked `999` "Removed" are dropped because they are no longer standing; private and property-transferred trees are kept) | City of Santa Clara GIS terms |
| Santa Clara County, CA | [County tree inventories](https://services.arcgis.com/NkcnS0qk4w2wasOJ/arcgis/rest/services/Tree_Inventories_in_Santa_Clara_County_WFL1/FeatureServer/0) (ArcGIS; Saratoga, Campbell, Gilroy, Morgan Hill, San Martin and unincorporated county only — the county service also republishes Palo Alto, San Jose, Sunnyvale, Milpitas and Los Gatos, which come from their own inventories and are filtered out here) | County of Santa Clara GIS terms |
| Sunnyvale, CA | City of Sunnyvale Street Tree Inventory (spreadsheet supplied after a public records request, November 2026; 36,866 sites, data edited 2026-11-13; stumps, removals and vacant planting pits excluded) | City of Sunnyvale public records; attribution requested |
| Oakland, CA | [Trees Along Sidewalks](https://data.oaklandca.gov/dataset/TreesAlongSidewalks/svwc-9r23) (Socrata; 2006 survey — the city's newer tree exports all share one placeholder coordinate and cannot be mapped; stumps, dead trees, empty planting sites and "Tree well only" pits excluded) | City of Oakland Open Data terms |
| Pasadena, CA | [Street ROW Trees](https://services2.arcgis.com/zNjnZafDYCAJAbN0/arcgis/rest/services/Street_ROW_Trees/FeatureServer/0) (ArcGIS; `Status_Text = 'Active'`; rows with internal `ZADD` planting codes excluded) | City of Pasadena GIS terms |
| Riverside, CA | [Street Trees](https://services.arcgis.com/Fu2oOWg1Aw7azh41/arcgis/rest/services/Street_Trees/FeatureServer/0) (ArcGIS; one row per planting site, "Vacant site" excluded) | City of Riverside GIS terms |
| Redlands, CA | [Street Trees](https://services.arcgis.com/FLM8UAw9y5MmuVTV/arcgis/rest/services/Street_Trees/FeatureServer/0) (ArcGIS; one row per planting site, "Vacant site" and "Stump" excluded) | City of Redlands GIS terms |
| Sacramento, CA | [City Maintained Trees](https://services5.arcgis.com/54falWtcpty3V47Z/arcgis/rest/services/City_Maintained_Trees/FeatureServer/0) (ArcGIS; vacant sites, stumps and unknown-species rows excluded) | City of Sacramento open data terms |
| Escondido, CA | [Tree Inventory](https://services2.arcgis.com/eJcVbjTyyZIzZ5Ye/arcgis/rest/services/TreeInventory/FeatureServer/0) (ArcGIS; vacant sites and stumps excluded) | City of Escondido GIS terms |
| Encinitas, CA | [Tree Inventory](https://services2.arcgis.com/yrktbS5Xw87hJQvs/arcgis/rest/services/TreeInvEncinitas_Public/FeatureServer/0) (ArcGIS/PlanITGeo; `LifeCycleStatus = 'Active'`, vacant sites, stumps and unsuitable sites excluded) | City of Encinitas GIS terms |
| Napa, CA | [Trees Napa](https://services3.arcgis.com/HVKk0mXWDGCVpolG/arcgis/rest/services/Trees_Napa/FeatureServer/0) (ArcGIS; Davey Resource Group inventory published from a contractor account, no licence text, "Unknown Tree" excluded) | City of Napa GIS terms; provenance should be confirmed with the city |
| La Mesa, CA | [Tree Inventory](https://services3.arcgis.com/iYP51zxNr6TITn6r/arcgis/rest/services/Tree_Inventory/FeatureServer/4) (ArcGIS; vacant sites, stumps, unsuitable sites and "no replant" rows excluded; six records at (0, 0) dropped by the bbox check) | City of La Mesa GIS terms |
| Ventura, CA | [Trees](https://services.arcgis.com/dBVj4EXO3IdRPOqb/arcgis/rest/services/OpenData_AssetsOther_Trees/FeatureServer/0) (ArcGIS; "This dataset is a product of the City of San Buenaventura … cannot guarantee its accuracy" — no explicit redistribution grant; vacant sites, stumps and unsuitable sites excluded) | City of San Buenaventura terms to verify |
| Santa Monica, CA | [Santa_Monica_Trees](https://services7.arcgis.com/piPfTFmrV9d1DIvN/arcgis/rest/services/Santa_Monica_Trees/FeatureServer/0) (ArcGIS; published from a generic Esri Local Government account, not a city account; vacant sites, stumps and "asphalted well" rows excluded) | City of Santa Monica terms to verify |
| Signal Hill, CA | [Street Trees](https://services9.arcgis.com/LUBoZWfQwvBnZCmP/arcgis/rest/services/Street_Trees_public/FeatureServer/0) (ArcGIS; 2022 snapshot; vacant sites and stumps excluded) | City of Signal Hill GIS terms |
| Bay Area / LA / San Diego / Vancouver | legacy `py/run_*.py` sources | see individual portal terms |

The legacy Oakland GeoJSON (`trees_oakland.geojson`, 2013 export) is kept out
of the tiles and the stats: every row in that export carries the same
placeholder coordinate. `oakland_ca` supersedes it.

`kind="workbook"` sources are files the publisher sent rather than a REST
service. `data/raw/` is not committed, so a fresh clone needs the file placed
by hand at the path in its `SourceSpec` before `fetch` will run (the error
message names the path).

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

## Fonts

`scripts/make_og_image.py` draws `web/og-image.png` with DejaVu Sans, which is
distributed under a permissive Bitstream Vera / Arev licence and ships with most
Linux distributions (`fonts-dejavu-core`). No font file is bundled here.

## Icon artwork

The app icon's oak leaf silhouette is adapted from
[Gold heraldic oak leaf](https://commons.wikimedia.org/wiki/File:Gold_heraldic_oak_leaf.svg)
on Wikimedia Commons (CC BY 3.0), recoloured to the site palette. The
BotaniSense bird-of-paradise mark is the project's own artwork.
