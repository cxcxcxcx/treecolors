"""Generate small frontend sidecars: species statistics and source links.

The big PMTiles file stays authoritative for popup details.  These two JSON
files only power the species panel and the per-tree source link, so they are
small enough to ship as normal web assets.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from .cities import CITIES
from .export import _color_range, species_color
from .species import load_resolver


PROJECT_ROOT = Path(__file__).resolve().parents[2]
GEOJSON_DIR = PROJECT_ROOT / "data" / "output" / "geojson"
WEB_DIR = PROJECT_ROOT / "web"

# Cities produced by the legacy ``py/run_*.py`` scripts.  Their GeoJSON does
# not carry a ``city``/``source_key`` property, so the frontend falls back to
# these bounding boxes and the popup links to the matching source.
LEGACY_CITIES: dict[str, dict[str, Any]] = {
    "palo_alto": {
        "name": "Palo Alto, CA",
        "bbox": [-122.18, 37.39, -122.09, 37.48],
        "url": "https://services6.arcgis.com/evmyRZRrsopdeog7/arcgis/rest/services/TreeData/FeatureServer/0",
    },
    "san_jose": {
        "name": "San Jose, CA",
        "bbox": [-122.05, 37.20, -121.65, 37.47],
        "url": "https://data.sanjoseca.gov/dataset/street-tree",
    },
    "cupertino": {
        "name": "Cupertino, CA",
        "bbox": [-122.08, 37.28, -122.00, 37.35],
        "url": "https://data.cupertino.org/",
    },
    "sf": {
        "name": "San Francisco, CA",
        "bbox": [-122.53, 37.70, -122.35, 37.83],
        "url": "https://data.sfgov.org/City-Infrastructure/Street-Tree-List/tkzw-k3nq",
    },
    "berkeley": {
        "name": "Berkeley, CA",
        "bbox": [-122.32, 37.84, -122.23, 37.91],
        "url": "https://geodata.lib.berkeley.edu/catalog/berkeley-s7gq2s",
    },
    "fremontca": {
        "name": "Fremont, CA",
        "bbox": [-122.05, 37.47, -121.75, 37.60],
        "url": "https://www.fremont.gov/",
    },
    "sanleandroca": {
        "name": "San Leandro, CA",
        "bbox": [-122.18, 37.68, -122.10, 37.75],
        "url": "https://www.sanleandro.org/",
    },
    "sdtt": {
        "name": "San Diego, CA",
        "bbox": [-117.28, 32.53, -116.90, 33.11],
        "url": "https://data.sandiego.gov/",
    },
    "los_angeles": {
        "name": "Los Angeles, CA",
        "bbox": [-118.67, 33.70, -118.15, 34.34],
        "url": "https://data.lacity.org/",
    },
    "vancouver": {
        "name": "Vancouver, BC",
        "bbox": [-123.25, 49.20, -123.02, 49.32],
        "url": "https://opendata.vancouver.ca/explore/dataset/public-trees/",
    },
    "concordca": {
        "name": "Concord, CA",
        "bbox": [-122.10, 37.93, -121.90, 38.03],
        "url": "https://www.cityofconcord.org/",
    },
}


def _city_meta(slug: str) -> dict[str, Any]:
    for city in CITIES:
        if city.slug == slug:
            return {
                "name": city.name,
                "bbox": list(city.bbox),
                "url": next((s.homepage for s in city.sources if s.homepage), ""),
            }
    return LEGACY_CITIES.get(slug, {"name": slug, "bbox": None, "url": ""})


def _qa_by_slug() -> dict[str, dict[str, Any]]:
    qa_dir = PROJECT_ROOT / "data" / "output" / "qa"
    result: dict[str, dict[str, Any]] = {}
    for path in qa_dir.glob("*.json"):
        with path.open(encoding="utf-8") as handle:
            qa = json.load(handle)
        result[qa["slug"]] = qa
    return result


PLATE_DIR = PROJECT_ROOT / "samples" / "plates80"
LEAF_DIR = PROJECT_ROOT / "samples" / "leaves"


def _plate_files() -> set[str]:
    if not PLATE_DIR.exists():
        return set()
    return {path.stem for path in PLATE_DIR.glob("*.png")}


def _leaf_files() -> set[str]:
    if not LEAF_DIR.exists():
        return set()
    return {path.stem for path in LEAF_DIR.glob("*.png")}


def _with_common(entries: list[dict[str, Any]], resolver) -> list[dict[str, Any]]:
    """Attach a display common name looked up from the species knowledge base."""
    plates = _plate_files()
    leaves = _leaf_files()
    for entry in entries:
        common = ""
        key = ""
        plate = ""
        hit = resolver.resolve(entry["species"])
        if hit is not None:
            display = entry["species"].strip().lower()
            for name in hit.info.get("common_names") or []:
                name = str(name).strip()
                if not name:
                    continue
                low = name.lower()
                if low == display or low in display or display in low:
                    continue
                # skip inventory codes such as QUPE
                if name.isupper() and len(name) <= 6 and " " not in name:
                    continue
                if name.islower() or name.isupper():
                    name = name.title()
                common = name
                break
        entry["common"] = common
        if hit is not None:
            key = hit.key
            # Stored colours and categories may predate species_color() and the
            # current KB; recompute both so the legend and list match the tiles
            # after scripts/recolor_geojson.py --sync-traits.
            if "deciduous" in hit.info:
                entry["color_range"] = _color_range(key, hit.info)
            entry["color"] = species_color(key, entry.get("color_range") or "green")
            slug = "".join(c if c.isalnum() else "_" for c in key.lower()).strip("_")
            if slug in plates:
                plate = slug
        entry["key"] = key
        entry["leaf"] = slug if slug in leaves else ""
        entry["plate"] = plate
    return entries


def build_species_stats() -> dict[str, Any]:
    resolver = load_resolver()
    qa_by_slug = _qa_by_slug()
    cities: list[dict[str, Any]] = []
    for path in sorted(GEOJSON_DIR.glob("trees_*.geojson")):
        slug = path.stem.removeprefix("trees_")
        if slug == "oakland":
            # Legacy Oakland export: every row carries the same placeholder
            # coordinate.  Superseded by oakland_ca, which has real geometry.
            continue
        meta = _city_meta(slug)
        qa = qa_by_slug.get(slug)
        if qa and qa.get("species"):
            cities.append(
                {
                    "slug": slug,
                    "name": meta["name"],
                    "bbox": meta.get("bbox") or qa.get("bbox"),
                    "total": qa["kept"],
                    "species": _with_common(qa["species"], resolver),
                }
            )
            print(f"  stats {slug}: {qa['kept']:,} (QA)")
            continue

        # Legacy cities do not have a QA file; derive stats from GeoJSON.
        print(f"  stats {slug}: reading GeoJSON ...")
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
        counts: Counter[str] = Counter()
        colors: dict[str, tuple[str, str]] = {}
        for feature in data.get("features", []):
            props = feature.get("properties") or {}
            species = str(props.get("species") or "").strip()
            if not species:
                continue
            counts[species] += 1
            colors.setdefault(
                species,
                (props.get("color") or "#888888", props.get("color_range") or "green"),
            )
        cities.append(
            {
                "slug": slug,
                "name": meta["name"],
                "bbox": meta.get("bbox"),
                "total": sum(counts.values()),
                "species": _with_common(
                    [
                        {
                            "species": species,
                            "count": count,
                            "color": colors[species][0],
                            "color_range": colors[species][1],
                        }
                        for species, count in counts.most_common()
                    ],
                    resolver,
                ),
            }
        )
        del data

    payload = {"cities": cities}
    WEB_DIR.mkdir(parents=True, exist_ok=True)
    out = WEB_DIR / "species_stats.json"
    with out.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
    print(f"  -> {out.relative_to(PROJECT_ROOT)}")
    return payload


def build_sources() -> dict[str, Any]:
    by_key: dict[str, Any] = {}
    by_city: dict[str, Any] = {}
    for city in CITIES:
        for source in city.sources:
            by_key[f"{city.slug}:{source.slug}"] = {
                "name": source.name,
                "url": source.homepage or source.url,
                "city": source.fixed_city or city.name,
            }
        first = next((s for s in city.sources if s.homepage), None)
        if first:
            by_city[city.name] = {"name": first.name, "url": first.homepage}

    legacy = [
        {"name": meta["name"], "bbox": meta["bbox"], "url": meta["url"]}
        for meta in LEGACY_CITIES.values()
    ]
    payload = {"by_key": by_key, "by_city": by_city, "legacy": legacy}
    out = WEB_DIR / "sources.json"
    with out.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
    print(f"  -> {out.relative_to(PROJECT_ROOT)}")
    return payload


def build_web_assets() -> None:
    print("[web-assets] species stats")
    build_species_stats()
    print("[web-assets] source links")
    build_sources()
