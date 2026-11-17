# Regional coverage survey — what was investigated and left out

Compiled 17 November 2026 for treecolors.botanisense.app.

This is the baseline for regions that were looked at and **not** added (or added
later): the North Bay, San Diego County and Southern California. It exists so a
future pass can tell *what changed* from *what was always true*, instead of
re-running the whole search from memory.

Every number below came from a live query against the publisher's REST service
on 16–17 November 2026. Nothing is copied from a portal blurb. Service names,
counts, "last data edit" timestamps and verdicts are recorded so each row can be
re-checked with one `curl`.

`docs/SOUTH_BAY_PENINSULA_SOURCES.md` covers the South Bay and Peninsula the
same way; this file does not repeat it.

## Method

Three passes per region:

1. **ArcGIS Online item search** restricted to the city or town name, then the
   region's bounding box (`search?q=title:"tree"&bbox=…`), sorted by views.
2. **The city's own REST directory** where one is published, and its open-data
   portal (Socrata `/api/catalog/v1`, or the dataset index HTML).
3. **The county service** that republishes several city inventories, where one
   exists.

Every candidate that survived was then measured:

```bash
# row count
…/FeatureServer/0/query?where=1=1&returnCountOnly=true&f=json
# species composition, one row per spelling
…/FeatureServer/0/query?where=1=1&groupByFieldsForStatistics=<SPECIES_FIELD>
  &outStatistics=[{"statisticType":"count","onStatisticField":"OBJECTID",
                   "outStatisticFieldName":"n"}]
  &orderByFields=n+DESC&returnGeometry=false&f=json
# where the data actually is, and whether it is stale
…/FeatureServer/0/query?where=1=1&returnExtentOnly=true&outSR=4326&f=json
…/FeatureServer/0?f=json        # editingInfo.dataLastEditDate
```

### Definitions used here

- **Usable** — rows the pipeline would keep: species name present and not a
  placeholder (`vacant site`, `stump`, `other tree`, `unknown`, …) *and*
  resolvable by `species.py`. Computed with `is_invalid()` and
  `SpeciesResolver.resolve()` against the current knowledge base. This is an
  estimate: the real pipeline also drops duplicates and out-of-bbox rows.
- **Turn %** — share of usable trees whose species is `red` (deciduous with
  `fall_colors`) or `orange` (ginkgo), i.e. the share the map paints as turning.
  Same definition as `scripts/readme_cities.py`, so it is comparable to the city
  table in the README.
- **Addable** — could go on the map today as a data-only `CitySpec`.
- **Not usable** — no per-tree species; canning data only; gated; or a sample
  that would misrepresent a city.

## Summary

| Region | Layer | Rows | Usable | Turn | Verdict |
|---|---|---:|---:|---:|---|
| North Bay | Napa `Trees_Napa` | 34,127 | 33,573 | 57.0% | **addable** (provenance to confirm) |
| North Bay | Petaluma ROW + Park | 7,487 | ~7,124 | ~50% | **addable**, sample survey — see correction |
| North Bay | San Rafael `Trees_points` | 22,282 | 6,029 | 91.5% | **not usable** (72.4% "Other-Unknown") |
| North Bay | Calistoga `Calistoga_Tree_Points` | 588 | 0 | — | **not usable** (no species field) |
| North Bay | St. Helena `StHelenaTreeInventory2025` | ? | ? | — | **gated** (token required) |
| North Bay | Santa Rosa fire-damaged survey | 705 | — | — | **not usable** (not an inventory) |
| North Bay | Yountville_Trees (11 layers) | 1,209 | 0 | — | **not usable** (letter codes, no dictionary) |
| San Diego | La Mesa `Tree_Inventory` | 13,359 | 9,190 | 16.8% | **addable** |
| San Diego | SD `Street_Tree_Inventory_for_RSG` | 19,581 | 16,732 | 12.0% | **addable** (superset of D4) |
| San Diego | SD `San_Diego_District_4_Trees` | 16,553 | 14,643 | 11.3% | addable, but 34.5% inside RSG |
| San Diego | SD `Encanto_Planning_Area_Tree_Map` | 6,147 | 5,384 | 8.7% | subset of D4 — do not add separately |
| San Diego | Solana Beach iTree benefits | 1,166 | 1,112 | 10.0% | sample only |
| SoCal | Ventura `OpenData_AssetsOther_Trees` | 47,386 | 28,439 | 13.9% | **addable** (official account) |
| SoCal | Anaheim `Master_Anaheim_Tree_Inventory` | 87,291 | 61,347 | 21.4% | **addable pending licence** |
| SoCal | Santa Monica `Santa_Monica_Trees` | 34,992 | 30,485 | 9.1% | **addable pending provenance** |
| SoCal | Signal Hill `Street_Trees_public` | 3,879 | 2,723 | 21.6% | addable, 2022 vintage |

If everything marked addable were taken, the map would gain roughly **189,000
trees** — about 2.7% on top of the current 7.04M, concentrated in the three
regions the map currently covers worst (North Bay, San Diego County, Ventura
County).

## North Bay

### Napa — usable, found on re-probe

`Trees_Napa`, owner `holly.knox_DRG_GIS` (a Davey Resource Group account, not a
city account):

```
https://services3.arcgis.com/HVKk0mXWDGCVpolG/arcgis/rest/services/Trees_Napa/FeatureServer/0
```

- **34,127 rows**, 34,127 distinct `UNIQUEID`, 271 distinct `SPECIES_BO`.
- Fields: `FID, ID, UNIQUEID, SPECIES_CO, SPECIES_BO, DBH`. Species is
  complete: the only unusable value is `Unknown Tree` (99 rows).
- Geometry is Web Mercator (`wkid 102100`) but `outSR=4326` returns correct
  WGS84 points; bbox 38.245–38.351 N, 122.352–122.256 W (the city, not the
  county).
- Last data edit **2024-08-06**.
- Top species: Crapemyrtle 6,325 · Coast Live Oak 3,640 · Chinese Pistache 2,506
  · Red Maple 2,032 · Valley Oak 1,696 · Trident Maple 1,602.

Earlier passes missed this because they looked at
`TreePlantingNapaCA`, which is a `CityLimits` polygon for canopy statistics
(one row), not a tree layer. The mislabelled "Napa has no tree data" was wrong.

**Caveat:** the item has no description, no licence, and is published from a
contractor's personal ArcGIS account. Before it goes live, confirm the city
stands behind it — the same standard applied to Burlingame.

### Petaluma — correction: this is a real inventory

Earlier notes said Petaluma was "a random sample plus parks only". That was
wrong: it came from inspecting only the `Random sample trees` layer (359
points). The publisher (`CA_Urban_Forests_Council`) also hosts two much larger
layers:

```
ROW    https://services5.arcgis.com/BqxiHToJxUMLZkJn/arcgis/rest/services/ROW_Tree_inventory_(final)/FeatureServer/0
Parks  https://services5.arcgis.com/BqxiHToJxUMLZkJn/arcgis/rest/services/Petaluma_Park_Trees_(final)/FeatureServer/0
```

| Layer | Rows | Distinct species | Usable | Turn | Top species |
|---|---:|---:|---:|---:|---|
| ROW | 3,651 | 108 (`Latin`) | 3,640 | 65.4% | London Plane 630 · Crape Myrtle 420 · Callery Pear 395 · Red Maple 387 · Chinese Pistache 305 |
| Parks | 3,836 | 131 (`Species`) | 3,484 | 33.0% | Coast Live Oak 569 · Coast Redwood 431 · Valley Oak 364 · London Plane 328 |

Only **8** points coincide within 3 m, so the two layers are additive:
**7,487 trees, ~7,124 usable**. Last data edit **2025-03-12** (both).

**Caveat, stated by the publisher:** the ROW item is titled *"Partial ROW Tree
inventory (not random)"* and its description says *"Should not be used for
statistical analysis as this data is not random. Output generated from running
the Join Features analysis tool."* It is a survey of real street trees, not a
complete municipal register — fine for "what is planted where", not for "share
of the city's street trees". Labelling the layer as a partial survey matters
for how its turn share (65%) is quoted: it is the share of the surveyed trees,
not of all of Petaluma.

Also present: `PetalumaTrees_10_10_24` (5,602 rows, 403 with a blank species, a
combined street+park export). It is older and dirtier than the two `(final)`
layers; do not use it.

### San Rafael — present but not usable

`Trees_points`:

```
https://services5.arcgis.com/sruoiBDPu8SihcGN/arcgis/rest/services/Trees/FeatureServer/0
```

- 22,282 rows, but only **32 distinct `Species_Name` values** and
  **16,139 (72.4%) are `Other-Unknown`**.
- Of the 6,029 that resolve, 91.5% turn — a strong sign of a biased subset
  (the trees that were identified are the showy maples and pistaches).
  Mapping it would paint San Rafael as the most autumnal city on the map on the
  strength of a quarter of its trees.
- Last edit **2025-03-21**. Re-check: if `Other-Unknown` ever drops below
  ~10%, re-run the composition query — the layer is cheap to add.

### Calistoga — no species at all

`Calistoga_Tree_Points` (owner `sdhogan_UCANR`, University of California ANR):

```
https://services.arcgis.com/0xnwbwUttaTjns4i/arcgis/rest/services/Calistoga_Tree_Points/FeatureServer/0
```

588 points; fields are `OBJECTID, Id, gridcode, Shape_Leng, ORIG_FID,
Tree_Number, Tree_ID, Comments`. `gridcode` holds **289 distinct integers**
(probably census-block or parcel ids) and `Comments` is empty on every row.
There is no species field to map. Last edit 2024-05-21.

### St. Helena — gated

`StHelenaTreeInventory2025` is referenced by the public web map *"St.Helena Tree
Inventory 2025"* (owner `pomettam_sonoma`), but the service returns
`Token Required` (`GWM_0003`) on every layer, 0–9:

```
https://services1.arcgis.com/tIgNEsvmQ5Qg6njs/arcgis/rest/services/StHelenaTreeInventory2025/FeatureServer
```

The layer split (Main St., Wappo Park, Stone Bridge Park, Starr Baldwin Park,
…) is visible only through the web map definition. Nothing can be counted, so
it cannot be added and cannot be baselined beyond "still gated, 17 Nov 2026".

### Santa Rosa — a fire survey, not an inventory

The only tree service under the city's account is
`City_of_Santa_Rosa_Fire_Damaged_Tree_Removal_2019_WFL1` (owner
`MStull@srcity.org`): `Fountain Grove Trees` 354 + `Coffee Park Trees` 351 =
**705** hazard assessments after the 2017 fires. Useful context, not a city
inventory.

### Yountville — 11 layers, no readable species

`Yountville_Trees` (owner `myYountville`) has 11 layers (Street Trees, nine
parks, cemetery), **1,209 points** total. Species is written as 3–4 letter
codes — `clo` (coast live oak), `rema` (red maple), `sp` (spruce) — and no code
table ships with the service. Some layers also store the coordinate in
`Latitude`/`Longitude` *attributes* while the geometry extent is broken. Not
addable without a published dictionary.

### Small-town sweep — nothing

Checked by name and by region bbox, 17 Nov 2026:

| Town | Result |
|---|---|
| Novato, Mill Valley, San Anselmo, Sausalito, Tiburon | 0 tree services |
| Sebastopol, Healdsburg, Sonoma, Rohnert Park, Benicia, Fairfield | 0 tree services |
| Corte Madera | only "Christmas Tree Hill Policy Zone" (zoning) |
| Larkspur | only an HOA reserve study |
| Vallejo | only urban-tree-suitability / general-plan layers |
| Vacaville | only growth-area and "Nut Tree Village" planning layers |

Name-only searches confuse this region with others: **Fairfax** hits Fairfax
County, Virginia; **Windsor** hits Windsor, Ontario.

## San Diego County

### The city portal publishes no tree data

`data.sandiego.gov` has 26 occurrences of "tree" in its dataset index and every
one is inside the words "street"/"streets" — Street Sweeping, Streets Repair,
Planned Paving. `https://data.sandiego.gov/api/catalog/v1` and the CKAN
`/api/3/action/package_search` both 404. The portal is not the place to look.

### La Mesa — usable

`Tree Inventory`, owner `GISTech2_lamesaca`:

```
https://services3.arcgis.com/iYP51zxNr6TITn6r/arcgis/rest/services/Tree_Inventory/FeatureServer/4
```

- **13,359 rows**, all with `IsValid = ' Yes'`; 239 distinct `BotanicalName`.
- Usable 9,190 after the standard placeholder filter (`Vacant site` 3,290,
  `Stump` 294, `Stump - not accessible` 5, `Other tree` 3, `No tree at this
  address` 2).
- Best attributes of anything on this list: `CommonName`, `BotanicalName`,
  `DBH`, `Height`, `TreeCondition`, `Address`, `Street`, `Latitude`,
  `Longitude`.
- The item description calls it "the City of La Mesa's official dataset of
  public trees …, more than 13,300 trees and planting sites …, most recent
  update from September 2025"; `dataLastEditDate` is **2025-11-07**.
- **Two data quirks, both harmless:** species names carry a leading space
  (`" Syagrus romanzoffianum"`), and the service's declared extent is garbage
  (`ymin: -14.50`, `xmax: 2.67e-12`) because the geometry is stored in
  state-plane feet. All 13,359 rows carry clean `Latitude`/`Longitude`, and
  13,353 are inside 32.6–32.9 / -117.1..-116.9. The 6 outliers are rows with
  `Latitude = Longitude = 0` — they must be dropped by bbox, which the pipeline
  already does. Point geometry *does* come back correct at `outSR=4326`.
- Turn 16.8% — a palm-heavy city, consistent with Escondido (16%) and
  Encinitas (8%).

### San Diego street trees — three layers, one inventory

A single ArcGIS publisher account (`KateSessions`, an individual account, not a
city account) hosts the city's street-tree data in pieces:

```
RSG     …/Street_Tree_Inventory_for_RSG_WFL1/FeatureServer/0   19,581 rows  turn 12.0%  edit 2026-08-30
D4      …/San_Diego_District_4_Trees/FeatureServer/3          16,553 rows  turn 11.3%  edit 2026-02-08
Encanto …/Encanto_Planning_Area_Tree_Map_WFL1/FeatureServer/4  6,147 rows  turn  8.7%  edit 2026-02-08
(all under https://services3.arcgis.com/DUfavTOaypGm9VbA/arcgis/rest/services/)
```

- **RSG ⊃ D4:** 6,755 of the 19,581 RSG points (34.5%) sit within 2 m of a D4
  point and **100%** of those agree on species. RSG *Existing Street Trees
  2024* is the newer, wider superset; adding both would double-plot a third of
  District 4.
- **Encanto ⊂ D4:** Encanto (6147 rows) is inside District 4's extent.
- If one is taken, take **RSG** (16,732 usable). Its sibling layer `Vacant
  Sites RSG` (9,211 rows) is all planting pits and must not be added.
- Neither layer overlaps the legacy `sdtt` GeoJSON already on the map: only
  0.3–1.0% of RSG points fall within 2–11 m of an `sdtt` point and **0%** agree
  on species. The legacy San Diego export (21,434 trees, `sdtt`) is a different
  vintage — the two would be additive, not duplicates. Read the README note on
  `sdtt` before assuming one supersedes the other; nothing in the repo records
  its original source (it is a legacy `py/run_*.py` import).

### The rest of the county — no per-tree inventories

| City | Finding |
|---|---|
| Oceanside, Carlsbad, El Cajon, San Marcos, Vista, Coronado, National City, Santee, Del Mar | no point inventory found |
| Chula Vista | a StoryMap about tree-less development; no data |
| Poway | `Poway_Tree_Canopy_Distribution_WFL1` — **170,482 canopy polygons** (2014), not trees |
| Solana Beach | `City_of_Solana_Beach_Tree_Benefits_Map_WFL1` layer 1 — **1,166 iTree points**, 87 species, turn 10.0%; a benefits-study sample, not the city inventory. Published under a generic Esri account (`LocalGovDeploy…`), so provenance is unverified too |

## Southern California

### Ventura — usable, official account

`OpenData_AssetsOther_Trees`, owner `SiteAdmin_CityOfVentura`, layer `Trees`:

```
https://services.arcgis.com/dBVj4EXO3IdRPOqb/arcgis/rest/services/OpenData_AssetsOther_Trees/FeatureServer/0
```

- **47,386 rows**, 377 distinct `BOTANICAL`; usable **28,439** after
  placeholders (`Vacant site` 15,872, `Stump` 535, `Other tree` 8,
  `Stump - not accessible` 8, `Unknown` 1).
- Turn 13.9%. Top: California Fan Palm 1,917 · Queen Palm 1,461 · Brush Box
  1,405 · Holly Oak 1,048 · London Plane 961 · Coast Live Oak 882 · Jacaranda
  862.
- Fields: `ADDRESS, STREET, DBH_ACTUAL, CONDITION, DATE, BOTANICAL, COMMON,
  LATITUDE, LONGITUDE, ISVALID, FICTITIOUS`. `maxRecordCount` is 16,000, so
  fetch in paginated batches.
- Licence text: *"This dataset is a product of the City of San Buenaventura,
  California. Although reasonable efforts have been made to ensure its
  accuracy, the City of San Buenaventura cannot guarantee its accuracy."* — no
  explicit redistribution grant, so add the attribution row and treat it like
  the other city GIS terms.
- `dataLastEditDate` **2026-11-17** — a live feed.

**Do not filter on `FICTITIOUS = 'X'`.** 25,546 rows carry it, but the flag
does not mark placeholder records: those rows have real coordinates (all 1,940
sampled were distinct), real DBH, real condition, and `ISVALID = ' Yes'`. It is
an internal West Coast Arborists flag (`SOURCE` is `WCA, Inc.` for all 47,386
rows), and the rows it marks include 19,148 with a real species. Filtering on
it would silently drop half the inventory. 702 points fall outside the city
bbox and are dropped by the bbox rule as usual.

### Anaheim — usable data, unclear licence

`Master_Anaheim_Tree_Inventory`, owner `andpineda`:

```
https://services2.arcgis.com/yrktbS5Xw87hJQvs/arcgis/rest/services/Master_Anaheim_Tree_Inventory/FeatureServer/0
```

- **87,291 rows**, 2,540 distinct `BotanicalName`, usable **61,347** after
  placeholders (`Vacant site` 21,553, `Not City Planted/Maintained` 819,
  `Stump` 412, `Other tree` 58, …). Turn 21.4%.
- Top: Washingtonia robusta 4,455 · Southern Magnolia 4,309 · Crape Myrtle 3,093
  · Canary Island Pine 2,789 · Camphor 2,324.
- `dataLastEditDate` **2026-11-17**.
- **Two blockers.** (a) The item's `licenseInfo` reads *"For municipal tree
  inventory QA/QC, analysis, and operational use."* and `accessInformation`
  names *"West Coast Arborists, Inc."* — that is not a redistribution grant, so
  this needs an explicit check before publishing a derived map. (b) The
  service's declared extent is broken the same way La Mesa's is, but for a
  different reason: **one** of the 87,291 rows sits at (0, 0) and its
  `BotanicalName` is a 200-species concatenation. The other 87,290 points are
  in or immediately around the city. Drop by bbox and ignore the extent.
- Useful for later: `Master_Anaheim_Tree_Inventory_CombinedMultipleInv`
  (2,220 rows) is a duplicate-resolution table, and `…_Invalid_Tree_Inventory`
  holds the rejected records. Neither is a map layer.

### Santa Monica — usable data, unverified publisher

`Santa_Monica_Trees`, owner `LocalGovDeployBrandonA` (a generic Esri account,
not `@smgov.net`):

```
https://services7.arcgis.com/piPfTFmrV9d1DIvN/arcgis/rest/services/Santa_Monica_Trees/FeatureServer/0
```

- **34,992 rows**, 292 distinct `botanicaln`, usable **30,485** (`Vacant site`
  974, `Stump` 12, `Stump - not accessible` 4, `Other tree` 2). Turn 9.1% —
  palms and figs dominate.
- Top: Washingtonia robusta 4,356 · *Ficus microcarpa* 'Nitida' 3,015 ·
  Southern Magnolia 1,986 · Afrocarpus 1,297 · Camphor 1,239.
- Last edit **2024-06-13**.
- **Quirks:** `isvalid` is the string `' Ye'` on every row (truncated "Yes"),
  and `fictitious` is a single space on every row — both status fields are
  useless as filters here.
- **Not a duplicate of Los Angeles.** No Santa Monica point is within 2 m of an
  LA-layer point (median nearest distance 791 m; the LA layer has 0 features
  inside the dense Santa Monica core). The LA bbox reaches the coast but its
  data stops at the city boundary.

### Signal Hill — small but usable

`Street_Trees_public`, owner `cityofsignalhill`:

```
https://services9.arcgis.com/LUBoZWfQwvBnZCmP/arcgis/rest/services/Street_Trees_public/FeatureServer/0
```

- **3,879 rows**, 94 distinct `botanical_name`, usable **2,723** (`Vacant site`
  972, `Stump` 28). Turn 21.6%.
- Last edit **2022-10-13** — the oldest of the addable set, so it is a snapshot.
- Zero LA-layer features share its bbox; it does not double-plot anything.

### Cities checked and found wanting

| City | Result |
|---|---|
| Glendale | 0 tree services |
| Burbank | a `Layer: Burbank Trees` item only (no feature service) |
| Pomona | `PomonaTree` is a collector app with **8 rows**; `pomona_farm_trees` is a farm dataset |
| Ontario | hits are Ontario, **Canada** |
| Santa Barbara | historic-landmark trees StoryMap and CWMP polygons; no inventory |
| Thousand Oaks, Simi Valley | 0 tree services |

### Los Angeles — the colour gradient the guide is about

Recomputed from `data/output/geojson/trees_los_angeles.geojson` (323,510 trees)
on 17 Nov 2026, not quoted from an earlier note:

| Latitude band | Trees | Turn share |
|---|---:|---:|
| < 34.05 (coastal / South LA) | 96,293 | 9.3% |
| 34.05–34.10 | 60,781 | 10.3% |
| 34.10–34.15 | 28,721 | 16.6% |
| 34.15–34.20 | 51,213 | 45.7% |
| 34.20–34.25 | 49,932 | 53.0% |
| > 34.25 (San Fernando Valley) | 36,570 | 44.4% |

The city total is 27% only because the flat, coastal half is almost all palm
and ficus. The north-of-34.15 band (137,715 trees) turns at ~48% — the
strongest single contrast available for a Southern California fall-colour
guide, and it needs no new data.

## Re-checking this baseline

One command per row, in order of how likely things are to change:

```bash
# counts — if any of these moved, the verdict below needs revisiting
url=https://services5.arcgis.com/sruoiBDPu8SihcGN/arcgis/rest/services/Trees/FeatureServer/0
curl -s "$url/query?where=Species_Name%3D%27Other-Unknown%27&returnCountOnly=true&f=json"
# San Rafael becomes usable when this is < ~2,000 of 22,282.

# last data edit — how stale is each addable layer?
for u in <service urls above>; do
  curl -s "$u/FeatureServer/0?f=json" | python3 -c \
    'import json,sys,datetime; d=json.load(sys.stdin); t=d["editingInfo"]["dataLastEditDate"];
     print(d["name"], datetime.datetime.fromtimestamp(t/1000, datetime.UTC).date())'
done

# species composition — compare against the top-5 lists recorded here
curl -s "$url/query?where=1%3D1&groupByFieldsForStatistics=SPECIES_BO&outStatistics=%5B%7B%22statisticType%22%3A%22count%22%2C%22onStatisticField%22%3A%22OBJECTID%22%2C%22outStatisticFieldName%22%3A%22n%22%7D%5D&orderByFields=n+DESC&returnGeometry=false&f=json"
```

Signals that a "not usable" verdict has changed:

- **San Rafael** — `Other-Unknown` share falls below ~10%.
- **Calistoga / Yountville** — a species or species-code field appears in the
  layer's field list.
- **St. Helena** — the service stops returning `GWM_0003` without a token.
- **A new city** — a `title:"tree"` item search in this region's bbox returns a
  feature service that did not appear in the 16–17 Nov 2026 sweep.

## What to decide before adding any of it

1. **Napa / Ventura / Anaheim / Santa Monica / Signal Hill** — provenance and
   licence, in that order of doubt. Napa and Santa Monica are published from
   non-municipal accounts, Ventura is municipal but has no redistribution grant,
   and Anaheim's terms explicitly restrict use to QA/QC and operations.
2. **Petaluma** — label it as a partial survey, and decide whether a surveyed
   subset belongs on a map that otherwise shows municipal registers.
3. **San Diego** — RSG *or* District 4, never both. And decide whether to keep
   the legacy `sdtt` layer alongside a current RSG import; they share no trees.
4. **La Mesa** — the easiest add of the set: official account, official
   description, clean attributes, current data.
