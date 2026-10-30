#!/usr/bin/env python3
"""Summarize data/output/qa/*.json across all cities."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qa-dir", default="data/output/qa")
    parser.add_argument("--missing-limit", type=int, default=8)
    args = parser.parse_args()

    qa_dir = Path(args.qa_dir)
    rows = []
    for path in sorted(qa_dir.glob("*.json")):
        with path.open(encoding="utf-8") as handle:
            rows.append(json.load(handle))

    if not rows:
        raise SystemExit(f"No QA files found in {qa_dir}")

    print(f"{'city':20s} {'kept':>9s} {'invalid':>9s} {'outside':>8s} {'missing':>8s}")
    print("-" * 60)
    total = 0
    for qa in rows:
        total += qa.get("kept", 0)
        print(
            f"{qa.get('slug', '?'):20s} "
            f"{qa.get('kept', 0):9,d} "
            f"{qa.get('invalid_placeholders', 0):9,d} "
            f"{qa.get('outside_bbox', 0):8,d} "
            f"{qa.get('missing_species', 0):8,d}"
        )
    print("-" * 60)
    print(f"{'TOTAL':20s} {total:9,d}")

    problems = [qa for qa in rows if qa.get("missing_species", 0) > 0]
    if problems:
        print("\nCities with unresolved species:")
        for qa in problems:
            print(f"\n{qa['slug']} ({qa['missing_species']:,} rows)")
            for name, count in (qa.get("missing_top") or [])[: args.missing_limit]:
                print(f"  {count:6,d}  {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
