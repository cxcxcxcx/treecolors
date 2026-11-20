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

    ``kind`` selects the adapter: ArcGIS REST, Socrata, CSV, or ``workbook``
    (a locally supplied .xlsx, see ``_fetch_workbook``).
    """

    slug: str
    name: str
    url: str
    kind: str = "arcgis"  # arcgis | socrata | csv | workbook
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
    # ``kind="workbook"`` only: sheet name (first sheet if None).
    sheet: str | None = None
    # ``kind="workbook"`` only: drop rows whose value in ``column`` is in this
    # set.  Used for records that are no longer standing trees.
    drop_values: tuple[tuple[str, tuple[str, ...]], ...] = ()
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


LOS_GATOS_CA = CitySpec(
    slug="los_gatos_ca",
    name="Los Gatos, CA",
    state="CA",
    bbox=(-122.00, 37.21, -121.91, 37.27),
    sources=(
        SourceSpec(
            slug="tree_inventory",
            name="Town of Los Gatos Tree Inventory",
            url=(
                "https://services.arcgis.com/NkcnS0qk4w2wasOJ/arcgis/rest/services/"
                "Los_Gatos_Tree_Inventory/FeatureServer/0"
            ),
            where="1=1",
            out_fields=("Botanical", "Common", "Height", "DBH", "OBJECTID"),
            # ~2k rows (vacant sites, stumps) have no Botanical value; fall back
            # to the common name so the resolver can still classify them.
            species_fields=("Botanical", "Common"),
            common_fields=("Common",),
            fixed_city="Los Gatos, CA",
            homepage="https://www.losgatosca.gov/",
        ),
    ),
    attribution="Town of Los Gatos / Santa Clara County GIS",
)


SAN_MATEO_CA = CitySpec(
    slug="san_mateo_ca",
    name="San Mateo, CA",
    state="CA",
    bbox=(-122.36, 37.51, -122.27, 37.59),
    sources=(
        SourceSpec(
            slug="street_trees",
            name="City of San Mateo Street Tree Inventory",
            url=(
                "https://services2.arcgis.com/g26Y0m7OCdjU0ObA/arcgis/rest/services/"
                "Street_Trees/FeatureServer/0"
            ),
            where="1=1",
            out_fields=("SPP", "ADDRESS", "STREET", "DBH", "OBJECTID"),
            species_fields=("SPP",),
            fixed_city="San Mateo, CA",
            homepage="https://www.cityofsanmateo.org/",
        ),
    ),
    attribution="City of San Mateo Public Works GIS",
)


BURLINGAME_CA = CitySpec(
    slug="burlingame_ca",
    name="Burlingame, CA",
    state="CA",
    bbox=(-122.41, 37.56, -122.33, 37.61),
    sources=(
        SourceSpec(
            slug="tree_sites",
            name="City of Burlingame Tree Inventory",
            url=(
                "https://services2.arcgis.com/yrktbS5Xw87hJQvs/arcgis/rest/services/"
                "WebMap_Burlingame_AllLayers_WFL1/FeatureServer/0"
            ),
            where="BotanicalName IS NOT NULL AND BotanicalName <> ''",
            out_fields=(
                "BotanicalName",
                "CommonName",
                "DBH",
                "Address",
                "Street",
                "OBJECTID_1",
            ),
            species_fields=("BotanicalName",),
            common_fields=("CommonName",),
            id_field="OBJECTID_1",
            fixed_city="Burlingame, CA",
            homepage="https://www.burlingame.org/",
        ),
    ),
    attribution="City of Burlingame GIS",
)


SANTA_CLARA_COUNTY_CA = CitySpec(
    slug="santa_clara_county_ca",
    name="Santa Clara County, CA",
    state="CA",
    # Unincorporated county plus the smaller foothill towns; the big cities
    # in this layer are already covered by their own inventories and are
    # filtered out in ``where`` so nothing is counted twice.
    bbox=(-122.15, 37.00, -121.51, 37.44),
    sources=(
        SourceSpec(
            slug="county_trees",
            name="Santa Clara County Tree Inventories",
            url=(
                "https://services.arcgis.com/NkcnS0qk4w2wasOJ/arcgis/rest/services/"
                "Tree_Inventories_in_Santa_Clara_County_WFL1/FeatureServer/0"
            ),
            where=(
                "City IN ('Saratoga','Campbell','Gilroy','Morgan Hill',"
                "'San Martin','Unincorporated','Unassigned')"
            ),
            out_fields=(
                "Scientific",
                "CommonName",
                "City",
                "DBH",
                "FID",
            ),
            species_fields=("Scientific", "CommonName"),
            common_fields=("CommonName",),
            id_field="FID",
            fixed_city="Santa Clara County, CA",
            homepage="https://www.sccgov.org/",
        ),
    ),
    attribution="County of Santa Clara Parks and Recreation GIS",
)


BRISBANE_CA = CitySpec(
    slug="brisbane_ca",
    name="Brisbane, CA",
    state="CA",
    bbox=(-122.43, 37.67, -122.38, 37.71),
    sources=(
        SourceSpec(
            slug="city_trees",
            name="City of Brisbane Tree Inventory",
            url=(
                "https://services9.arcgis.com/UGpGSV1ugL0pHSgX/arcgis/rest/services/"
                "Trees_PlanITGeo/FeatureServer/0"
            ),
            where="Scientific <> ' '",
            out_fields=(
                "Scientific",
                "CommonName",
                "DBH",
                "Address",
                "Status",
                "FID",
            ),
            species_fields=("Scientific",),
            common_fields=("CommonName",),
            id_field="FID",
            fixed_city="Brisbane, CA",
            homepage="https://www.brisbaneca.org/",
        ),
    ),
    attribution="City of Brisbane GIS (PlanITGeo inventory)",
)


SANTA_CLARA_CA = CitySpec(
    slug="santa_clara_ca",
    name="Santa Clara, CA",
    state="CA",
    bbox=(-122.03, 37.31, -121.92, 37.42),
    sources=(
        SourceSpec(
            slug="street_trees",
            name="City of Santa Clara Street Trees",
            url=(
                "https://map.santaclaraca.gov/maps/rest/services/Lucity/"
                "StreetTrees/FeatureServer/0"
            ),
            # StatusCode 2 = "In Inventory"; 999 is removed, 5 is a private
            # tree, 3 is transferred to the property owner.  Rows with no
            # species are planting sites rather than trees.
            where="StatusCode = 2 AND SpeciesName IS NOT NULL AND SpeciesName <> ''",
            out_fields=(
                "SpeciesName",
                "DBH",
                "Height",
                "AddressID",
                "OBJECTID",
            ),
            species_fields=("SpeciesName",),
            fixed_city="Santa Clara, CA",
            homepage="https://www.santaclaraca.gov/",
        ),
        SourceSpec(
            slug="parkway_trees",
            name="City of Santa Clara Parkway Trees",
            url=(
                "https://map.santaclaraca.gov/maps/rest/services/Lucity/"
                "ParkwayTrees/FeatureServer/0"
            ),
            where="StatusCode = 2 AND SpeciesName IS NOT NULL AND SpeciesName <> ''",
            out_fields=("SpeciesName", "DBH", "Height", "OBJECTID"),
            species_fields=("SpeciesName",),
            fixed_city="Santa Clara, CA",
            homepage="https://www.santaclaraca.gov/",
        ),
    ),
    attribution="City of Santa Clara GIS (Lucity inventory)",
)


SUNNYVALE_CA = CitySpec(
    slug="sunnyvale_ca",
    name="Sunnyvale, CA",
    state="CA",
    bbox=(-122.10, 37.31, -121.96, 37.44),
    sources=(
        SourceSpec(
            slug="street_trees",
            name="City of Sunnyvale Street Tree Inventory",
            # City-supplied export (records request, November 2026): 36,866
            # Sites, far past the county's capped 10,000-row copy, with data
            # last edited 2026-11-13.  Placed by hand under data/raw/.
            url="data/raw/sunnyvale_ca/Sunnyvale_street_trees.xlsx",
            kind="workbook",
            sheet="sql_statement",
            # ``MT`` is the last work order on the site.  "STUMP REMOVAL" and
            # "TREE REMOVAL" records are trees that are gone (notes confirm:
            # "Tree was removed"), and "VACANT SITE" is an empty planting pit.
            # Keeping them would put stumps on the map as if they were trees;
            # Santa Clara drops its ``999`` "Removed" rows for the same reason.
            drop_values=(("MT", ("STUMP REMOVAL", "TREE REMOVAL", "VACANT SITE")),),
            species_fields=("SPP_bot",),
            common_fields=("SPP_com",),
            lat_field="latitude",
            lng_field="longitude",
            id_field="uniqueid",
            fixed_city="Sunnyvale, CA",
            homepage="https://sunnyvale.ca.gov/",
        ),
    ),
    attribution="City of Sunnyvale Public Works (supplied by records request, Nov 2026)",
)


ATHERTON_CA = CitySpec(
    slug="atherton_ca",
    name="Atherton, CA",
    state="CA",
    bbox=(-122.24, 37.43, -122.16, 37.48),
    sources=(
        SourceSpec(
            slug="town_trees",
            name="Town of Atherton Tree Inventory 2026",
            # Town-supplied West Coast Arborists export (Public Records Act
            # request PRA 2026-188, November 2026): 1,444 rows, town-maintained
            # trees only — Holbrook-Palmer Park, medians and town frontages.
            # Atherton's residential street trees are private and not in it.
            # Placed by hand under data/raw/.
            url="data/raw/atherton_ca/PRA 2026-188 Record.xlsx",
            kind="workbook",
            # ``Recommended`` is WCA's next action for the site.  "Plant" rows
            # are empty sites carrying the species proposed for them (17 of 28
            # have no DBH at all), and "Removal-Stump" is a stump.  Do not
            # filter on ``Fictitious``: as in Ventura it is a WCA flag that 97%
            # of real trees carry.
            drop_values=(("Recommended", ("Plant", "Removal-Stump")),),
            species_fields=("BotanicalName", "CommonName"),
            common_fields=("CommonName",),
            lat_field="Latitude",
            lng_field="Longitude",
            id_field="InventoryID",
            fixed_city="Atherton, CA",
            homepage="https://www.ci.atherton.ca.us/",
            notes=("One Gambel oak in Holbrook-Palmer Park (InventoryID 12203793) "
                   "is split over three spreadsheet rows by a stray quote and has "
                   "no usable coordinates, so it is not mapped."),
        ),
    ),
    attribution="Town of Atherton Public Works (supplied by records request, Nov 2026)",
)


OAKLAND_CA = CitySpec(
    slug="oakland_ca",
    name="Oakland, CA",
    state="CA",
    bbox=(-122.36, 37.69, -122.11, 37.91),
    sources=(
        SourceSpec(
            slug="trees_along_sidewalks",
            name="City of Oakland Trees Along Sidewalks",
            # The older "Oakland Street Trees" exports (sv45-t3gc, 4jcx-enxf,
            # whu4-i6pg) all carry the same placeholder coordinate for every
            # row, so they cannot be mapped.  This survey has real geometry.
            url="https://data.oaklandca.gov/resource/svwc-9r23.json",
            kind="socrata",
            # ``tree`` is -1 for a standing tree and 0 for an empty planting
            # site; ``stump``/``dead`` are -1 for yes.  "Tree well only" rows
            # are pits with no tree.
            where=(
                "species NOT IN ('Unknown','Tree well only') "
                "AND dead='0' AND stump='0' AND tree='-1'"
            ),
            species_fields=("species",),
            point_field="the_geom",
            id_field="objectid",
            fixed_city="Oakland, CA",
            homepage="https://data.oaklandca.gov/dataset/TreesAlongSidewalks/svwc-9r23",
            notes=(
                "2006 sidewalk-tree survey: the city has not published a newer "
                "point-level inventory.  Locations are approximate for trees "
                "planted or removed since then."
            ),
        ),
    ),
    attribution="City of Oakland Open Data (Trees Along Sidewalks survey)",
)


PASADENA_CA = CitySpec(
    slug="pasadena_ca",
    name="Pasadena, CA",
    state="CA",
    bbox=(-118.19, 34.11, -118.06, 34.21),
    sources=(
        SourceSpec(
            slug="street_row_trees",
            name="City of Pasadena Street ROW Trees",
            url=(
                "https://services2.arcgis.com/zNjnZafDYCAJAbN0/arcgis/rest/services/"
                "Street_ROW_Trees/FeatureServer/0"
            ),
            where="Status_Text = 'Active'",
            out_fields=("Genus", "Species", "Common_Name", "OBJECTID"),
            # The inventory splits the binomial: Genus="ULMUS",
            # Species="PARVIFOLIA".  A blank Species leaves the genus alone,
            # which the resolver treats as a genus-level name.
            species_concat=("Genus", "Species"),
            common_fields=("Common_Name",),
            fixed_city="Pasadena, CA",
            homepage="https://www.cityofpasadena.net/",
        ),
    ),
    attribution="City of Pasadena GIS",
)


RIVERSIDE_CA = CitySpec(
    slug="riverside_ca",
    name="Riverside, CA",
    state="CA",
    bbox=(-117.52, 33.87, -117.27, 34.03),
    sources=(
        SourceSpec(
            slug="street_trees",
            name="City of Riverside Street Trees",
            url=(
                "https://services.arcgis.com/Fu2oOWg1Aw7azh41/arcgis/rest/services/"
                "Street_Trees/FeatureServer/0"
            ),
            where="BotanicalName <> 'Vacant site'",
            out_fields=("BotanicalName", "CommonName", "OBJECTID"),
            species_fields=("BotanicalName",),
            common_fields=("CommonName",),
            fixed_city="Riverside, CA",
            homepage="https://riversideca.gov/publicworks/",
            notes=(
                "One row per planting site.  The TreeCount column aggregates "
                "several trees at a site and is not used as a tree count."
            ),
        ),
    ),
    attribution="City of Riverside GIS",
)


REDLANDS_CA = CitySpec(
    slug="redlands_ca",
    name="Redlands, CA",
    state="CA",
    bbox=(-117.25, 34.00, -117.10, 34.09),
    sources=(
        SourceSpec(
            slug="street_trees",
            name="City of Redlands Street Trees",
            url=(
                "https://services.arcgis.com/FLM8UAw9y5MmuVTV/arcgis/rest/services/"
                "Street_Trees/FeatureServer/0"
            ),
            where="BOTANICALN NOT IN ('Vacant site','Stump')",
            out_fields=("BOTANICALN", "COMMONNAME", "OBJECTID"),
            species_fields=("BOTANICALN",),
            common_fields=("COMMONNAME",),
            fixed_city="Redlands, CA",
            homepage="https://www.cityofredlands.org/",
            notes="One row per planting site; the TREE column is per-site numbering.",
        ),
    ),
    attribution="City of Redlands GIS",
)


SACRAMENTO_CA = CitySpec(
    slug="sacramento_ca",
    name="Sacramento, CA",
    state="CA",
    bbox=(-121.56, 38.42, -121.32, 38.69),
    sources=(
        SourceSpec(
            slug="city_maintained_trees",
            name="City of Sacramento City Maintained Trees",
            url=(
                "https://services5.arcgis.com/54falWtcpty3V47Z/arcgis/rest/services/"
                "City_Maintained_Trees/FeatureServer/0"
            ),
            where=(
                "BOTANICAL IS NOT NULL AND BOTANICAL <> '' AND "
                "SPECIES NOT IN ('vacant site','stump','unknown spp','Unknown species')"
            ),
            out_fields=("BOTANICAL", "SPECIES", "OBJECTID"),
            species_fields=("BOTANICAL", "SPECIES"),
            common_fields=("SPECIES",),
            fixed_city="Sacramento, CA",
            homepage="https://data.cityofsacramento.org/",
        ),
    ),
    attribution="City of Sacramento Public Works (City Maintained Trees)",
)


ESCONDIDO_CA = CitySpec(
    slug="escondido_ca",
    name="Escondido, CA",
    state="CA",
    bbox=(-117.14, 33.05, -116.96, 33.20),
    sources=(
        SourceSpec(
            slug="tree_inventory",
            name="City of Escondido Tree Inventory",
            url=(
                "https://services2.arcgis.com/eJcVbjTyyZIzZ5Ye/arcgis/rest/services/"
                "TreeInventory/FeatureServer/0"
            ),
            where=(
                "BOTANICAL_NAME NOT IN "
                "('Vacant site','Stump','Stump - not accessible')"
            ),
            out_fields=("BOTANICAL_NAME", "COMMON_NAME", "OBJECTID"),
            species_fields=("BOTANICAL_NAME", "COMMON_NAME"),
            common_fields=("COMMON_NAME",),
            fixed_city="Escondido, CA",
            homepage="https://www.escondido.org/",
        ),
    ),
    attribution="City of Escondido GIS",
)


ENCINITAS_CA = CitySpec(
    slug="encinitas_ca",
    name="Encinitas, CA",
    state="CA",
    bbox=(-117.31, 33.01, -117.20, 33.09),
    sources=(
        SourceSpec(
            slug="tree_inventory",
            name="City of Encinitas Tree Inventory",
            url=(
                "https://services2.arcgis.com/yrktbS5Xw87hJQvs/arcgis/rest/services/"
                "TreeInvEncinitas_Public/FeatureServer/0"
            ),
            where=(
                "LifeCycleStatus = 'Active' AND BotanicalName NOT IN "
                "('Vacant site','Stump','Unknown','Unsuitable site',"
                "'Stump - not accessible')"
            ),
            out_fields=("BotanicalName", "CommonName", "OBJECTID"),
            species_fields=("BotanicalName", "CommonName"),
            common_fields=("CommonName",),
            fixed_city="Encinitas, CA",
            homepage="https://www.encinitasca.gov/",
        ),
    ),
    attribution="City of Encinitas GIS",
)


# --- North Bay -------------------------------------------------------------
NAPA_CA = CitySpec(
    slug="napa_ca",
    name="Napa, CA",
    state="CA",
    bbox=(-122.36, 38.24, -122.25, 38.36),
    sources=(
        SourceSpec(
            slug="trees",
            name="Trees Napa",
            url=(
                "https://services3.arcgis.com/HVKk0mXWDGCVpolG/arcgis/rest/services/"
                "Trees_Napa/FeatureServer/0"
            ),
            out_fields=("SPECIES_BO", "SPECIES_CO", "FID"),
            species_fields=("SPECIES_BO", "SPECIES_CO"),
            common_fields=("SPECIES_CO",),
            id_field="FID",
            fixed_city="Napa, CA",
            homepage="https://www.cityofnapa.org/",
            notes=(
                "Davey Resource Group inventory published from a contractor "
                "ArcGIS account; last data edit 2024-08-06."
            ),
        ),
    ),
    attribution="City of Napa / Davey Resource Group (ArcGIS Online)",
)


# --- San Diego County ------------------------------------------------------
LA_MESA_CA = CitySpec(
    slug="la_mesa_ca",
    name="La Mesa, CA",
    state="CA",
    bbox=(-117.07, 32.70, -116.95, 32.81),
    sources=(
        SourceSpec(
            slug="tree_inventory",
            name="City of La Mesa Tree Inventory",
            url=(
                "https://services3.arcgis.com/iYP51zxNr6TITn6r/arcgis/rest/services/"
                "Tree_Inventory/FeatureServer/4"
            ),
            out_fields=("BotanicalName", "CommonName", "OBJECTID"),
            species_fields=("BotanicalName", "CommonName"),
            common_fields=("CommonName",),
            fixed_city="La Mesa, CA",
            homepage="https://www.cityoflamesa.us/",
            notes=(
                "Official city layer. Six records sit at (0, 0) and are dropped "
                "by the bbox check; the service's declared extent is broken for "
                "the same reason."
            ),
        ),
    ),
    attribution="City of La Mesa GIS",
)


# --- Southern California ---------------------------------------------------
VENTURA_CA = CitySpec(
    slug="ventura_ca",
    name="Ventura, CA",
    state="CA",
    bbox=(-119.36, 34.22, -119.13, 34.36),
    sources=(
        SourceSpec(
            slug="trees",
            name="City of San Buenaventura Trees",
            url=(
                "https://services.arcgis.com/dBVj4EXO3IdRPOqb/arcgis/rest/services/"
                "OpenData_AssetsOther_Trees/FeatureServer/0"
            ),
            out_fields=("BOTANICAL", "COMMON", "OBJECTID"),
            species_fields=("BOTANICAL", "COMMON"),
            common_fields=("COMMON",),
            page_size=16000,
            fixed_city="Ventura, CA",
            homepage="https://www.cityofventura.ca.gov/",
            notes=(
                "Do not filter on FICTITIOUS='X': it is a West Coast Arborists "
                "internal flag, not a placeholder marker, and half the real trees "
                "carry it."
            ),
        ),
    ),
    attribution="City of San Buenaventura (City of Ventura) GIS",
)


SANTA_MONICA_CA = CitySpec(
    slug="santa_monica_ca",
    name="Santa Monica, CA",
    state="CA",
    bbox=(-118.52, 33.99, -118.43, 34.05),
    sources=(
        SourceSpec(
            slug="trees",
            name="Santa Monica Trees",
            url=(
                "https://services7.arcgis.com/piPfTFmrV9d1DIvN/arcgis/rest/services/"
                "Santa_Monica_Trees/FeatureServer/0"
            ),
            out_fields=("botanicaln", "commonname", "FID"),
            species_fields=("botanicaln", "commonname"),
            common_fields=("commonname",),
            id_field="FID",
            fixed_city="Santa Monica, CA",
            homepage="https://www.santamonica.gov/",
            notes=(
                "isvalid is a truncated ' Ye' and fictitious is a single space on "
                "every row, so neither works as a filter."
            ),
        ),
    ),
    attribution="City of Santa Monica (Esri Local Government deployment)",
)


SIGNAL_HILL_CA = CitySpec(
    slug="signal_hill_ca",
    name="Signal Hill, CA",
    state="CA",
    bbox=(-118.19, 33.78, -118.14, 33.83),
    sources=(
        SourceSpec(
            slug="street_trees",
            name="City of Signal Hill Street Trees",
            url=(
                "https://services9.arcgis.com/LUBoZWfQwvBnZCmP/arcgis/rest/services/"
                "Street_Trees_public/FeatureServer/0"
            ),
            out_fields=("botanical_name", "common_name", "OBJECTID"),
            species_fields=("botanical_name", "common_name"),
            common_fields=("common_name",),
            fixed_city="Signal Hill, CA",
            homepage="https://www.cityofsignalhill.org/",
            notes="2022 inventory — a snapshot, not a live feed.",
        ),
    ),
    attribution="City of Signal Hill GIS",
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
    LOS_GATOS_CA,
    SAN_MATEO_CA,
    BURLINGAME_CA,
    SANTA_CLARA_COUNTY_CA,
    BRISBANE_CA,
    SANTA_CLARA_CA,
    SUNNYVALE_CA,
    ATHERTON_CA,
    OAKLAND_CA,
    PASADENA_CA,
    RIVERSIDE_CA,
    REDLANDS_CA,
    SACRAMENTO_CA,
    ESCONDIDO_CA,
    ENCINITAS_CA,
    NAPA_CA,
    LA_MESA_CA,
    VENTURA_CA,
    SANTA_MONICA_CA,
    SIGNAL_HILL_CA,
)

CITY_BY_SLUG = {city.slug: city for city in CITIES}


def get_city(slug: str) -> CitySpec:
    try:
        return CITY_BY_SLUG[slug]
    except KeyError as exc:
        raise SystemExit(
            f"Unknown city {slug!r}. Available: {', '.join(sorted(CITY_BY_SLUG))}"
        ) from exc
