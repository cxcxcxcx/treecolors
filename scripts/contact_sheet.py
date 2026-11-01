#!/usr/bin/env python3
"""Build a labelled contact sheet for artwork QA.

    python3 scripts/contact_sheet.py --kind leaf  --out /tmp/leaves.png
    python3 scripts/contact_sheet.py --kind plate --limit 60

Species are ordered by how many trees they represent, so the top-left corner is
what most visitors see first.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "leaf": PROJECT_ROOT / "web" / "leaves",
    "plate": PROJECT_ROOT / "web" / "plates",
}


def _ordered_slugs(kind: str, limit: int) -> list[str]:
    stats = json.loads((PROJECT_ROOT / "web" / "species_stats.json").read_text())
    counts: dict[str, int] = {}
    for city in stats["cities"]:
        for entry in city.get("species", []):
            slug = entry.get(kind) or ""
            if slug:
                counts[slug] = counts.get(slug, 0) + entry["count"]
    ordered = [slug for slug, _ in sorted(counts.items(), key=lambda item: -item[1])]
    if limit:
        ordered = ordered[:limit]
    return ordered


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", default="leaf", choices=sorted(SOURCES))
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--columns", type=int, default=12)
    parser.add_argument("--size", type=int, default=96)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    directory = SOURCES[args.kind]
    slugs = [slug for slug in _ordered_slugs(args.kind, args.limit)
             if (directory / f"{slug}.png").exists()]
    if not slugs:
        raise SystemExit("no artwork found for that kind")

    cell = args.size
    gap, label = 8, 16
    columns = args.columns
    rows = (len(slugs) + columns - 1) // columns
    sheet = Image.new("RGB", (gap + columns * (cell + gap),
                              gap + rows * (cell + label + gap)), (250, 250, 250))
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
    except OSError:
        font = ImageFont.load_default()

    for index, slug in enumerate(slugs):
        row, column = divmod(index, columns)
        x = gap + column * (cell + gap)
        y = gap + row * (cell + label + gap)
        image = Image.open(directory / f"{slug}.png").convert("RGB").resize((cell, cell), Image.LANCZOS)
        sheet.paste(image, (x, y))
        draw.text((x, y + cell + 2), slug[:18], font=font, fill=(40, 40, 40))

    sheet.save(args.out)
    print(f"{len(slugs)} images -> {args.out} {sheet.size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
