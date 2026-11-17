"""Normalize all-caps species names in the legacy GeoJSON exports.

The `py/run_*.py` scripts predate the tree_pipeline's `_smart_title()`, so a
few legacy exports shout: Cupertino's 16,584 trees are all `PISTACIA
CHINENSIS`, and Los Angeles ships 16 species twice — once mixed case and once
all caps (`Liquidambar styraciflua` / `LIQUIDAMBAR STYRACIFLUA`).  The detail
sheet and the species panel key off the exact string, so those rows render as
separate species.

An all-caps name that already has a mixed-case spelling in the same file is
rewritten to that spelling, which merges the duplicate rows.  Otherwise it is
smart-titled the same way the pipeline titles new inventories.  Colour and
traits are untouched: they were computed from the resolved species key, which
is case-insensitive.

    python3 scripts/normalize_species_case.py [--dry-run] [slug ...]

Rebuild web assets and tiles afterwards.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "py"))

from tree_pipeline.species import _smart_title, is_invalid  # noqa: E402

GEOJSON = ROOT / "data" / "output" / "geojson"

_CULTIVAR_RE = re.compile(r"(['‘’])([^'‘’]*)(['’'])")


def _needs_fix(name: str) -> bool:
    # Inventory shorthand (QUPE, ZADD 12) is not a species name.  Test the
    # part before the cultivar: Pasadena ships "FRAXINUS VELUTINA 'modesto'",
    # all caps except the cultivar the resolver lower-cased.  A bare genus is
    # left alone unless it carries a cultivar ("LAGERSTROEMIA 'TUSCARORA'").
    if is_invalid(name):
        return False
    head = _CULTIVAR_RE.sub("", name).strip()
    if not head.isupper() or len(head) <= 3:
        return False
    return " " in head or bool(_CULTIVAR_RE.search(name))


def _title(name: str) -> str:
    """Delegate to the pipeline's display helper so the two cannot disagree."""
    return _smart_title(name)


def normalize(path: Path, dry_run: bool) -> Counter:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    features = data.get("features", [])
    names = {
        str((f.get("properties") or {}).get("species") or "").strip()
        for f in features
    }
    names.discard("")
    # Prefer the mixed-case spelling when a file carries both forms; a plain
    # ``{n.lower(): n}`` over a set picks whichever the iteration hits first.
    by_lower: dict[str, str] = {}
    for name in names:
        current = by_lower.get(name.lower())
        if current is None or (current.isupper() and not name.isupper()):
            by_lower[name.lower()] = name

    mapping: dict[str, str] = {}
    merged = 0
    for name in names:
        if not _needs_fix(name):
            continue
        twin = by_lower.get(name.lower())
        if twin and twin != name:
            # A mixed-case spelling of the same species is already in this
            # file: adopt it so the two rows become one species.
            mapping[name] = twin
            merged += 1
        else:
            mapping[name] = _title(name)

    stats = Counter()
    if not mapping:
        return stats

    for feature in features:
        props = feature.get("properties") or {}
        raw = str(props.get("species") or "").strip()
        new = mapping.get(raw)
        if new:
            props["species"] = new
            stats["rows"] += 1
        if raw:
            stats["trees"] += 1

    stats["names"] = len(mapping)
    stats["merged"] = merged

    if not dry_run:
        with path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, separators=(",", ":"))
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("slugs", nargs="*")
    args = parser.parse_args()

    paths = (
        [GEOJSON / f"trees_{slug}.geojson" for slug in args.slugs]
        if args.slugs
        else sorted(GEOJSON.glob("trees_*.geojson"))
    )

    changed = 0
    for path in paths:
        if not path.exists():
            raise SystemExit(f"Missing {path}")
        stats = normalize(path, args.dry_run)
        if not stats:
            continue
        changed += 1
        verb = "would rewrite" if args.dry_run else "rewrote"
        print(
            f"{verb} {stats['rows']:,} of {stats['trees']:,} rows in {path.name}: "
            f"{stats['names']} names, {stats['merged']} merged into an existing spelling"
        )

    if not changed:
        print("Nothing to normalize.")
    elif not args.dry_run:
        print("Rebuild web assets and tiles: build_web_assets(), then ./build_tiles.sh")


if __name__ == "__main__":
    main()
