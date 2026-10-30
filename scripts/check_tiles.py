#!/usr/bin/env python3
"""Validate the generated PMTiles file with the `pmtiles` CLI."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", default="web/trees.pmtiles")
    parser.add_argument("--min-bytes", type=int, default=10_000_000)
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        raise SystemExit(f"Missing {path}")
    size = path.stat().st_size
    if size < args.min_bytes:
        raise SystemExit(f"{path} is suspiciously small: {size:,} bytes")

    output = subprocess.check_output(["pmtiles", "show", str(path)], text=True)
    print(output)
    values = dict(re.findall(r"^([a-z ]+):\s*(.+)$", output, re.MULTILINE))
    max_zoom = values.get("max zoom", "").strip()
    bounds = values.get("bounds", "").strip()
    if max_zoom != "12":
        raise SystemExit(f"expected max zoom 12, got {max_zoom!r}")
    if not bounds:
        raise SystemExit("PMTiles header has no bounds")
    print(f"OK: {size:,} bytes, max zoom {max_zoom}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
