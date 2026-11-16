#!/usr/bin/env python3
"""Render web/og-image.png (1200x630) from the numbers in web/species_stats.json.

The card is what Slack, X, iMessage and most link previews show, so its counts
must match the map. The layout, fonts and colours below reproduce the original
hand-drawn card exactly; only the numbers, and the GitHub line in the footer,
come from outside this file.

    python3 scripts/make_og_image.py            # rewrite web/og-image.png
    python3 scripts/make_og_image.py --check    # exit 1 if the image is stale

The type is DejaVu Sans, which ships with Debian/Ubuntu (fonts-dejavu-core);
nothing is bundled. The icon is web/icon-f-1024.png.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "web" / "og-image.png"
ICON = ROOT / "web" / "icon-f-1024.png"

# Where each distribution puts fonts-dejavu-core.
FONT_DIRS = [
    Path("/usr/share/fonts/truetype/dejavu"),  # Debian, Ubuntu
    Path("/usr/share/fonts/TTF"),              # Arch, Fedora
    Path("/usr/share/fonts/dejavu"),           # openSUSE
]

W, H = 1200, 630
BG = (247, 240, 225)
ACCENT = (184, 64, 22)
INK = (31, 45, 58)
MUTED = (74, 85, 96)
LABEL = (60, 70, 80)
FOOT = (120, 100, 80)
DOMAIN = "treecolors.botanisense.app"
GITHUB = "github.com/cxcxcxcx/treecolors"

# (label, left half, right half, swatch left edge, swatch top, label x, label y)
LEGEND = [
    ("Evergreen", (45, 80, 22), (76, 175, 80), 420, 360, 474, 366),
    ("Ginkgo", (255, 165, 0), (255, 165, 0), 642, 360, 696, 366),
    ("Fall colour", (204, 0, 0), (128, 0, 128), 420, 422, 474, 428),
    ("Other deciduous", (139, 69, 19), (43, 43, 43), 640, 422, 694, 428),
]


def stats() -> tuple[str, str]:
    data = json.loads((ROOT / "web" / "species_stats.json").read_text(encoding="utf-8"))
    trees = sum(city["total"] for city in data["cities"])
    return f"{trees / 1_000_000:.1f} million".replace(".0 million", " million"), str(len(data["cities"]))


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    for directory in FONT_DIRS:
        path = directory / name
        if path.exists():
            return ImageFont.truetype(str(path), size)
    # Some distributions (and CI images) keep the family somewhere else.
    for path in Path("/usr/share/fonts").rglob(name):
        return ImageFont.truetype(str(path), size)
    raise SystemExit(f"{name} not found; install fonts-dejavu-core")


def draw_split_circle(draw: ImageDraw.ImageDraw, box, left, right) -> None:
    draw.pieslice(box, 90, 270, fill=left)
    draw.pieslice(box, 270, 90, fill=right)


def render() -> Image.Image:
    millions, cities = stats()
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    draw.rectangle((0, 0, W, 8), fill=ACCENT)

    icon = Image.open(ICON).convert("RGBA")
    icon = icon.crop(icon.getbbox()).resize((204, 258), Image.LANCZOS)
    img.paste(icon, (118, 171), icon)

    draw.text((420, 150), "Tree Species Map", font=font("DejaVuSans-Bold.ttf", 60), fill=INK)
    sub = font("DejaVuSans.ttf", 29)
    draw.text((420, 232), f"{millions} street trees in {cities} North American", font=sub, fill=MUTED)
    draw.text((420, 272), "cities, coloured by species and fall foliage", font=sub, fill=MUTED)

    label_font = font("DejaVuSans.ttf", 25)
    for label, left, right, x, y, tx, ty in LEGEND:
        draw_split_circle(draw, (x, y, x + 40, y + 40), left, right)
        draw.text((tx, ty), label, font=label_font, fill=LABEL)

    draw.text((70, 545), DOMAIN, font=label_font, fill=FOOT)
    github_w = draw.textlength(GITHUB, font=label_font)
    draw.text((W - 70 - github_w, 545), GITHUB, font=label_font, fill=FOOT)

    return img


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if og-image.png is stale")
    args = parser.parse_args()

    new = render()
    if args.check:
        if not OUT.exists() or Image.open(OUT).convert("RGB").tobytes() != new.tobytes():
            print("web/og-image.png is stale; run python3 scripts/make_og_image.py", file=sys.stderr)
            return 1
        print("og-image.png is current")
        return 0

    new.save(OUT, optimize=True)
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
