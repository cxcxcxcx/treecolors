# South Bay & Peninsula Tree Data — Coverage, Gaps and Records Requests

Compiled 13 November 2026 for treecolors.botanisense.app.

## Status

The map now carries **39 municipal inventories and 6,607,614 trees**. Six Bay Area
layers were added in this round: Santa Clara, Los Gatos, San Mateo, Burlingame,
Brisbane and the Santa Clara County inventory. Mountain View and Milpitas were
already live.

All counts below were measured with the ArcGIS `returnCountOnly` query against the
live service on 12–13 November 2026, not copied from a portal description.

## Added in this round (live)

- **Santa Clara, CA — 9,692 trees.** Street Trees plus Parkway Trees from the city's
  Lucity inventory, limited to `StatusCode = 2` ("In Inventory") rows that have a
  species name. Removed trees, privately owned trees and trees transferred to the
  property owner are excluded. No coordinate overlap with the San Jose, Cupertino,
  Mountain View, Palo Alto or county layers.
- **Los Gatos, CA — 11,993 trees.** Town inventory published by Santa Clara County.
- **San Mateo, CA — 22,950 trees.** City street tree inventory; records freeze in
  September 2019, so it is a snapshot rather than a live feed.
- **Burlingame, CA — 16,433 trees.** Rows without a botanical name dropped. Published
  from the city's web map by the account `andpineda`, not an official city account —
  the fields (District, address, species) look like genuine city data, but the
  provenance is worth confirming with the city before citing it as authoritative.
- **Brisbane, CA — 4,650 trees.** PlanITGeo inventory; rows with a blank scientific
  name dropped.
- **Santa Clara County, CA — 4,416 trees.** Saratoga, Campbell, Gilroy, Morgan Hill,
  San Martin and unincorporated county only. The county service also republishes
  Palo Alto, San Jose, Sunnyvale, Milpitas and Los Gatos, which are filtered out so
  nothing is counted twice.

## Available but deliberately not added

- **Sunnyvale — truncated export.** The county-hosted "Sunnyvale Trees" layer
  (`Tree_Inventories_in_Santa_Clara_County_WFL1/FeatureServer/1`) returns exactly
  10,000 rows, with OBJECTIDs 1–10000 contiguous and street names running only A–D.
  That is a capped export, not the inventory. Separately, its species field packs the
  common and scientific name into one string, e.g. "NAME (Scientific)", and the name
  cleaner keeps only the common name — only 65 of 167 distinct values resolve to a
  species. Wait for the full export before mapping Sunnyvale.
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

## Caveat on contact addresses

Every city website was checked from this machine and returned 403 or timed out, and
the general web fetcher failed with a 502, so **no city clerk or public records
email address was verified**. The drafts below therefore address the records request
to a role, not to an address. Look the address up on the city's own "Public Records"
or "City Clerk" page before sending; do not guess an address.

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
- For Sunnyvale, skip the inventory request and ask instead for the **uncapped
  export** of the existing "Sunnyvale Trees" layer, since the public copy is capped
  at 10,000 rows.
- For Campbell, Gilroy and Morgan Hill, the ask is a current city-maintained
  inventory rather than the county's republished copy.

## Method

Each candidate was checked three ways: the city's own GIS REST endpoint directory,
an ArcGIS Online item search restricted to the city name, and the county service
that republishes several city inventories. Every accepted layer was then counted,
field-inspected, bbox-checked and compared coordinate-by-coordinate against the
layers already on the map to rule out double counting.
