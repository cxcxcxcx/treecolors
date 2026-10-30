"""Merge raw records, resolve species, and write GeoJSON/summary/QA output."""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "py"))

from tree_data import deterministic_color  # noqa: E402

from .cities import CitySpec
from .species import SpeciesResolver, is_invalid
from .sources import RAW_ROOT


OUTPUT_ROOT = PROJECT_ROOT / "data" / "output"
GEOJSON_DIR = OUTPUT_ROOT / "geojson"
SUMMARY_DIR = OUTPUT_ROOT / "summary"
QA_DIR = OUTPUT_ROOT / "qa"


def _color_range(species_key: str, info: dict[str, Any]) -> str:
    lower = species_key.lower()
    if "ginkgo" in lower:
        return "orange"
    if info.get("deciduous"):
        return "red" if info.get("fall_colors") else "brown"
    return "green"


def _read_city_records(city: CitySpec) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for source in city.sources:
        path = RAW_ROOT / city.slug / f"{source.slug}.jsonl"
        if not path.exists():
            print(f"  [warn] missing raw file: {path}")
            continue
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                record.setdefault("city", source.fixed_city or city.name)
                record["_source"] = source.slug
                record.setdefault("source_key", f"{city.slug}:{source.slug}")
                records.append(record)
    return records


def process_city(city: CitySpec, resolver: SpeciesResolver) -> dict[str, Any]:
    GEOJSON_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
    QA_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[process] {city.name} ({city.slug})")
    raw_records = _read_city_records(city)
    if not raw_records:
        raise SystemExit(f"No raw records for {city.slug}; run fetch first.")

    seen: set[tuple[float, float, str]] = set()
    invalid: Counter[str] = Counter()
    outside_bbox = 0
    missing: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    color_counts: Counter[str] = Counter()
    species_counts: Counter[str] = Counter()
    species_colors: dict[str, tuple[str, str]] = {}
    kept: list[dict[str, Any]] = []
    deduped = 0
    no_geometry = 0

    for record in raw_records:
        source_counts[record["_source"]] += 1
        try:
            lat = float(record["lat"])
            lng = float(record["lng"])
        except (KeyError, TypeError, ValueError):
            no_geometry += 1
            continue

        west, south, east, north = city.bbox
        buffer = 0.01  # ~1 km; absorbs boundary/rounding differences
        if not (west - buffer <= lng <= east + buffer and south - buffer <= lat <= north + buffer):
            outside_bbox += 1
            continue

        raw_species = str(record.get("raw") or "").strip()
        if is_invalid(raw_species):
            invalid[raw_species] += 1
            continue
        def try_resolve(value: str):
            if not value:
                return None
            hit = resolver.resolve(value)
            if hit is not None:
                return hit
            if "," in value:
                first, second = value.split(",", 1)
                inverted = f"{second.strip()} {first.strip()}"
                return resolver.resolve(inverted)
            return None

        resolution = try_resolve(raw_species)
        # Some publishers put a species code in the main field and the common
        # name in a second field (e.g. Mississauga's BOTNAME/BOTDESC).  Fall
        # back to the common name before declaring the row unresolved.
        common_species = str(record.get("common") or "").strip()
        if resolution is None and common_species and common_species != raw_species:
            resolution = try_resolve(common_species)
        if resolution is None or "deciduous" not in resolution.info:
            missing[raw_species] += 1
            continue

        dedupe_key = (round(lat, 5), round(lng, 5), resolution.key)
        if dedupe_key in seen:
            deduped += 1
            continue
        seen.add(dedupe_key)

        info = resolution.info
        color_range = _color_range(resolution.key, info)
        color = deterministic_color(resolution.key, color_range=color_range)
        species_counts[resolution.display] += 1
        species_colors.setdefault(resolution.display, (color, color_range))
        color_counts[color_range] += 1

        kept.append(
            {
                "lat": lat,
                "lng": lng,
                "species_key": resolution.key,
                "species": resolution.display,
                "city": record.get("city") or city.name,
                "source_key": record.get("source_key") or f"{city.slug}:unknown",
                "color": color,
                "color_range": color_range,
                "deciduous": bool(info.get("deciduous")),
                "fall_colors": bool(info.get("fall_colors")),
                "beautiful_flowers": bool(info.get("beautiful_flowers")),
                "blooming_season": info.get("blooming_season") or "N/A",
                "common_names": info.get("common_names") or [],
                "chinese_common_names": info.get("chinese_common_names") or [],
                "explanation": info.get("explanation") or "",
            }
        )

    features = [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [round(item["lng"], 6), round(item["lat"], 6)],
            },
            "properties": {
                "species": item["species"],
                "city": item["city"],
                "source_key": item["source_key"],
                "color": item["color"],
                "color_range": item["color_range"],
                "deciduous": item["deciduous"],
                "fall_colors": item["fall_colors"],
                "beautiful_flowers": item["beautiful_flowers"],
                "blooming_season": item["blooming_season"],
                "common_names": item["common_names"],
                "chinese_common_names": item["chinese_common_names"],
                "explanation": item["explanation"],
            },
        }
        for item in kept
    ]

    geojson_path = GEOJSON_DIR / f"trees_{city.slug}.geojson"
    with geojson_path.open("w", encoding="utf-8") as handle:
        json.dump(
            {"type": "FeatureCollection", "features": features},
            handle,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    summary: dict[str, list[dict[str, float]]] = defaultdict(list)
    for item in kept:
        summary[item["species"]].append({"lat": round(item["lat"], 6), "lng": round(item["lng"], 6)})
    summary_list = [
        {"species": species, "locations": locations}
        for species, locations in sorted(summary.items(), key=lambda pair: len(pair[1]), reverse=True)
    ]
    summary_path = SUMMARY_DIR / f"tree_summary_{city.slug}.json"
    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(summary_list, handle, ensure_ascii=False, separators=(",", ":"))

    bbox = (
        {
            "west": min(item["lng"] for item in kept),
            "south": min(item["lat"] for item in kept),
            "east": max(item["lng"] for item in kept),
            "north": max(item["lat"] for item in kept),
        }
        if kept
        else None
    )
    qa = {
        "city": city.name,
        "slug": city.slug,
        "sources": dict(source_counts),
        "raw_records": len(raw_records),
        "kept": len(kept),
        "deduped": deduped,
        "outside_bbox": outside_bbox,
        "no_geometry": no_geometry,
        "invalid_placeholders": sum(invalid.values()),
        "invalid_top": invalid.most_common(15),
        "missing_species": sum(missing.values()),
        "missing_unique": len(missing),
        "missing_top": missing.most_common(30),
        "species_count": len(species_counts),
        "species_top": species_counts.most_common(30),
        "species": [
            {
                "species": name,
                "count": count,
                "color": species_colors.get(name, ("#888888", "green"))[0],
                "color_range": species_colors.get(name, ("#888888", "green"))[1],
            }
            for name, count in species_counts.most_common()
        ],
        "color_counts": dict(color_counts),
        "bbox": bbox,
        "geojson": str(geojson_path.relative_to(PROJECT_ROOT)),
        "summary": str(summary_path.relative_to(PROJECT_ROOT)),
    }
    qa_path = QA_DIR / f"{city.slug}.json"
    with qa_path.open("w", encoding="utf-8") as handle:
        json.dump(qa, handle, ensure_ascii=False, indent=2)

    print(
        f"  kept {len(kept):,}/{len(raw_records):,} "
        f"(deduped {deduped:,}, outside {outside_bbox:,}, invalid {sum(invalid.values()):,}, "
        f"missing {sum(missing.values()):,}, species {len(species_counts)})"
    )
    print(f"  -> {geojson_path.relative_to(PROJECT_ROOT)}")
    return qa
