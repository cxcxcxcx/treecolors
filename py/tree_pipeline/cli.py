"""CLI for the tree pipeline.

Usage (from the ``py`` directory)::

    python -m tree_pipeline list
    python -m tree_pipeline fetch --all
    python -m tree_pipeline process --all
    python -m tree_pipeline all --city washington_dc
    python -m tree_pipeline tiles
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from .cities import CITIES, get_city
from .enrich import enrich
from .export import process_city
from .species import load_resolver
from .sources import fetch_city
from .web_assets import build_web_assets


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _split_city_args(values: list[str] | None) -> list[str]:
    slugs: list[str] = []
    for value in values or []:
        slugs.extend(part.strip() for part in value.split(",") if part.strip())
    return slugs


def _select_cities(args: argparse.Namespace) -> list:
    if getattr(args, "all", False):
        return list(CITIES)
    slugs = _split_city_args(getattr(args, "city", None))
    if not slugs:
        raise SystemExit("Pass --city <slug> (repeatable) or --all.")
    return [get_city(slug) for slug in slugs]


def cmd_list(_: argparse.Namespace) -> int:
    for city in CITIES:
        print(f"{city.slug:22s} {city.name}  ({len(city.sources)} source(s))")
        for source in city.sources:
            print(f"  - {source.slug}: {source.name}")
    return 0


def cmd_fetch(args: argparse.Namespace) -> int:
    for city in _select_cities(args):
        fetch_city(city, force=args.force)
    return 0


def cmd_process(args: argparse.Namespace) -> int:
    resolver = load_resolver()
    for city in _select_cities(args):
        process_city(city, resolver)
    return 0


def cmd_all(args: argparse.Namespace) -> int:
    cities = _select_cities(args)
    for city in cities:
        fetch_city(city, force=args.force)
    resolver = load_resolver()
    for city in cities:
        process_city(city, resolver)
    build_web_assets()
    return 0


def cmd_enrich(args: argparse.Namespace) -> int:
    enrich(_select_cities(args), dry_run=args.dry_run)
    return 0


def cmd_web_assets(_: argparse.Namespace) -> int:
    build_web_assets()
    return 0


def cmd_tiles(_: argparse.Namespace) -> int:
    script = PROJECT_ROOT / "build_tiles.sh"
    if not script.exists():
        raise SystemExit(f"Missing {script}")
    subprocess.run([str(script)], cwd=PROJECT_ROOT, check=True)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Tree map city pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List configured cities/sources")
    list_parser.set_defaults(func=cmd_list)

    for name, func in (("fetch", cmd_fetch), ("process", cmd_process), ("all", cmd_all)):
        sub = subparsers.add_parser(name)
        sub.add_argument("--city", action="append", help="City slug; repeat or comma-separate")
        sub.add_argument("--all", action="store_true", help="All configured cities")
        sub.add_argument("--force", action="store_true", help="Re-fetch cached raw data")
        sub.set_defaults(func=func)

    enrich_parser = subparsers.add_parser(
        "enrich", help="Fill missing species in the knowledge base with GPT-4o"
    )
    enrich_parser.add_argument("--city", action="append", help="City slug; repeat or comma-separate")
    enrich_parser.add_argument("--all", action="store_true", help="All configured cities")
    enrich_parser.add_argument("--dry-run", action="store_true", help="List unresolved names only")
    enrich_parser.set_defaults(func=cmd_enrich)

    web_parser = subparsers.add_parser(
        "web-assets", help="Generate species_stats.json and sources.json for the frontend"
    )
    web_parser.set_defaults(func=cmd_web_assets)

    tiles_parser = subparsers.add_parser("tiles", help="Build one PMTiles file from all GeoJSON")
    tiles_parser.set_defaults(func=cmd_tiles)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
