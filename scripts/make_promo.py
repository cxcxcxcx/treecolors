#!/usr/bin/env python3
"""Build the Instagram / 小红书 promo set in English and Chinese.

    python3 scripts/make_promo.py            # both languages
    python3 scripts/make_promo.py --lang en  # English only
    python3 scripts/make_promo.py --lang zh  # Chinese only

Output: promo/instagram/ (en) and promo/instagram/zh/ (zh).
All numbers come from web/species_stats.json, so they never drift from the app.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "promo" / "shots"
PLATES = ROOT / "web" / "plates"
ICON = ROOT / "web" / "icon-f-512.png"
FLOWER = ROOT / "promo" / "brand" / "botanisense-flower.png"

CREAM = (247, 240, 225)
INK = (31, 45, 58)
MUTED = (108, 120, 131)
ACCENT = (184, 64, 22)
CARD = (255, 252, 245)
DOMAIN = "treecolors.botanisense.app"

FONT_EN_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_EN = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_ZH_BOLD = "/usr/share/fonts/wenquanyi/wqy-microhei/wqy-microhei.ttc"
FONT_ZH = "/usr/share/fonts/wenquanyi/wqy-microhei/wqy-microhei.ttc"

BAY_AREA = {"berkeley", "concordca", "cupertino", "fremontca", "palo_alto",
            "sf", "san_jose", "sanleandroca", "mountain_view_ca"}

COPY = {
    "en": {
        "bold": FONT_EN_BOLD, "reg": FONT_EN,
        "s1_eyebrow": "BAY AREA · AUTUMN COLOUR",
        "s1_h1": ["Same bay.", "Three times the colour."],
        "s1_sub": "Share of street trees that change colour in autumn.",
        "s1_left": "San Francisco", "s1_right": "Cupertino",
        "s1_turn": "{share:.0f}% turn", "s1_count": "{fall:,} of {total:,} trees",
        "s1_note1": "A tree “turns” when its leaves go red, purple or yellow before falling.",
        "s1_note2": "Green ones stay green all winter — skip them.",
        "s2_eyebrow": "WHAT YOU WILL SEE",
        "s2_h1": "Four that carry the season",
        "s2_items": [("pistacia_chinensis.png", "Chinese pistache", "scarlet to orange"),
                     ("liquidambar_styraciflua.png", "Sweetgum", "wine red, purple"),
                     ("ginkgo_biloba.png", "Ginkgo", "one clean yellow"),
                     ("lagerstroemia_indica.png", "Crape myrtle", "late, deep red")],
        "s3_eyebrow": "READ IT LIKE A COLOUR MAP",
        "s3_h1": "What to look for",
        "s3_items": [("#cc0000", "#800080", "These turn", "Red through purple: worth a walk"),
                     ("#ffa500", None, "Ginkgo", "Every ginkgo turns one orange"),
                     ("#8b4513", "#2b2b2b", "Turns, muted", "Browns, later in the season"),
                     ("#2d5016", "#4caf50", "Skip these", "Evergreens stay green all winter")],
        "s4_eyebrow": "PALO ALTO + MOUNTAIN VIEW",
        "s4_h1": "Two cities, side by side",
        "s4_sub": "Same peninsula, different planting.",
        "s5_h1": ["Find the colour.", "Walk to it."],
        "s5_sub": "{fall:,} Bay Area trees that turn, each one mapped",
        "s5_free": "Free · no account · works on your phone",
        "s6_eyebrow": "ONE NEIGHBOURHOOD",
        "s6_h1": "City close-up",
        "s6_note": "Purple dots change colour. Green ones stay green.",
        "s6_stats": "{total:,} trees · {fall:,} turn ({pct:.0f}%)",
        "s4_pa": "Palo Alto", "s4_mv": "Mountain View",
        "story_h1": ["Find the colour.", "Walk to it."],
        "story_sub": "Bay Area · {fall:,} trees that turn",
        "story_cta": "Link in bio",
        "bs_tagline": ["AI that is actually useful", "for plant lovers."],
        "by_bs": "by BotaniSense",
    },
    "zh": {
        "bold": FONT_ZH_BOLD, "reg": FONT_ZH,
        "s1_eyebrow": "湾区 · 秋色",
        "s1_h1": ["同一个湾区，", "三倍的秋色。"],
        "s1_sub": "行道树里，秋天会变色的比例。",
        "s1_left": "旧金山", "s1_right": "库比蒂诺",
        "s1_turn": "{share:.0f}% 会变色", "s1_count": "共 {total:,} 棵，其中 {fall:,} 棵会变",
        "s1_note1": "「会变色」指叶子在落叶前变红、变紫或变黄。",
        "s1_note2": "绿色是常绿树，整个冬天都是绿的，可以直接跳过。",
        "s2_eyebrow": "会看到什么",
        "s2_h1": "撑起秋天的四种树",
        "s2_items": [("pistacia_chinensis.png", "中国黄连木", "猩红到橙"),
                     ("liquidambar_styraciflua.png", "枫香", "酒红、紫"),
                     ("ginkgo_biloba.png", "银杏", "一整条街同时变黄"),
                     ("lagerstroemia_indica.png", "紫薇", "最晚，深红")],
        "s3_eyebrow": "怎么看这张图",
        "s3_h1": "四种颜色",
        "s3_items": [("#cc0000", "#800080", "会变色", "红到紫，值得专门走一趟"),
                     ("#ffa500", None, "银杏", "所有银杏都是同一种橙黄"),
                     ("#8b4513", "#2b2b2b", "变得晚、偏暗", "褐色系，季节靠后"),
                     ("#2d5016", "#4caf50", "常绿，跳过", "整个冬天都是绿的")],
        "s4_eyebrow": "帕洛阿尔托 + 山景城",
        "s4_h1": "相邻两城，同框对比",
        "s4_sub": "同一个半岛，种的东西不一样。",
        "s5_h1": ["找秋色。", "走过去。"],
        "s5_sub": "湾区 {fall:,} 棵会变色的树，每一棵都有位置",
        "s5_free": "免费 · 不用注册 · 手机直接打开",
        "s6_eyebrow": "一个街区",
        "s6_h1": "城市特写",
        "s6_note": "紫点会变色，绿点是常绿。",
        "s6_stats": "共 {total:,} 棵，{fall:,} 棵会变色（{pct:.0f}%）",
        "s4_pa": "帕洛阿尔托", "s4_mv": "山景城",
        "story_h1": ["找秋色。", "走过去。"],
        "story_sub": "湾区 · {fall:,} 棵会变色",
        "story_cta": "主页链接",
        "bs_tagline": ["让 AI 对植物爱好者", "真正有用。"],
        "by_bs": "由 BotaniSense 出品",
    },
}


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def stats() -> dict:
    data = json.loads((ROOT / "web" / "species_stats.json").read_text())
    cities = data["cities"]
    bay = [c for c in cities if c["slug"] in BAY_AREA]

    def fall_of(city):
        return sum(e["count"] for e in city["species"] if e.get("color_range") in ("red", "orange"))

    return {
        "trees": sum(c["total"] for c in cities),
        "cities": len(cities),
        "plates": len(list(PLATES.glob("*.png"))),
        "bay_cities": len(bay),
        "bay_trees": sum(c["total"] for c in bay),
        "bay_fall": sum(fall_of(c) for c in bay),
        "city": {c["slug"]: {"name": c["name"], "total": c["total"], "fall": fall_of(c)} for c in bay},
    }


def rounded_photo(path: Path, size: tuple[int, int], radius: int = 28,
                  crop_bottom: float = 0.0) -> Image.Image:
    image = Image.open(path).convert("RGB")
    if crop_bottom:
        image = image.crop((0, 0, image.width, int(image.height * (1 - crop_bottom))))
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


def card(canvas: Image.Image, box: tuple[int, int, int, int], radius: int = 28) -> None:
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        [box[0] + 4, box[1] + 10, box[2] + 4, box[3] + 10], radius=radius, fill=(60, 40, 20, 45))
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(12)))
    ImageDraw.Draw(canvas).rounded_rectangle(box, radius=radius, fill=CARD)


def fit_text(draw: ImageDraw.ImageDraw, text: str, path: str, size: int, width: int) -> ImageFont.FreeTypeFont:
    """Shrink until the line fits; keeps headlines from running under cards."""
    while size > 24 and draw.textlength(text, font=font(path, size)) > width:
        size -= 2
    return font(path, size)


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt, width: int) -> list[str]:
    words = text.split()
    if not words:
        return []
    lines, line = [], words[0]
    for word in words[1:]:
        probe = f"{line} {word}"
        if draw.textlength(probe, font=fnt) <= width:
            line = probe
        else:
            lines.append(line)
            line = word
    lines.append(line)
    return lines


def brand_footer(canvas: Image.Image, t: dict, y: int = 1192) -> None:
    """Bottom bar: TreeColors plate on the left, BotaniSense slogan + byline right.

    The product keeps the highlight; the attribution carries the one-line
    positioning ("AI that is actually useful for plant lovers") but stays quiet.
    """
    draw = ImageDraw.Draw(canvas)
    icon = 54
    pad = 18
    name_font = font(t["bold"], 26)
    domain_font = font(t["bold"], 20)

    # left plate, sized to its own contents with even padding
    text_x = 72 + pad + icon + 14
    plate_right = text_x + max(draw.textlength("TreeColors", font=name_font),
                               draw.textlength(DOMAIN, font=domain_font)) + pad
    plate = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(plate).rounded_rectangle(
        [72, y, plate_right, y + pad * 2 + icon], radius=16, fill=(255, 252, 245, 235))
    canvas.alpha_composite(plate.filter(ImageFilter.GaussianBlur(0.4)))

    logo = Image.open(ICON).convert("RGBA").resize((icon, icon), Image.LANCZOS)
    canvas.alpha_composite(logo, (72 + pad, y + pad))
    draw.text((text_x, y + pad + 1), "TreeColors", font=name_font, fill=INK)
    draw.text((text_x, y + pad + 34), DOMAIN, font=domain_font, fill=ACCENT)

    # right block: slogan above, byline below, both right-aligned
    tag_font = font(t["reg"], 18)
    right = 1008
    ty = y + pad - 6
    for line in t["bs_tagline"]:
        w = draw.textlength(line, font=tag_font)
        draw.text((right - w, ty), line, font=tag_font, fill=MUTED)
        ty += 24

    flower = Image.open(FLOWER).convert("RGBA")
    flower.thumbnail((22, 22), Image.LANCZOS)
    byline = t["by_bs"]
    by_font = font(t["reg"], 20)
    w = draw.textlength(byline, font=by_font)
    bx = right - (flower.width + 8 + w)
    canvas.alpha_composite(flower, (int(bx), ty + 2))
    draw.text((bx + flower.width + 8, ty), byline, font=by_font, fill=INK)


def build_contrast(info: dict, t: dict, out: Path) -> None:
    W, H = 1080, 1350
    canvas = Image.new("RGBA", (W, H), CREAM + (255,))
    draw = ImageDraw.Draw(canvas)
    draw.text((72, 80), t["s1_eyebrow"], font=font(t["bold"], 24), fill=ACCENT)

    y = 122
    for line in t["s1_h1"]:
        f = fit_text(draw, line, t["bold"], 72, 900)
        draw.text((72, y), line, font=f, fill=INK)
        y += int(f.size * 1.12)
    draw.text((72, y + 6), t["s1_sub"], font=font(t["reg"], 25), fill=MUTED)

    panels = [("map-all-sf.png", t["s1_left"], info["city"]["sf"]),
              ("cmp-cupertino.png", t["s1_right"], info["city"]["cupertino"])]
    y = y + 56
    for file, label, city in panels:
        photo = rounded_photo(SHOTS / file, (936, 236), radius=22)
        canvas.alpha_composite(photo, (72, y))
        share = city["fall"] / city["total"]
        draw.text((72, y + 248), f"{label} — {t['s1_turn'].format(share=share * 100)}",
                  font=font(t["bold"], 30), fill=INK)
        draw.text((72, y + 286), t["s1_count"].format(fall=city["fall"], total=city["total"]),
                  font=font(t["reg"], 23), fill=MUTED)
        bar_y, bar_w = y + 322, 936
        draw.rounded_rectangle([72, bar_y, 72 + bar_w, bar_y + 22], radius=11, fill=(228, 220, 203))
        draw.rounded_rectangle([72, bar_y, 72 + max(22, int(bar_w * share)), bar_y + 22],
                               radius=11, fill=(153, 28, 106))
        y += 392

    note_y = 1085
    for note in (t["s1_note1"], t["s1_note2"]):
        for line in wrap(draw, note, font(t["reg"], 21), 540):
            draw.text((72, note_y), line, font=font(t["reg"], 21), fill=MUTED)
            note_y += 28
    brand_footer(canvas, t)
    canvas.convert("RGB").save(out / "01-contrast.png")


def build_species(info: dict, t: dict, out: Path) -> None:
    W, H = 1080, 1350
    canvas = Image.new("RGBA", (W, H), CREAM + (255,))
    draw = ImageDraw.Draw(canvas)
    draw.text((72, 80), t["s2_eyebrow"], font=font(t["bold"], 24), fill=ACCENT)
    draw.text((72, 122), t["s2_h1"], font=fit_text(draw, t["s2_h1"], t["bold"], 56, 700), fill=INK)

    x0, y0, size, gap, row_h = 72, 232, 372, 72, 462
    for index, (file, name, colour) in enumerate(t["s2_items"]):
        col, row = index % 2, index // 2
        x = x0 + col * (size + gap)
        y = y0 + row * row_h
        card(canvas, (x - 8, y - 8, x + size + 8, y + size + 8), radius=26)
        plate = rounded_photo(PLATES / file, (size, size), radius=20, crop_bottom=0.11)
        canvas.alpha_composite(plate, (x, y))
        draw.text((x, y + size + 12), name, font=font(t["bold"], 28), fill=INK)
        draw.text((x, y + size + 48), colour, font=font(t["reg"], 22), fill=MUTED)
    brand_footer(canvas, t)
    canvas.convert("RGB").save(out / "02-species.png")


def build_legend(info: dict, t: dict, out: Path) -> None:
    W, H = 1080, 1350
    canvas = Image.new("RGBA", (W, H), CREAM + (255,))
    draw = ImageDraw.Draw(canvas)
    draw.text((72, 88), t["s3_eyebrow"], font=font(t["bold"], 24), fill=ACCENT)
    draw.text((72, 136), t["s3_h1"], font=font(t["bold"], 62), fill=INK)

    y = 300
    for left, right, title, note in t["s3_items"]:
        card(canvas, (72, y, 1008, y + 190), radius=24)
        swatch = Image.new("RGBA", (96, 96), (0, 0, 0, 0))
        sd = ImageDraw.Draw(swatch)
        sd.rounded_rectangle([0, 0, 96, 96], radius=48, fill=left)
        if right:
            sd.pieslice([0, 0, 96, 96], start=270, end=90, fill=right)
        canvas.alpha_composite(swatch, (116, y + 47))
        draw.text((252, y + 44), title, font=font(t["bold"], 38), fill=INK)
        draw.text((252, y + 100), note, font=font(t["reg"], 26), fill=MUTED)
        y += 210
    brand_footer(canvas, t)
    canvas.convert("RGB").save(out / "03-legend.png")


def build_region(info: dict, t: dict, out: Path) -> None:
    W, H = 1080, 1350
    canvas = Image.new("RGBA", (W, H), CREAM + (255,))
    draw = ImageDraw.Draw(canvas)
    draw.text((72, 80), t["s4_eyebrow"], font=font(t["bold"], 24), fill=ACCENT)
    draw.text((72, 122), t["s4_h1"], font=fit_text(draw, t["s4_h1"], t["bold"], 58, 540), fill=INK)
    draw.text((72, 196), t["s4_sub"], font=font(t["reg"], 25), fill=MUTED)

    photo = rounded_photo(SHOTS / "pamv-area.png", (936, 820), radius=24)
    canvas.alpha_composite(photo, (72, 246))
    pa = info["city"]["palo_alto"]
    mv = info["city"]["mountain_view_ca"]
    draw.text((72, 1082), f"{t['s4_pa']} — {pa['fall']:,} / {pa['total']:,}",
              font=font(t["bold"], 24), fill=INK)
    draw.text((72, 1118), f"{t['s4_mv']} — {mv['fall']:,} / {mv['total']:,}",
              font=font(t["bold"], 24), fill=INK)
    brand_footer(canvas, t)
    canvas.convert("RGB").save(out / "04-region.png")


def build_city(info: dict, t: dict, out: Path) -> None:
    W, H = 1080, 1350
    canvas = Image.new("RGBA", (W, H), CREAM + (255,))
    draw = ImageDraw.Draw(canvas)
    draw.text((72, 80), t["s6_eyebrow"], font=font(t["bold"], 24), fill=ACCENT)
    draw.text((72, 122), t["s6_h1"], font=fit_text(draw, t["s6_h1"], t["bold"], 70, 900), fill=INK)
    mv = info["city"]["mountain_view_ca"]
    draw.text((72, 206), t["s6_stats"].format(total=mv["total"], fall=mv["fall"],
                                              pct=mv["fall"] / mv["total"] * 100),
              font=font(t["reg"], 26), fill=MUTED)
    photo = rounded_photo(SHOTS / "mv-close.png", (936, 840), radius=26)
    canvas.alpha_composite(photo, (72, 258))
    draw.text((72, 1116), t["s6_note"], font=font(t["reg"], 24), fill=MUTED)
    brand_footer(canvas, t)
    canvas.convert("RGB").save(out / "04-city.png")


def build_backcover(info: dict, t: dict, out: Path) -> None:
    W, H = 1080, 1350
    canvas = Image.new("RGBA", (W, H), CREAM + (255,))
    draw = ImageDraw.Draw(canvas)
    draw.text((72, 76), DOMAIN.upper(), font=font(t["bold"], 26), fill=ACCENT)
    photo = rounded_photo(SHOTS / "map-all-sj.png", (936, 640), radius=28)
    canvas.alpha_composite(photo, (72, 132))
    draw.text((72, 872), t["s5_h1"][0], font=fit_text(draw, t["s5_h1"][0], t["bold"], 66, 900), fill=INK)
    draw.text((72, 946), t["s5_h1"][1], font=fit_text(draw, t["s5_h1"][1], t["bold"], 66, 900), fill=ACCENT)
    draw.text((72, 1036), t["s5_sub"].format(fall=info["bay_fall"]), font=font(t["reg"], 27), fill=MUTED)
    draw.text((72, 1076), t["s5_free"], font=font(t["reg"], 25), fill=MUTED)
    brand_footer(canvas, t, y=1176)
    canvas.convert("RGB").save(out / "05-backcover.png")


def build_story(info: dict, t: dict, out: Path) -> None:
    W, H = 1080, 1920
    canvas = Image.new("RGBA", (W, H), CREAM + (255,))
    photo = rounded_photo(SHOTS / "map-all-sj.png", (936, 860), radius=36)
    canvas.alpha_composite(photo, (72, 360))
    draw = ImageDraw.Draw(canvas)

    logo = Image.open(ICON).convert("RGBA").resize((100, 100), Image.LANCZOS)
    canvas.alpha_composite(logo, (72, 120))
    draw.text((192, 132), "TreeColors", font=font(t["bold"], 44), fill=INK)
    flower = Image.open(FLOWER).convert("RGBA")
    flower.thumbnail((40, 40), Image.LANCZOS)
    canvas.alpha_composite(flower, (192, 186))
    draw.text((192 + flower.width + 10, 190), t["by_bs"], font=font(t["reg"], 26), fill=MUTED)

    draw.text((72, 1290), t["story_h1"][0], font=font(t["bold"], 70), fill=INK)
    draw.text((72, 1372), t["story_h1"][1], font=font(t["bold"], 70), fill=ACCENT)
    draw.text((72, 1476), t["story_sub"].format(fall=info["bay_fall"]), font=font(t["reg"], 32), fill=MUTED)
    draw.text((72, 1536), DOMAIN, font=font(t["bold"], 34), fill=ACCENT)
    draw.rounded_rectangle([72, 1636, 600, 1726], radius=45, fill=ACCENT)
    draw.text((116, 1662), t["story_cta"], font=font(t["bold"], 34), fill=(255, 255, 255))
    canvas.convert("RGB").save(out / "story.png")


def build_xhs_cover(info: dict, t: dict, out: Path, variant: str) -> None:
    """3:4 cover for 小红书 — big Chinese type, one idea, readable at thumbnail."""
    W, H = 1080, 1440
    canvas = Image.new("RGBA", (W, H), CREAM + (255,))
    draw = ImageDraw.Draw(canvas)
    sf = info["city"]["sf"]
    cp = info["city"]["cupertino"]
    sf_share = sf["fall"] / sf["total"] * 100
    cp_share = cp["fall"] / cp["total"] * 100

    # brand strip
    logo = Image.open(ICON).convert("RGBA").resize((56, 56), Image.LANCZOS)
    canvas.alpha_composite(logo, (72, 64))
    draw.text((140, 70), "湾区秋色地图", font=font(t["bold"], 28), fill=INK)
    draw.text((140, 104), DOMAIN, font=font(t["reg"], 18), fill=MUTED)

    if variant == "a":
        draw.text((72, 210), "湾区看秋色", font=font(t["bold"], 96), fill=INK)
        draw.text((72, 320), "别整条街白走", font=font(t["bold"], 96), fill=ACCENT)
        draw.text((72, 470), "同样 20 分钟车程，会变色的树差三倍", font=font(t["reg"], 34), fill=MUTED)
        photo = rounded_photo(SHOTS / "map-all-sf.png", (936, 420), radius=26)
        canvas.alpha_composite(photo, (72, 550))
        # two big numbers
        draw.rounded_rectangle([72, 1010, 500, 1210], radius=24, fill=(255, 252, 245))
        draw.text((100, 1032), "旧金山", font=font(t["bold"], 34), fill=INK)
        draw.text((100, 1082), f"{sf_share:.0f}%", font=font(t["bold"], 96), fill=(153, 28, 106))
        draw.text((300, 1128), "的树会变色", font=font(t["reg"], 26), fill=MUTED)
        draw.rounded_rectangle([540, 1010, 1008, 1210], radius=24, fill=(255, 252, 245))
        draw.text((568, 1032), "库比蒂诺", font=font(t["bold"], 34), fill=INK)
        draw.text((568, 1082), f"{cp_share:.0f}%", font=font(t["bold"], 96), fill=ACCENT)
        draw.text((768, 1128), "的树会变色", font=font(t["reg"], 26), fill=MUTED)
    else:
        draw.text((72, 210), "湾区哪条街", font=font(t["bold"], 96), fill=INK)
        draw.text((72, 320), "秋色最浓？", font=font(t["bold"], 96), fill=ACCENT)
        draw.text((72, 470), "54 万棵行道树，按树种上了颜色", font=font(t["reg"], 34), fill=MUTED)
        photo = rounded_photo(SHOTS / "map-all-sj.png", (936, 560), radius=26)
        canvas.alpha_composite(photo, (72, 560))
        draw.text((72, 1160), "缩到你那条街，紫红色的就是会变的", font=font(t["bold"], 34), fill=INK)

    # footer: domain + byline
    draw.text((72, 1290), DOMAIN, font=font(t["bold"], 30), fill=ACCENT)
    flower = Image.open(FLOWER).convert("RGBA")
    flower.thumbnail((26, 26), Image.LANCZOS)
    byline = t["by_bs"]
    w = draw.textlength(byline, font=font(t["reg"], 22))
    canvas.alpha_composite(flower, (int(1008 - w - 34), 1294))
    draw.text((1008 - w, 1292), byline, font=font(t["reg"], 22), fill=MUTED)
    canvas.convert("RGB").save(out / f"xhs-cover-{variant}.png")


def build(lang: str) -> Path:
    t = COPY[lang]
    info = stats()
    out = ROOT / "promo" / "instagram" if lang == "en" else ROOT / "promo" / "instagram" / "zh"
    out.mkdir(parents=True, exist_ok=True)
    build_contrast(info, t, out)
    build_species(info, t, out)
    build_legend(info, t, out)
    build_city(info, t, out)
    build_backcover(info, t, out)
    build_story(info, t, out)
    if lang == "zh":
        build_xhs_cover(info, t, out, "a")
        build_xhs_cover(info, t, out, "b")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lang", choices=["en", "zh", "both"], default="both")
    args = parser.parse_args()
    langs = ["en", "zh"] if args.lang == "both" else [args.lang]
    for lang in langs:
        out = build(lang)
        files = sorted(out.glob("*.png"))
        print(f"{lang}: {out.relative_to(ROOT)} — {len(files)} files")
        for path in files:
            print(f"   {path.name:22s} {path.stat().st_size // 1024:5d} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
