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
    """One public tree inventory source.

    ``kind`` selects the adapter: ArcGIS REST, Socrata, or CSV.
    """

    slug: str
    name: str
    url: str
    kind: str = "arcgis"  # arcgis | socrata | csv
    where: str = "1=1"
    out_fields: tuple[str, ...] = ()
    # Ordered candidates for the scientific/species name.
    species_fields: tuple[str, ...] = ()
    # Optional concatenation, e.g. Calgary's genus + species.
    species_concat: tuple[str, ...] = ()
    species_separator: str = " "
    common_fields: tuple[str, ...] = ()
    # If set, the ArcGIS coded-value domain turns a common-name code into a
    # scientific name (Montgomery's ITEM field).
    domain_field: str | None = None
    id_field: str = "OBJECTID"
    page_size: int = 2000
    # "Oak, Willow" -> "Willow Oak".
    invert_comma: bool = False
    # "ACER RUBRUM - RED MAPLE" -> "ACER RUBRUM".
    split_dash: bool = False
    # Socrata / CSV coordinate fields.
    lat_field: str | None = None
    lng_field: str | None = None
    # Socrata ``point`` object or CSV JSON geometry column.
    point_field: str | None = None
    delimiter: str = ","
    encoding: str = "utf-8-sig"
    fixed_city: str | None = None
    homepage: str = ""
    notes: str = ""


@dataclass(frozen=True)
class CitySpec:
    slug: str
    name: str
    state: str
    bbox: tuple[float, float, float, float]  # west, south, east, north
    sources: tuple[SourceSpec, ...]
    attribution: str = ""


# --- Existing East Coast coverage ------------------------------------------
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
            where="RETIREDDT IS NULL",
            out_fields=("SCI_NM", "CMMN_NM", "OBJECTID"),
            species_fields=("SCI_NM", "CMMN_NM"),
            common_fields=("CMMN_NM",),
            fixed_city="Washington, DC",
            homepage="https://opendata.dc.gov/datasets/urban-forestry-street-trees",
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
            homepage="https://www.nps.gov/subjects/cherryblossom/index.htm",
        ),
    ),
    attribution="DC Open Data / DDOT UFA; National Park Service",
)

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
            homepage="https://gisdata-arlgis.opendata.arcgis.com/",
        ),
    ),
    attribution="Arlington County GIS Open Data",
)

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
            homepage="https://data.montgomerycountymd.gov/",
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
            homepage="https://montgomeryparks.org/",
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
            homepage="https://www.gaithersburgmd.gov/",
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
            homepage="https://bethesdabid.com/",
        ),
    ),
    attribution=(
        "Montgomery County MCDOT; Montgomery Parks; City of Gaithersburg; "
        "Bethesda Urban Partnership"
    ),
)

BALTIMORE_MD = CitySpec(
    slug="baltimore_md",
    name="Baltimore City, MD",
    state="MD",
    bbox=(-76.75, 39.19, -76.50, 39.38),
    sources=(
        SourceSpec(
            slug="forestry_trees",
            name="Baltimore City Forestry Trees",
            url="https://baltegis.baltimorecity.gov/mapping/rest/services/Forestry/Trees/MapServer/0",
            where="1=1",
            out_fields=("SPP", "OBJECTID"),
            species_fields=("SPP",),
            common_fields=("SPP",),
            fixed_city="Baltimore, MD",
            homepage="https://data.baltimorecity.gov/",
        ),
    ),
    attribution="Baltimore City Open Data / TreeBaltimore",
)

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
            homepage="https://opendataphilly.org/datasets/philadelphia-tree-inventory/",
        ),
    ),
    attribution="City of Philadelphia Open Data / Philadelphia Parks & Recreation",
)

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
            homepage="https://www.rva.gov/public-works/",
        ),
    ),
    attribution="City of Richmond Open Data",
)


# --- Major US metros --------------------------------------------------------
NEW_YORK_NY = CitySpec(
    slug="new_york_ny",
    name="New York City, NY",
    state="NY",
    bbox=(-74.27, 40.49, -73.68, 40.93),
    sources=(
        SourceSpec(
            slug="street_tree_census",
            name="NYC 2015 Street Tree Census",
            url="https://data.cityofnewyork.us/resource/uvpi-gqnh.json",
            kind="socrata",
            where="status = 'Alive'",
            species_fields=("spc_latin", "spc_common"),
            common_fields=("spc_common",),
            lat_field="latitude",
            lng_field="longitude",
            id_field=":id",
            page_size=50000,
            fixed_city="New York, NY",
            homepage=(
                "https://data.cityofnewyork.us/Environment/"
                "2015-Street-Tree-Census-Tree-Data/uvpi-gqnh"
            ),
        ),
    ),
    attribution="NYC Open Data / NYC Parks",
)

BOSTON_MA = CitySpec(
    slug="boston_ma",
    name="Boston, MA",
    state="MA",
    bbox=(-71.20, 42.22, -70.90, 42.40),
    sources=(
        SourceSpec(
            slug="bprd_trees",
            name="Boston BPRD Trees",
            url=(
                "https://services.arcgis.com/sFnw0xNflSi8J0uh/arcgis/rest/services/"
                "BPRD_Trees/FeatureServer/0"
            ),
            where="1=1",
            out_fields=("spp_bot", "spp_com", "OBJECTID"),
            species_fields=("spp_bot", "spp_com"),
            common_fields=("spp_com",),
            lat_field="y_latitude",
            lng_field="x_longitude",
            fixed_city="Boston, MA",
            homepage="https://data.boston.gov/dataset/bprd-trees",
        ),
    ),
    attribution="Analyze Boston / Boston Parks and Recreation",
)

SEATTLE_WA = CitySpec(
    slug="seattle_wa",
    name="Seattle, WA",
    state="WA",
    bbox=(-122.46, 47.49, -122.22, 47.74),
    sources=(
        SourceSpec(
            slug="sdot_trees",
            name="SDOT Trees (Active)",
            url=(
                "https://services.arcgis.com/ZOyb2t4B0UYuYNYH/arcgis/rest/services/"
                "SDOT_Trees_(Active)/FeatureServer/0"
            ),
            where="1=1",
            out_fields=("SCIENTIFIC_NAME", "BOTANICAL_NAME", "OBJECTID"),
            species_fields=("SCIENTIFIC_NAME", "BOTANICAL_NAME"),
            common_fields=("BOTANICAL_NAME",),
            fixed_city="Seattle, WA",
            homepage="https://data.seattle.gov/",
        ),
    ),
    attribution="Seattle Open Data / SDOT",
)

PORTLAND_OR = CitySpec(
    slug="portland_or",
    name="Portland, OR",
    state="OR",
    bbox=(-122.84, 45.43, -122.47, 45.65),
    sources=(
        SourceSpec(
            slug="street_trees",
            name="Portland Street Trees",
            url="https://www.portlandmaps.com/od/rest/services/COP_OpenData_Environment/MapServer/25",
            where="1=1",
            out_fields=("Scientific", "Common", "Species", "OBJECTID"),
            page_size=200,
            species_fields=("Scientific", "Species", "Common"),
            common_fields=("Common",),
            fixed_city="Portland, OR",
            homepage="https://www.portlandmaps.com/bps/",
        ),
    ),
    attribution="Portland Maps / City of Portland",
)

AUSTIN_TX = CitySpec(
    slug="austin_tx",
    name="Austin, TX",
    state="TX",
    bbox=(-97.95, 30.13, -97.35, 30.52),
    sources=(
        SourceSpec(
            slug="tree_inventory",
            name="Austin Tree Inventory",
            url=(
                "https://services.arcgis.com/0L95CJ0VTaxqcmED/arcgis/rest/services/"
                "Tree_Inventory/FeatureServer/0"
            ),
            where="1=1",
            out_fields=("SPECIES", "LATITUDE", "LONGTITUDE", "FID"),
            species_fields=("SPECIES",),
            common_fields=("SPECIES",),
            invert_comma=True,
            lat_field="LATITUDE",
            lng_field="LONGTITUDE",
            id_field="FID",
            fixed_city="Austin, TX",
            homepage="https://data.austintexas.gov/",
        ),
    ),
    attribution="Austin Open Data",
)

DENVER_CO = CitySpec(
    slug="denver_co",
    name="Denver, CO",
    state="CO",
    bbox=(-105.11, 39.61, -104.73, 39.91),
    sources=(
        SourceSpec(
            slug="tree_inventory",
            name="Denver Tree Inventory",
            url="https://data.colorado.gov/resource/wz8h-dap6.json",
            kind="socrata",
            species_fields=("species_botanic", "species_common"),
            common_fields=("species_common",),
            lat_field="y_lat",
            lng_field="x_long",
            point_field="the_geom",
            id_field=":id",
            page_size=50000,
            fixed_city="Denver, CO",
            homepage="https://data.colorado.gov/Natural-Resources/Tree-Inventory-Denver/wz8h-dap6",
        ),
    ),
    attribution="Colorado Information Marketplace / Denver Parks & Recreation",
)


# --- Major Canadian metros --------------------------------------------------
TORONTO_ON = CitySpec(
    slug="toronto_on",
    name="Toronto, ON",
    state="ON",
    bbox=(-79.64, 43.58, -79.12, 43.86),
    sources=(
        SourceSpec(
            slug="street_tree_data",
            name="Toronto Street Tree Data",
            url=(
                "https://ckan0.cf.opendata.inter.prod-toronto.ca/dataset/"
                "6ac4569e-fd37-4cbc-ac63-db3624c5f6a2/resource/"
                "b65cd31d-fabc-4222-83ef-8ddd11295d2b/download/street-tree-data-4326.csv"
            ),
            kind="csv",
            species_fields=("BOTANICAL_NAME",),
            common_fields=("COMMON_NAME",),
            point_field="geometry",
            delimiter=",",
            encoding="utf-8-sig",
            fixed_city="Toronto, ON",
            homepage="https://open.toronto.ca/dataset/street-tree-data/",
        ),
    ),
    attribution="City of Toronto Open Data",
)

MONTREAL_QC = CitySpec(
    slug="montreal_qc",
    name="Montreal, QC",
    state="QC",
    bbox=(-73.98, 45.40, -73.47, 45.70),
    sources=(
        SourceSpec(
            slug="arbres_publics",
            name="Montreal Public Trees",
            url=(
                "https://donnees.montreal.ca/dataset/"
                "b89fd27d-4b49-461b-8e54-fa2b34a628c4/resource/"
                "64e28fe6-ef37-437a-972d-d1d3f1f7d891/download/arbres-publics.csv"
            ),
            kind="csv",
            species_fields=("Essence_latin",),
            common_fields=("Essence_ang", "Essence_fr"),
            lat_field="Latitude",
            lng_field="Longitude",
            delimiter=",",
            encoding="utf-8-sig",
            fixed_city="Montreal, QC",
            homepage="https://donnees.montreal.ca/dataset/arbres",
        ),
    ),
    attribution="Ville de Montréal Open Data (CC BY 4.0)",
)

OTTAWA_ON = CitySpec(
    slug="ottawa_on",
    name="Ottawa, ON",
    state="ON",
    bbox=(-76.00, 45.10, -75.40, 45.60),
    sources=(
        SourceSpec(
            slug="tree_inventory",
            name="Ottawa Tree Inventory",
            url="https://maps.ottawa.ca/arcgis/rest/services/Forestry/MapServer/0",
            where="1=1",
            out_fields=("SPECIES", "OBJECTID"),
            page_size=1000,
            species_fields=("SPECIES",),
            domain_field="SPECIES",
            common_fields=("SPECIES",),
            fixed_city="Ottawa, ON",
            homepage="https://open.ottawa.ca/",
        ),
    ),
    attribution="City of Ottawa Open Data",
)

CALGARY_AB = CitySpec(
    slug="calgary_ab",
    name="Calgary, AB",
    state="AB",
    bbox=(-114.35, 50.80, -113.80, 51.20),
    sources=(
        SourceSpec(
            slug="public_trees",
            name="Calgary Public Trees",
            url="https://data.calgary.ca/resource/tfs4-3wwa.json",
            kind="socrata",
            species_concat=("genus", "species"),
            common_fields=("common_name",),
            point_field="point",
            id_field=":id",
            page_size=50000,
            fixed_city="Calgary, AB",
            homepage="https://data.calgary.ca/Environment/Public-Trees/tfs4-3wwa",
        ),
    ),
    attribution="City of Calgary Open Data",
)

EDMONTON_AB = CitySpec(
    slug="edmonton_ab",
    name="Edmonton, AB",
    state="AB",
    bbox=(-113.72, 53.40, -113.30, 53.72),
    sources=(
        SourceSpec(
            slug="trees",
            name="Edmonton Trees",
            url="https://data.edmonton.ca/resource/eecg-fc54.json",
            kind="socrata",
            species_fields=("species_botanical", "species"),
            common_fields=("species",),
            lat_field="latitude",
            lng_field="longitude",
            id_field=":id",
            page_size=50000,
            fixed_city="Edmonton, AB",
            homepage="https://data.edmonton.ca/Environmental-Services/Trees/eecg-fc54",
        ),
    ),
    attribution="City of Edmonton Open Data",
)

WINNIPEG_MB = CitySpec(
    slug="winnipeg_mb",
    name="Winnipeg, MB",
    state="MB",
    bbox=(-97.35, 49.70, -96.95, 49.98),
    sources=(
        SourceSpec(
            slug="tree_inventory",
            name="Winnipeg Tree Inventory",
            url="https://data.winnipeg.ca/resource/hfwk-jp4h.json",
            kind="socrata",
            species_fields=("botanical_name", "common_name"),
            common_fields=("common_name",),
            point_field="point",
            id_field=":id",
            page_size=50000,
            fixed_city="Winnipeg, MB",
            homepage="https://data.winnipeg.ca/",
        ),
    ),
    attribution="City of Winnipeg Open Data",
)

MISSISSAUGA_ON = CitySpec(
    slug="mississauga_on",
    name="Mississauga, ON",
    state="ON",
    bbox=(-79.85, 43.45, -79.53, 43.75),
    sources=(
        SourceSpec(
            slug="city_owned_trees",
            name="Mississauga City Owned Tree Inventory",
            url=(
                "https://services6.arcgis.com/hM5ymMLbxIyWTjn2/arcgis/rest/services/"
                "2023_City_Owned_Tree_Inventory/FeatureServer/0"
            ),
            where="1=1",
            out_fields=("BOTNAME", "BOTDESC", "LATITUDE", "LONGITUDE", "OBJECTID"),
            species_fields=("BOTNAME", "BOTDESC"),
            common_fields=("BOTDESC",),
            lat_field="LATITUDE",
            lng_field="LONGITUDE",
            fixed_city="Mississauga, ON",
            homepage="https://data.mississauga.ca/",
        ),
    ),
    attribution="City of Mississauga Open Data",
)

HAMILTON_ON = CitySpec(
    slug="hamilton_on",
    name="Hamilton, ON",
    state="ON",
    bbox=(-80.25, 43.04, -79.61, 43.47),
    sources=(
        SourceSpec(
            slug="public_tree_inventory",
            name="Hamilton Public Tree Inventory",
            url=(
                "https://services.arcgis.com/rYz782eMbySr2srL/arcgis/rest/services/"
                "Public_Tree_Inventory/FeatureServer/0"
            ),
            where="1=1",
            out_fields=("SPECIES_SCIENTIFIC", "SPECIES_COMMON", "OBJECTID"),
            species_fields=("SPECIES_SCIENTIFIC", "SPECIES_COMMON"),
            common_fields=("SPECIES_COMMON",),
            fixed_city="Hamilton, ON",
            homepage="https://open.hamilton.ca/",
        ),
    ),
    attribution="City of Hamilton Open Data",
)

MOUNTAIN_VIEW_CA = CitySpec(
    slug="mountain_view_ca",
    name="Mountain View, CA",
    state="CA",
    bbox=(-122.13, 37.34, -121.99, 37.45),
    sources=(
        SourceSpec(
            slug="city_trees",
            name="City of Mountain View Tree Inventory",
            url="https://maps.mountainview.gov/arcgis/rest/services/Public/Trees/MapServer/0",
            # ~5.1k rows are empty planting pits with no species; they are not trees.
            where="TREEGROUP <> 'Vacant'",
            out_fields=("SPECIES", "NAME", "TREEGROUP", "HERITAGE", "OBJECTID"),
            species_fields=("SPECIES",),
            common_fields=("NAME",),
            fixed_city="Mountain View, CA",
            homepage="https://www.mountainview.gov/",
        ),
    ),
    attribution="City of Mountain View GIS",
)


MILPITAS_CA = CitySpec(
    slug="milpitas_ca",
    name="Milpitas, CA",
    state="CA",
    bbox=(-122.05, 37.36, -121.75, 37.50),
    sources=(
        SourceSpec(
            slug="city_trees",
            name="City of Milpitas Street Tree Inventory",
            url=(
                "https://services8.arcgis.com/OPmRdssd8jj0bT5H/arcgis/rest/services/"
                "Trees/FeatureServer/0"
            ),
            where="1=1",
            out_fields=("Species", "Name", "FACILITYID", "CONDITION", "OBJECTID"),
            species_fields=("Species",),
            common_fields=("Name",),
            fixed_city="Milpitas, CA",
            homepage="https://www.ci.milpitas.ca.gov/",
        ),
    ),
    attribution="City of Milpitas GIS",
)


CITIES: tuple[CitySpec, ...] = (
    WASHINGTON_DC,
    ARLINGTON_VA,
    MONTGOMERY_MD,
    BALTIMORE_MD,
    PHILADELPHIA_PA,
    RICHMOND_VA,
    NEW_YORK_NY,
    BOSTON_MA,
    SEATTLE_WA,
    PORTLAND_OR,
    AUSTIN_TX,
    DENVER_CO,
    TORONTO_ON,
    MONTREAL_QC,
    OTTAWA_ON,
    CALGARY_AB,
    EDMONTON_AB,
    WINNIPEG_MB,
    MISSISSAUGA_ON,
    HAMILTON_ON,
    MOUNTAIN_VIEW_CA,
    MILPITAS_CA,
)

CITY_BY_SLUG = {city.slug: city for city in CITIES}


def get_city(slug: str) -> CitySpec:
    try:
        return CITY_BY_SLUG[slug]
    except KeyError as exc:
        raise SystemExit(
            f"Unknown city {slug!r}. Available: {', '.join(sorted(CITY_BY_SLUG))}"
        ) from exc
