#!/usr/bin/env python3
"""Build an Instagram promo set from the assets already in the repo.

Every image is generated from real project material: the map screenshots in
promo/shots, the botanical plates in web/plates, the app icon and the live
counts in web/species_stats.json.

    python3 promo/make_instagram.py

Outputs (promo/instagram/):
    01-hero.png      1080x1350  feed
    02-colours.png   1080x1350  feed
    03-ginkgo.png    1080x1350  feed
    04-tap.png       1080x1350  feed
    05-cities.png    1080x1350  feed
    story.png        1080x1920  story / reel cover
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "promo" / "instagram"
SHOTS = ROOT / "promo" / "shots"
PLATES = ROOT / "web" / "plates"
ICON = ROOT / "web" / "icon-f-512.png"
BOTANISENSE = ROOT / "promo" / "brand" / "botanisense-flower.png"

CREAM = (247, 240, 225)
INK = (31, 45, 58)
MUTED = (108, 120, 131)
ACCENT = (184, 64, 22)
CARD = (255, 252, 245)

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
BOLD = f"{FONT_DIR}/DejaVuSans-Bold.ttf"
REG = f"{FONT_DIR}/DejaVuSans.ttf"
SERIF_IT = "/usr/share/fonts/TTF/DejaVuSerifCondensed-Italic.ttf"


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


BAY_AREA = {"berkeley", "concordca", "cupertino", "fremontca",
            "palo_alto", "sf", "san_jose", "sanleandroca", "mountain_view_ca"}


def stats() -> dict:
    data = json.loads((ROOT / "web" / "species_stats.json").read_text())
    cities = data["cities"]
    bay = [c for c in cities if c["slug"] in BAY_AREA]
    vancouver = next((c for c in cities if c["slug"] == "vancouver"), None)
    return {
        "trees": sum(c["total"] for c in cities),
        "cities": len(cities),
        "plates": len(list(PLATES.glob("*.png"))),
        "bay_cities": len(bay),
        "bay_trees": sum(c["total"] for c in bay),
        "bay_fall": sum(entry["count"] for c in bay for entry in c["species"]
                        if entry.get("color_range") in ("red", "orange")),
        "city": {c["slug"]: {
            "name": c["name"],
            "total": c["total"],
            "fall": sum(entry["count"] for entry in c["species"]
                        if entry.get("color_range") in ("red", "orange")),
        } for c in bay},
        "bay_names": sorted(c["name"].replace(" County", "").replace(" City", "") for c in bay),
        "vancouver_trees": vancouver["total"] if vancouver else 0,
    }


def rounded_photo(path: Path, size: tuple[int, int], radius: int = 28,
                  crop_bottom: float = 0.0) -> Image.Image:
    image = Image.open(path).convert("RGB")
    if crop_bottom:
        image = image.crop((0, 0, image.width, int(image.height * (1 - crop_bottom))))
    # cover-crop to the target aspect
    target = size[0] / size[1]
    source = image.width / image.height
    if source > target:
        new_w = int(image.height * target)
        image = image.crop(((image.width - new_w) // 2, 0, (image.width + new_w) // 2, image.height))
    else:
        new_h = int(image.width / target)
        image = image.crop((0, (image.height - new_h) // 2, image.width, (image.height + new_h) // 2))
    image = image.resize(size, Image.LANCZOS)
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size[0], size[1]], radius=radius, fill=255)
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    out.paste(image, (0, 0), mask)
    return out


def card(canvas: Image.Image, box: tuple[int, int, int, int], radius: int = 28, fill=CARD) -> None:
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        [box[0] + 4, box[1] + 10, box[2] + 4, box[3] + 10], radius=radius, fill=(60, 40, 20, 45))
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(12)))
    ImageDraw.Draw(canvas).rounded_rectangle(box, radius=radius, fill=fill)


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt, width: int) -> list[str]:
    words = text.split()
    lines, line = [], ""
    for word in words:
        probe = f"{line} {word}".strip()
        if draw.textlength(probe, font=fnt) <= width:
            line = probe
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def brand_block(canvas: Image.Image, x: int, y: int, compact: bool = False) -> None:
    """TreeColors mark, then the BotaniSense flower with “by BotaniSense”."""
    draw = ImageDraw.Draw(canvas)
    size = 56 if not compact else 44
    logo = Image.open(ICON).convert("RGBA").resize((size, size), Image.LANCZOS)
    canvas.alpha_composite(logo, (x, y))
    draw.text((x + size + 14, y + (2 if compact else 4)), "TreeColors",
              font=font(BOLD, 28 if compact else 32), fill=INK)

    flower_size = 26 if not compact else 22
    flower = Image.open(BOTANISENSE).convert("RGBA")
    flower.thumbnail((flower_size, flower_size), Image.LANCZOS)
    line_y = y + (size - 12 if compact else size - 8)
    canvas.alpha_composite(flower, (x + size + 14, line_y))
    draw.text((x + size + 14 + flower.width + 8, line_y - 2), "by BotaniSense",
              font=font(REG, 21 if compact else 23), fill=MUTED)


def chrome(canvas: Image.Image, handle: bool = True) -> None:
    draw = ImageDraw.Draw(canvas)
    brand_block(canvas, 72, 1176)
    if handle:
        draw.text((72, 1256), "treecolors.botanisense.app", font=font(REG, 22), fill=MUTED)


def _share_bar(canvas, x, y, width, height, share, label):
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle([x, y, x + width, y + height], radius=height // 2, fill=(228, 220, 203))
    turned = int(width * share)
    if turned > height:
        draw.rounded_rectangle([x, y, x + turned, y + height], radius=height // 2, fill=(153, 28, 106))
    if label:
        draw.text((x, y - 34), label, font=font(BOLD, 24), fill=INK)


def build_hero(info: dict) -> None:
    """The contrast that makes a map necessary, with the numbers drawn."""
    W, H = 1080, 1350
    canvas = Image.new("RGBA", (W, H), CREAM + (255,))
    draw = ImageDraw.Draw(canvas)
    draw.text((72, 80), "BAY AREA · AUTUMN COLOUR", font=font(BOLD, 24), fill=ACCENT)
    draw.text((72, 122), "Same bay.", font=font(BOLD, 76), fill=INK)
    draw.text((72, 202), "Three times the colour.", font=font(BOLD, 74), fill=INK)
    draw.text((72, 296), "Share of street trees that change colour in autumn.",
              font=font(REG, 27), fill=MUTED)

    panels = [
        ("map-all-sf.png", "San Francisco", info["city"]["sf"]),
        ("cmp-cupertino.png", "Cupertino", info["city"]["cupertino"]),
    ]
    y = 356
    for file, label, city in panels:
        photo = rounded_photo(SHOTS / file, (936, 300), radius=22)
        canvas.alpha_composite(photo, (72, y))
        share = city["fall"] / city["total"]
        draw.text((72, y + 316), f"{label} — {share * 100:.0f}% turn",
                  font=font(BOLD, 30), fill=INK)
        draw.text((560, y + 320), f"{city['fall']:,} of {city['total']:,} trees",
                  font=font(REG, 23), fill=MUTED)
        _share_bar(canvas, 72, y + 372, 936, 26, share, "")
        y += 452

    draw.text((72, 1240), "A tree “turns” when its leaves go red, purple or yellow before falling.",
              font=font(REG, 22), fill=MUTED)
    draw.text((72, 1270), "Green trees stay green all winter — the map lets you skip them.",
              font=font(REG, 22), fill=MUTED)
    canvas.convert("RGB").save(OUT / "01-contrast.png")


def build_colours() -> None:
    W, H = 1080, 1350
    canvas = Image.new("RGBA", (W, H), CREAM + (255,))
    draw = ImageDraw.Draw(canvas)
    draw.text((72, 96), "READ IT LIKE A COLOUR MAP", font=font(BOLD, 26), fill=ACCENT)
    draw.text((72, 146), "What to look for", font=font(BOLD, 66), fill=INK)

    rows = [
        ("#cc0000", "#800080", "These turn", "Red through purple: the trees worth a walk"),
        ("#ffa500", None, "Ginkgo", "Every ginkgo turns the same yellow"),
        ("#8b4513", "#2b2b2b", "Turns, but muted", "Browns and dark tones, later in the season"),
        ("#2d5016", "#4caf50", "Skip these", "Evergreens stay green all winter"),
    ]
    y = 330
    for left, right, title, note in rows:
        card(canvas, (72, y, 1008, y + 190), radius=24)
        swatch = Image.new("RGBA", (96, 96), (0, 0, 0, 0))
        sd = ImageDraw.Draw(swatch)
        sd.rounded_rectangle([0, 0, 96, 96], radius=48, fill=left)
        if right:
            sd.pieslice([0, 0, 96, 96], start=270, end=90, fill=right)
        canvas.alpha_composite(swatch, (116, y + 47))
        draw.text((252, y + 44), title, font=font(BOLD, 40), fill=INK)
        draw.text((252, y + 100), note, font=font(REG, 27), fill=MUTED)
        y += 214
    chrome(canvas)
    canvas.convert("RGB").save(OUT / "03-legend.png")


def build_species(info: dict) -> None:
    W, H = 1080, 1350
    canvas = Image.new("RGBA", (W, H), CREAM + (255,))
    draw = ImageDraw.Draw(canvas)
    draw.text((72, 96), "WHAT YOU WILL SEE", font=font(BOLD, 26), fill=ACCENT)
    draw.text((72, 146), "Four that carry the season", font=font(BOLD, 54), fill=INK)

    picks = [
        ("pistacia_chinensis.png", "Chinese pistache", "scarlet to orange"),
        ("liquidambar_styraciflua.png", "Sweetgum", "wine red, purple"),
        ("ginkgo_biloba.png", "Ginkgo", "one clean yellow"),
        ("lagerstroemia_indica.png", "Crape myrtle", "late, deep red"),
    ]
    x0, y0, size, gap, row_h = 72, 232, 400, 64, 508
    for index, (file, name, colour) in enumerate(picks):
        col, row = index % 2, index // 2
        x = x0 + col * (size + gap)
        y = y0 + row * row_h
        card(canvas, (x - 8, y - 8, x + size + 8, y + size + 8), radius=26)
        plate = rounded_photo(PLATES / file, (size, size), radius=20, crop_bottom=0.11)
        canvas.alpha_composite(plate, (x, y))
        draw.text((x, y + size + 12), name, font=font(BOLD, 28), fill=INK)
        draw.text((x, y + size + 46), colour, font=font(REG, 22), fill=MUTED)
    logo = Image.open(ICON).convert("RGBA").resize((52, 52), Image.LANCZOS)
    canvas.alpha_composite(logo, (72, 1252))
    draw.text((136, 1262), "Tree Species Map", font=font(BOLD, 26), fill=INK)
    draw.text((136, 1296), "treecolors.botanisense.app", font=font(REG, 21), fill=MUTED)
    canvas.convert("RGB").save(OUT / "02-species.png")


def build_tap() -> None:
    W, H = 1080, 1350
    canvas = Image.new("RGBA", (W, H), CREAM + (255,))
    draw = ImageDraw.Draw(canvas)
    draw.text((72, 96), "HOW TO USE IT", font=font(BOLD, 26), fill=ACCENT)
    draw.text((72, 146), "Three steps to a colour walk", font=font(BOLD, 52), fill=INK)

    shot = Image.open(SHOTS / "ui-sheet-mobile.png").convert("RGB")
    shot = shot.crop((0, 560, shot.width, 1420))
    shot = shot.resize((560, int(560 * shot.height / shot.width)), Image.LANCZOS).convert("RGBA")
    card(canvas, (72, 280, 72 + shot.width + 36, 280 + shot.height + 36), radius=28)
    canvas.alpha_composite(shot, (90, 298))

    x = 690
    items = [
        ("1", "Open the map", "no account, no app"),
        ("2", "Zoom to your block", "purple dots turn; green ones stay"),
        ("3", "Tap a tree", "species, plate, photos"),
    ]
    y = 330
    for num, title, note in items:
        draw.ellipse([x, y + 2, x + 36, y + 38], outline=ACCENT, width=3)
        draw.text((x + 18, y + 20), num, font=font(BOLD, 21), fill=ACCENT, anchor="mm")
        yy = y
        for line in wrap(draw, title, font(BOLD, 25), 300):
            draw.text((x + 50, yy), line, font=font(BOLD, 25), fill=INK)
            yy += 30
        for line in wrap(draw, note, font(REG, 21), 290):
            draw.text((x + 50, yy + 4), line, font=font(REG, 21), fill=MUTED)
            yy += 27
        y = max(y + 110, yy + 60)
    chrome(canvas)
    


def build_cities(info: dict) -> None:
    """Coverage as one wide map plus a few example neighbourhoods."""
    W, H = 1080, 1350
    canvas = Image.new("RGBA", (W, H), CREAM + (255,))
    draw = ImageDraw.Draw(canvas)
    draw.text((72, 80), "AROUND THE BAY", font=font(BOLD, 24), fill=ACCENT)
    draw.text((72, 122), "Some cities, some gaps", font=font(BOLD, 60), fill=INK)
    draw.text((72, 196), "Every city inventory we could find, drawn where the trees actually stand.",
              font=font(REG, 25), fill=MUTED)
    photo = rounded_photo(SHOTS / "bay-new.png", (936, 800), radius=24)
    canvas.alpha_composite(photo, (72, 262))
    draw.text((72, 1086), "San Francisco · Oakland · Palo Alto · Mountain View · Cupertino · San Jose · Fremont",
              font=font(REG, 22), fill=INK)
    draw.text((72, 1122), f"{info['bay_trees']:,} trees in the Bay Area · {info['bay_fall']:,} of them change colour",
              font=font(REG, 22), fill=MUTED)
    brand_block(canvas, 72, 1180, compact=True)
    draw.text((72, 1258), "treecolors.botanisense.app", font=font(REG, 21), fill=MUTED)
    canvas.convert("RGB").save(OUT / "04-coverage.png")


def build_mountainview(info: dict) -> None:
    """A city close-up: what a neighbourhood actually looks like on the map."""
    W, H = 1080, 1350
    canvas = Image.new("RGBA", (W, H), CREAM + (255,))
    draw = ImageDraw.Draw(canvas)
    draw.text((72, 80), "CITY CLOSE-UP", font=font(BOLD, 24), fill=ACCENT)
    draw.text((72, 122), "Mountain View", font=font(BOLD, 72), fill=INK)
    mv = info["city"].get("mountain_view_ca")
    if mv:
        share = mv["fall"] / mv["total"] * 100
        draw.text((72, 208), f"{mv['total']:,} street trees · {mv['fall']:,} of them turn ({share:.0f}%)",
                  font=font(REG, 26), fill=MUTED)
    photo = rounded_photo(SHOTS / "mv-close.png", (936, 780), radius=26)
    canvas.alpha_composite(photo, (72, 276))
    draw.text((72, 1076), "Purple dots change colour. Green ones stay green.",
              font=font(REG, 24), fill=MUTED)
    chrome(canvas)
    canvas.convert("RGB").save(OUT / "06-mountainview.png")


def build_backcover(info: dict) -> None:
    """Last slide / share card: a real map, the promise, the address."""
    W, H = 1080, 1350
    canvas = Image.new("RGBA", (W, H), CREAM + (255,))
    photo = rounded_photo(SHOTS / "map-all-sj.png", (936, 620), radius=30)
    canvas.alpha_composite(photo, (72, 190))
    draw = ImageDraw.Draw(canvas)
    draw.text((72, 92), "TREECOLORS.BOTANISENSE.APP", font=font(BOLD, 22), fill=ACCENT)
    draw.text((72, 878), "Find the colour.", font=font(BOLD, 72), fill=INK)
    draw.text((72, 960), "Walk to it.", font=font(BOLD, 72), fill=ACCENT)
    draw.text((72, 1064), f"{info['bay_fall']:,} Bay Area trees that turn, each one mapped",
              font=font(REG, 28), fill=MUTED)
    draw.text((72, 1112), "Free · no account · works on your phone",
              font=font(REG, 26), fill=MUTED)
    brand_block(canvas, 72, 1178)
    canvas.convert("RGB").save(OUT / "05-backcover.png")


def build_story(info: dict) -> None:
    """9:16 story / reel cover."""
    W, H = 1080, 1920
    canvas = Image.new("RGBA", (W, H), CREAM + (255,))
    photo = rounded_photo(SHOTS / "map-all-sj.png", (936, 900), radius=36)
    canvas.alpha_composite(photo, (72, 380))
    draw = ImageDraw.Draw(canvas)
    logo = Image.open(ICON).convert("RGBA").resize((110, 110), Image.LANCZOS)
    canvas.alpha_composite(logo, (72, 120))
    draw.text((206, 130), "TreeColors", font=font(BOLD, 46), fill=INK)
    flower = Image.open(BOTANISENSE).convert("RGBA")
    flower.thumbnail((44, 44), Image.LANCZOS)
    canvas.alpha_composite(flower, (206, 190))
    draw.text((206 + flower.width + 12, 196), "by BotaniSense", font=font(REG, 28), fill=MUTED)

    draw.text((72, 1330), "Find the colour.", font=font(BOLD, 74), fill=INK)
    draw.text((72, 1418), "Walk to it.", font=font(BOLD, 74), fill=ACCENT)
    draw.text((72, 1530), f"Bay Area · {info['bay_fall']:,} trees that turn",
              font=font(REG, 34), fill=MUTED)
    draw.rounded_rectangle([72, 1650, 600, 1740], radius=45, fill=ACCENT)
    draw.text((116, 1676), "Link in bio", font=font(BOLD, 36), fill=(255, 255, 255))
    canvas.convert("RGB").save(OUT / "story.png")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    info = stats()
    build_hero(info)
    build_colours()
    build_species(info)
    build_tap()
    build_cities(info)
    build_mountainview(info)
    build_backcover(info)
    build_story(info)
    for path in sorted(OUT.glob("*.png")):
        print(f"  {path.name}  {path.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
