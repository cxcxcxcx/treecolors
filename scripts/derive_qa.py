#!/usr/bin/env python3
"""Produce a derived quality report for cities that have no pipeline QA file.

Eleven California/Vancouver imports predate the configured city list, so they
have GeoJSON but no data/output/qa/<slug>.json.  Their raw records are gone,
which means the honest report is the one that can be computed from the built
GeoJSON -- and it is written to data/output/qa/derived/ so it is never confused
with a report produced by the real pipeline.

Usage:
    python3 scripts/derive_qa.py            # all cities missing a QA file
    python3 scripts/derive_qa.py --all      # refresh every derived report
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
QA_DIR = PROJECT_ROOT / "data" / "output" / "qa"
DERIVED_DIR = QA_DIR / "derived"
GEOJSON_DIR = PROJECT_ROOT / "data" / "output" / "geojson"
STATS_PATH = PROJECT_ROOT / "web" / "species_stats.json"


def _iter_features(path: Path):
    data = json.loads(path.read_text())
    for feature in data.get("features", []):
        yield feature


def build(slug: str, name: str, geojson: Path) -> dict:
    species: Counter[str] = Counter()
    colors: Counter[str] = Counter()
    west = south = east = north = None
    kept = 0
    for feature in _iter_features(geojson):
        kept += 1
        properties = feature.get("properties") or {}
        species[properties.get("species") or "unknown"] += 1
        colors[properties.get("color_range") or "unknown"] += 1
        geometry = feature.get("geometry") or {}
        coordinates = geometry.get("coordinates") or []
        if len(coordinates) >= 2:
            lng, lat = coordinates[0], coordinates[1]
            west = lng if west is None else min(west, lng)
            east = lng if east is None else max(east, lng)
            south = lat if south is None else min(south, lat)
            north = lat if north is None else max(north, lat)
    return {
        "city": name,
        "slug": slug,
        "report_kind": "derived",
        "derived_from": str(geojson.relative_to(PROJECT_ROOT)),
        "note": "Computed from built GeoJSON; raw source records are not available, "
                "so raw_records/deduped/invalid counts cannot be reconstructed.",
        "raw_records": None,
        "kept": kept,
        "deduped": None,
        "outside_bbox": None,
        "no_geometry": 0,
        "invalid_placeholders": None,
        "missing_species": 0,
        "species_count": len(species),
        "species_top": species.most_common(30),
        "color_counts": dict(colors),
        "bbox": {"west": west, "south": south, "east": east, "north": north},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true", help="Refresh every derived report")
    args = parser.parse_args()

    stats = json.loads(STATS_PATH.read_text())
    names = {city["slug"]: city["name"] for city in stats["cities"]}
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    written = 0
    for slug, name in sorted(names.items()):
        if not args.all and (QA_DIR / f"{slug}.json").exists():
            continue
        geojson = GEOJSON_DIR / f"trees_{slug}.geojson"
        if not geojson.exists():
            print(f"  [skip] {slug}: no geojson")
            continue
        report = build(slug, name, geojson)
        (DERIVED_DIR / f"{slug}.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
        print(f"  [derived] {slug}: {report['kept']:,} trees, {report['species_count']} species")
        written += 1
    print(f"wrote {written} derived reports into {DERIVED_DIR.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
