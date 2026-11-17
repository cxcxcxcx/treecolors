# South Bay & Peninsula Tree Data — Coverage, Gaps and Records Requests

Compiled 13 November 2026, revised 16 November 2026 for treecolors.botanisense.app.

## Status

The map now carries **40 municipal inventories and 6,642,191 trees**. Seven Bay Area
layers were added in this round: Santa Clara, Los Gatos, San Mateo, Burlingame,
Brisbane, the Santa Clara County inventory and Sunnyvale. Mountain View and
Milpitas were already live.

All counts below were measured with the ArcGIS `returnCountOnly` query against the
live service on 12–13 November 2026, not copied from a portal description.

## Added in this round (live)

- **Santa Clara, CA — 11,366 trees.** Street Trees plus Parkway Trees from the city's
  Lucity inventory, limited to `StatusCode = 2` ("In Inventory") rows that have a
  species name. The only thing the filter removes is trees marked `999` "Removed",
  which are no longer standing; private trees and trees transferred to the property
  owner stay in. (The status field is the only exclusion: `StatusCode = 5` "Private"
  is just 68 rows, and 1,957 rows with `OwnerCode = 103` "Private" pass the filter and
  are mapped.) No coordinate overlap with the San Jose, Cupertino, Mountain View,
  Palo Alto or county layers. An earlier build dropped 1,700 rows whose species names
  were missing from the resolver's vocabulary — "Flowering Pear", "Liquid Amber",
  "Fruitless Mulberry", "Camphor", "Geijera", "Redwood" and similar — which was a
  knowledge-base gap, not a data-quality one. Adding 23 common-name aliases recovered
  1,674 of them; only three ambiguous names (Laurel, Abelia, Bay Tree, 26 rows) are
  still unresolved.
- **Los Gatos, CA — 11,993 trees.** Town inventory published by Santa Clara County.
- **San Mateo, CA — 22,950 trees.** City street tree inventory; records freeze in
  September 2019, so it is a snapshot rather than a live feed.
- **Burlingame, CA — 16,433 trees.** Rows without a botanical name dropped. Published
  from the city's web map by the account `andpineda`, not an official city account,
  so the attribution is worth confirming before it is cited as authoritative — but
  the data itself checks out: coordinates are at ~1e-6° precision, and 96% of the
  12,853 points shared with the city's separately published November 2026 layer carry
  the same species. Two real caveats: the layer currently on the map has every
  contextual field (address, street, district, condition, land use, DBH) empty — only
  species and geometry survive — and its `Tree_ID` is reordered between versions, so
  it cannot be used to join records across releases. Neither affects the map, which
  plots species and position only. The account publishes a newer, complete-attribute
  layer at `Burlingame_November_Update_WFL1` (16,765 rows, `IsValid` all `Yes`), but
  its underlying data is older (last `DateModified` 2023-08-24, versus 2025-02-10 for
  the layer in use), so switching would trade completeness for freshness and change
  the species label on about 4% of shared points.
- **Brisbane, CA — 4,650 trees.** PlanITGeo inventory; rows with a blank scientific
  name dropped.
- **Santa Clara County, CA — 4,416 trees.** Saratoga, Campbell, Gilroy, Morgan Hill,
  San Martin and unincorporated county only. The county service also republishes
  Palo Alto, San Jose, Sunnyvale, Milpitas and Los Gatos, which are filtered out so
  nothing is counted twice.
- **Sunnyvale, CA — 32,903 trees.** The uncapped export arrived: the city sent a
  spreadsheet (36,866 site records, data edited 2026-11-13) after the records
  request. It supersedes the county's capped 10,000-row copy — 8,662 of those
  SiteIDs still appear, and on 97% of them the species agrees, so the old copy was
  the same inventory truncated, as suspected. Rows whose last work order is
  `STUMP REMOVAL`, `TREE REMOVAL` or `VACANT SITE` (337 records) are dropped: they
  are gone trees or empty pits, the same rule Santa Clara applies to its `999`
  "Removed" rows. 3,615 rows are exact duplicates (same address, DBH, date and
  coordinate) and are removed by the pipeline's dedupe. Sunnyvale now resolves
  **every** species name — the parenthesised-scientific-name parsing problem from
  the county copy does not apply, because the spreadsheet carries the scientific
  name in its own `SPP_bot` field. The file is not redistributable code and is
  kept out of git (`data/raw/`); the workbook adapter reads it from
  `data/raw/sunnyvale_ca/Sunnyvale_street_trees.xlsx`.

## Available but deliberately not added

- **Saratoga heritage trees — 44 trees.** The city's main "Trees" service has had
  0 features since 2023; the county layer's 512 Saratoga trees are already included
  through the county group. The heritage layer is a nice supplement but not a
  street-tree inventory.
- **Mountain View heritage trees.** A separate `MV_Heritage_Trees___For_Upload`
  layer exists in addition to the street tree inventory already live. Optional.
- **Watsonville — 701 records** in the county service, but it is in Santa Cruz
  County and outside this project's South Bay / Peninsula scope.

## Cities with no usable public per-tree inventory

These are the candidates for a public records request. None has a public point-level
tree inventory that could be added today.

- **Millbrae** — the only related ArcGIS Online item, "Millbrae Street Tree &
  Reforestation Program", contains city boundaries and fire-risk parcels; there is
  no tree layer in it.
- **San Bruno** — ArcGIS Online search finds only a Street Lights layer under the
  city's account; no tree layer.
- **Belmont** — the `Belmont_Features_Map_Trees` service is located at 38.32 N,
  77.47 W: Belmont, Virginia, not California. Belmont CA has no published tree data.
- **Los Altos** — public GIS carries parcels and zoning only.
- **Los Altos Hills** — no city-hosted GIS found.
- **Redwood City** — public layers are boundaries and zoning; the 3D layer map
  reports "Service not started".
- **Menlo Park** — the open data portal exists (49 datasets) but has no tree dataset.
- **San Carlos** — no public GIS host found.
- **Foster City** — public GIS has only `Public_Parcels`.
- **Daly City** — public GIS has city limit, addresses, parcels and zoning only.
- **South San Francisco** — 16 datasets on its portal, none of them trees.
- **Pacifica** — no city GIS host found. The "Quercus pacifica" hits are a shrub
  habitat polygon layer, not street trees.
- **Atherton, Woodside, Portola Valley, Half Moon Bay, East Palo Alto** — no
  city-hosted GIS found and no tree inventory found in ArcGIS Online. Woodside
  results are unrelated datasets from other states and countries.
- **Campbell, Gilroy, Morgan Hill** (and San Martin / unincorporated) — no city-level
  tree service, but the county layer's records for these places are already live.
  A direct city inventory would only be worth requesting to get fresher data.

## Contact addresses

Sunnyvale's website is behind a WAF that returns 403 for every path, including
`robots.txt`, with any user agent — so its clerk page could not be read directly.
The address below was recovered from the footer of a current city meeting agenda
published on Legistar (agenda for the Personnel Board, 16 November 2026), which
carries the City Clerk's office contact in English, Spanish and Chinese:

- **Sunnyvale City Clerk** — 456 W. Olive Ave., Sunnyvale, CA 94086 ·
  408-730-7483 · `cityclerk@sunnyvale.ca.gov` (verified 13 Nov 2026)

For every other city on the request list, no address was verified: their sites
returned 403 or timed out and the general web fetcher failed with a 502. The draft
below is written so the address can be filled in from the city's own "Public
Records" or "City Clerk" page. Do not guess an address.

## Email draft — request for a tree inventory

Subject: Public records request — city tree inventory (GIS point data)

Hello [City Clerk / Public Records Officer],

I am writing to request a copy of the city's street and park tree inventory in
electronic form. Specifically:

1. The tree inventory as point locations (shapefile, GeoJSON, CSV with latitude and
   longitude, or a link to the hosted GIS service), including for each tree the
   species or genus, trunk diameter where recorded, and location.
2. If the inventory is maintained in a GIS system, a link to the public or
   agency-accessible REST service would be preferable to a file export.
3. A short note on the date of the last update and the record layout.

I understand this is a request under the California Public Records Act. If the
records exist in an electronic format, I would prefer to receive them
electronically. If part of the request is exempt or would require redaction, please
let me know which part and I will narrow it.

Purpose: the data would be used in a free public map that shows street tree species
and autumn colour across North American cities, with each tree linked back to the
publishing city's own inventory record. The map attributes every city and links to
its source, and does not resell the data. The project is at
https://treecolors.botanisense.app/ and its per-city source list is at
https://treecolors.botanisense.app/DATA_LICENSES.md.

If a tree inventory is not maintained, a note saying so is a complete answer and
would save us both time.

Thank you,
[Name]
[Email] · [Phone]

### Notes for sending

- The CPRA gives the agency 10 days to respond, with a possible 14-day extension.
  It applies to identifiable existing records; an agency does not have to create a
  new dataset, but GIS exports of an existing layer normally qualify.
- Asking for "the hosted REST service link" is usually the fastest path — many
  cities will simply point at a service they already run.
- Send the same email to: Millbrae, San Bruno, Los Altos, Redwood City, Menlo Park,
  San Carlos, Foster City, Daly City, South San Francisco, Pacifica, Belmont,
  Atherton, Woodside, Portola Valley, Half Moon Bay, East Palo Alto, Los Altos Hills.
- **Sunnyvale is the one city with a verified address**:
  `cityclerk@sunnyvale.ca.gov`, 408-730-7483. Use the alternate draft below — the
  ask is the uncapped export of the inventory they already maintain, not a new
  inventory.
- For Campbell, Gilroy and Morgan Hill, the ask is a current city-maintained
  inventory rather than the county's republished copy.

## Email draft — Sunnyvale, uncapped export

To: cityclerk@sunnyvale.ca.gov
Subject: Public records request — complete copy of the Sunnyvale tree inventory

Hello City Clerk,

I am writing to request a copy of the city's tree inventory in electronic form.

I am already working with the copy of "Sunnyvale Trees" that the County of Santa
Clara republishes at
Tree_Inventories_in_Santa_Clara_County_WFL1, feature layer 1. That public copy
contains exactly 10,000 records, has sequential record IDs 1 through 10,000, and
stops at street names beginning with "D" — it looks like a capped export rather
than the full inventory. Its last data edit is dated 11 August 2021.

Could you provide:

1. The complete tree inventory as point locations — a GIS export (file
   geodatabase, shapefile or GeoJSON), a CSV with coordinates, or a link to the
   hosted REST service, whichever is easiest.
2. Per tree: species or genus, trunk diameter where recorded, address or street
   segment, and location.
3. The date of the last update.

If the inventory is managed in a system such as Tree Plotter or TreeKeeper, a
read-only service link is ideal and would avoid an export entirely.

I understand this is a request under the California Public Records Act. The data
would be used in a free public map of street tree species and autumn colour, with
each tree linked back to the city's own inventory record; the map credits every
city and does not resell the data — https://treecolors.botanisense.app/ and
https://treecolors.botanisense.app/DATA_LICENSES.md.

Thank you,
[Name]
[Email] · [Phone]

## Method

Each candidate was checked three ways: the city's own GIS REST endpoint directory,
an ArcGIS Online item search restricted to the city name, and the county service
that republishes several city inventories. Every accepted layer was then counted,
field-inspected, bbox-checked and compared coordinate-by-coordinate against the
layers already on the map to rule out double counting.
