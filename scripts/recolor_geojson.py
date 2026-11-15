"""Rewrite the `color` of every tree in data/output/geojson with species_color().

Exports made before species_color() hashed the raw inventory name, so the same
species had a different colour in each city. This brings old files in line
without re-running their pipelines. Streams each file as text (both the
pretty-printed legacy files and the compact new ones keep `species` before
`color`, then `color_range`, `deciduous`, `fall_colors`), so NYC's 450 MB never
becomes a Python object tree. Rebuild web assets and tiles afterwards.

With --sync-traits, `color_range`, `deciduous` and `fall_colors` are also
re-derived from the current knowledge base, so a species that an older KB
filed differently in one city lands in the same category everywhere.

    python3 scripts/recolor_geojson.py [--dry-run] [--sync-traits] [slug ...]
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "py"))
from tree_pipeline.export import _color_range, species_color  # noqa: E402
from tree_pipeline.species import load_resolver  # noqa: E402

GEOJSON = ROOT / "data" / "output" / "geojson"
STR = r'"((?:[^"\\]|\\.)*)"'
BOOL = r'(true|false|null|"[^"]*")'  # a few legacy rows hold null or a string
FEATURE = re.compile(
    rf'("species":\s*){STR}((?:(?!"species":).)*?"color":\s*)"([^"]*)"(,\s*"color_range":\s*){STR}'
    rf'(,\s*"deciduous":\s*){BOOL}(,\s*"fall_colors":\s*){BOOL}', re.S)


def recolor(path: Path, resolver, dry_run: bool, sync_traits: bool, moved: Counter) -> Counter:
    stats = Counter()
    keys: dict[str, tuple | None] = {}

    def swap(m: re.Match) -> str:
        raw = json.loads(f'"{m[2]}"')
        if raw not in keys:
            hit = resolver.resolve(raw)
            keys[raw] = (hit.key, hit.info) if hit and "deciduous" in hit.info else None
        stats["trees"] += 1
        if keys[raw] is None:
            stats["unresolved"] += 1
            return m[0]
        key, info = keys[raw]
        color_range, deciduous, fall = json.loads(f'"{m[6]}"'), m[8], m[10]
        if sync_traits:
            new_range = _color_range(key, info)
            if new_range != color_range:
                moved[(key, color_range, new_range)] += 1
                color_range = new_range
            deciduous = "true" if info.get("deciduous") else "false"
            fall = "true" if info.get("fall_colors") else "false"
        color = species_color(key, color_range)
        out = (f'{m[1]}"{m[2]}"{m[3]}"{color}"{m[5]}"{color_range}"'
               f'{m[7]}{deciduous}{m[9]}{fall}')
        if out != m[0]:
            stats["changed"] += 1
        return out

    text = path.read_text(encoding="utf-8")
    out = FEATURE.sub(swap, text)
    stats["features"] = text.count('"Feature"')
    del text
    if stats["trees"] != stats["features"]:
        raise SystemExit(f"{path.name}: matched {stats['trees']} of {stats['features']} features; not writing")
    if not dry_run and stats["changed"]:
        tmp = path.with_suffix(".geojson.tmp")
        tmp.write_text(out, encoding="utf-8")
        tmp.replace(path)
    return stats


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("slugs", nargs="*")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--sync-traits", action="store_true")
    args = parser.parse_args()
    resolver = load_resolver()
    paths = [GEOJSON / f"trees_{s}.geojson" for s in args.slugs] or sorted(GEOJSON.glob("trees_*.geojson"))
    moved: Counter = Counter()
    for path in paths:
        s = recolor(path, resolver, args.dry_run, args.sync_traits, moved)
        print(f"{path.stem.removeprefix('trees_'):24s} trees={s['trees']:>8,} changed={s['changed']:>8,} "
              f"unresolved={s['unresolved']:>6,}", flush=True)
    if moved:
        print(f"\ncategory changes: {sum(moved.values()):,} trees")
        for (key, old, new), n in moved.most_common(40):
            print(f"  {n:>8,}  {key:40s} {old} -> {new}")


if __name__ == "__main__":
    main()
