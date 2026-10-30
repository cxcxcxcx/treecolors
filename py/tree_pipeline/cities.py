"""Registry of city-level tree inventories.

Each city has one or more sources.  Sources are fetched independently and then
merged/deduplicated by the processing step.  ``fixed_city`` lets one city group
contain city-level supplements (for example Gaithersburg and Bethesda inside the
Montgomery County group) while keeping a useful label in the tiles.

Adding a city is deliberately data-only: add a ``CitySpec`` below and run the
pipeline.  No changes to the tiling or frontend code are required.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceSpec:
    """One ArcGIS REST tree layer (or another future adapter)."""

    slug: str
    name: str
    url: str
    where: str = "1=1"
    out_fields: tuple[str, ...] = ()
    # Ordered candidates for the scientific/species name.  The first non-empty
    # value wins; later fields are fallbacks.
    species_fields: tuple[str, ...] = ()
    common_fields: tuple[str, ...] = ()
    # If set, the layer's coded-value domain is used to turn a common-name code
    # into a scientific name.  This is how Montgomery's ITEM field works.
    domain_field: str | None = None
    id_field: str = "OBJECTID"
    page_size: int = 2000
    # "Oak, Willow" -> "Willow Oak" for Arlington-style common names.
    invert_comma: bool = False
    # "ACER RUBRUM - RED MAPLE" -> "ACER RUBRUM" for Philadelphia.
    split_dash: bool = False
    fixed_city: str | None = None
    notes: str = ""


@dataclass(frozen=True)
class CitySpec:
    slug: str
    name: str
    state: str
    bbox: tuple[float, float, float, float]  # west, south, east, north
    sources: tuple[SourceSpec, ...]
    attribution: str = ""


# --- Washington, DC ---------------------------------------------------------
# DDOT UFA street trees are the authoritative public street-tree inventory.
# NPS Tidal Basin cherry trees are federal trees and do not overlap UFA.
WASHINGTON_DC = CitySpec(
    slug="washington_dc",
    name="Washington, DC",
    state="DC",
    bbox=(-77.12, 38.78, -76.90, 39.00),
    sources=(
        SourceSpec(
            slug="ufa_street_trees",
            name="DDOT Urban Forestry Street Trees",
            url="https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Urban_Tree_Canopy/MapServer/23",
            # Keep the server-side filter simple: some city WAFs reject
            # multi-clause SQL with IS NOT NULL / empty-string comparisons.
            # Placeholder names are filtered in Python by the species resolver.
            where="RETIREDDT IS NULL",
            out_fields=("SCI_NM", "CMMN_NM", "OBJECTID"),
            species_fields=("SCI_NM", "CMMN_NM"),
            common_fields=("CMMN_NM",),
            fixed_city="Washington, DC",
            notes="223k rows total; retired trees and placeholder names filtered.",
        ),
        SourceSpec(
            slug="nps_cherry_trees",
            name="NPS Tidal Basin Cherry Trees 2021",
            url=(
                "https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/"
                "T2021_CherryTree_Selection/FeatureServer/0"
            ),
            out_fields=("SCI_NM", "CMMN_NM", "OBJECTID"),
            species_fields=("SCI_NM", "CMMN_NM"),
            common_fields=("CMMN_NM",),
            fixed_city="Washington, DC",
            notes="3.75k federal cherry trees around the Tidal Basin/National Mall.",
        ),
    ),
    attribution="DC Open Data / DDOT UFA; National Park Service",
)


# --- Arlington County, VA ---------------------------------------------------
# County inventory, treated as a city-equivalent area.  No scientific-name
# column or domain exists, so the species resolver uses common-name aliases.
ARLINGTON_VA = CitySpec(
    slug="arlington_va",
    name="Arlington County, VA",
    state="VA",
    bbox=(-77.18, 38.82, -77.03, 38.94),
    sources=(
        SourceSpec(
            slug="dpr_trees",
            name="Arlington County DPR Trees",
            url=(
                "https://arlgis.arlingtonva.us/arcgis/rest/services/Open_Data/"
                "od_DPR_Tree_Points/FeatureServer/0"
            ),
            where="1=1",
            out_fields=("CommonName", "OBJECTID"),
            species_fields=("CommonName",),
            common_fields=("CommonName",),
            invert_comma=True,
            fixed_city="Arlington, VA",
            notes="Common names only; reverse alias lookup is used.",
        ),
    ),
    attribution="Arlington County GIS Open Data",
)


# --- Montgomery County, MD --------------------------------------------------
# MCDOT street trees + Montgomery Parks + city-level supplements for
# Gaithersburg and downtown Bethesda.  All four are merged and deduplicated.
MONTGOMERY_MD = CitySpec(
    slug="montgomery_md",
    name="Montgomery County, MD",
    state="MD",
    bbox=(-77.55, 38.92, -76.90, 39.36),
    sources=(
        SourceSpec(
            slug="mcdot_street_trees",
            name="MCDOT Tree Inventory",
            url=(
                "https://www7.montgomerycountymd.gov/arcgis/rest/services/DOT/"
                "MCDOT_Tree_Inventory_maponly/MapServer/0"
            ),
            where="STATUS = 'Plant'",
            out_fields=("ITEM", "STATUS", "OBJECTID"),
            species_fields=("ITEM",),
            common_fields=("ITEM",),
            domain_field="ITEM",
            fixed_city="Montgomery County, MD",
            notes=(
                "ITEM is a common-name code; the field domain's 'name' value is "
                "'Scientific,Common', so the domain supplies the scientific name."
            ),
        ),
        SourceSpec(
            slug="parks_trees",
            name="Montgomery Parks Tree Inventory",
            url=(
                "https://montgomeryplans.org/server/rest/services/Arboriculture/"
                "TreeInventory_Pt/FeatureServer/0"
            ),
            where="1=1",
            out_fields=("SPP_BOT", "SPP_COM", "PARK_NAME", "OBJECTID"),
            species_fields=("SPP_BOT", "SPP_COM"),
            common_fields=("SPP_COM",),
            fixed_city="Montgomery County, MD",
            notes="33.5k park trees with botanical names.",
        ),
        SourceSpec(
            slug="gaithersburg_street_trees",
            name="Gaithersburg Street Trees",
            url=(
                "https://services1.arcgis.com/oYaMaMY9WlGtyT0U/arcgis/rest/services/"
                "Street_Trees_View/FeatureServer/0"
            ),
            where="1=1",
            out_fields=("Botanical_Name", "Common_Name", "OBJECTID"),
            species_fields=("Botanical_Name", "Common_Name"),
            common_fields=("Common_Name",),
            fixed_city="Gaithersburg, MD",
            notes="City-level supplement: 11.5k city-maintained street trees.",
        ),
        SourceSpec(
            slug="bethesda_bup_trees",
            name="Bethesda Urban Partnership Trees",
            url=(
                "https://services.arcgis.com/51pWQ4aVcZ9RRv2f/arcgis/rest/services/"
                "Map1_WFL1/FeatureServer/0"
            ),
            where="1=1",
            out_fields=("Species", "TREEID", "OBJECTID"),
            species_fields=("Species",),
            common_fields=("Species",),
            fixed_city="Bethesda, MD",
            notes="Downtown Bethesda BID inventory: 1.4k trees.",
        ),
    ),
    attribution=(
        "Montgomery County MCDOT; Montgomery Parks; City of Gaithersburg; "
        "Bethesda Urban Partnership"
    ),
)


# --- Baltimore City, MD -----------------------------------------------------
BALTIMORE_MD = CitySpec(
    slug="baltimore_md",
    name="Baltimore City, MD",
    state="MD",
    bbox=(-76.75, 39.19, -76.50, 39.38),
    sources=(
        SourceSpec(
            slug="forestry_trees",
            name="Baltimore City Forestry Trees",
            url=(
                "https://baltegis.baltimorecity.gov/mapping/rest/services/"
                "Forestry/Trees/MapServer/0"
            ),
            where="1=1",
            out_fields=("SPP", "OBJECTID"),
            species_fields=("SPP",),
            common_fields=("SPP",),
            fixed_city="Baltimore, MD",
            notes="193k rows total; vacant sites/stumps filtered to ~113k trees.",
        ),
    ),
    attribution="Baltimore City Open Data / TreeBaltimore",
)


# --- Philadelphia, PA -------------------------------------------------------
PHILADELPHIA_PA = CitySpec(
    slug="philadelphia_pa",
    name="Philadelphia, PA",
    state="PA",
    bbox=(-75.30, 39.86, -74.95, 40.15),
    sources=(
        SourceSpec(
            slug="ppr_tree_inventory",
            name="Philadelphia Parks & Recreation Tree Inventory 2023",
            url=(
                "https://services.arcgis.com/fLeGjb7u4uXqeF9q/arcgis/rest/services/"
                "ppr_tree_inventory_2023/FeatureServer/0"
            ),
            where="1=1",
            out_fields=("tree_name", "OBJECTID"),
            species_fields=("tree_name",),
            common_fields=("tree_name",),
            split_dash=True,
            fixed_city="Philadelphia, PA",
            notes="tree_name is 'SCIENTIFIC - COMMON'; first part is used.",
        ),
    ),
    attribution="City of Philadelphia Open Data / Philadelphia Parks & Recreation",
)


# --- Richmond, VA -----------------------------------------------------------
# Closer to DC than Philadelphia and has a clean citywide inventory.
RICHMOND_VA = CitySpec(
    slug="richmond_va",
    name="Richmond, VA",
    state="VA",
    bbox=(-77.62, 37.43, -77.38, 37.62),
    sources=(
        SourceSpec(
            slug="tree_inventory",
            name="Richmond Tree Inventory",
            url=(
                "https://services1.arcgis.com/k3vhq11XkBNeeOfM/arcgis/rest/services/"
                "Tree_Inventory_Public_View/FeatureServer/0"
            ),
            where="1=1",
            out_fields=("SPP", "OBJECTID"),
            species_fields=("SPP",),
            common_fields=("SPP",),
            fixed_city="Richmond, VA",
            notes="122k rows total; vacant sites/stumps filtered to ~65k trees.",
        ),
    ),
    attribution="City of Richmond Open Data",
)


CITIES: tuple[CitySpec, ...] = (
    WASHINGTON_DC,
    ARLINGTON_VA,
    MONTGOMERY_MD,
    BALTIMORE_MD,
    PHILADELPHIA_PA,
    RICHMOND_VA,
)

CITY_BY_SLUG = {city.slug: city for city in CITIES}


def get_city(slug: str) -> CitySpec:
    try:
        return CITY_BY_SLUG[slug]
    except KeyError as exc:
        raise SystemExit(
            f"Unknown city {slug!r}. Available: {', '.join(sorted(CITY_BY_SLUG))}"
        ) from exc
