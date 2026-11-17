"""Drop placeholder "species" from the legacy GeoJSON exports.

The `py/run_*.py` scripts passed every row through, so records that are not
trees at all — ``STUMP``, ``OTHER``, ``Other tree``, ``Stump Stump`` — ended up
as point features with a species name.  The tree_pipeline drops them via
``is_invalid()``, but the legacy exports predate that check, so they surface
in the species panel and in a popup as if they were species.

    python3 scripts/drop_placeholder_rows.py [--dry-run] [slug ...]

Rebuild web assets and tiles afterwards.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "py"))

from tree_pipeline.species import is_invalid  # noqa: E402

GEOJSON = ROOT / "data" / "output" / "geojson"


def drop(path: Path, dry_run: bool) -> Counter:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    features = data.get("features", [])
    kept = []
    removed: Counter = Counter()
    for feature in features:
        name = str((feature.get("properties") or {}).get("species") or "").strip()
        if name and is_invalid(name):
            removed[name] += 1
            continue
        kept.append(feature)

    if not removed:
        return removed

    data["features"] = kept
    if not dry_run:
        with path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, separators=(",", ":"))
    return removed


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
        removed = drop(path, args.dry_run)
        if not removed:
            continue
        changed += 1
        detail = ", ".join(f"{name} ×{count:,}" for name, count in removed.most_common())
        verb = "would drop" if args.dry_run else "dropped"
        print(f"{verb} {sum(removed.values()):,} rows from {path.name}: {detail}")

    if not changed:
        print("Nothing to drop.")
    elif not args.dry_run:
        print("Rebuild web assets and tiles: build_web_assets(), then ./build_tiles.sh")


if __name__ == "__main__":
    main()
