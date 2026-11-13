#!/usr/bin/env python3
"""Build a vertical (1080×1920) short from the promo assets.

    python3 scripts/make_reel.py            # writes promo/instagram/reel.mp4
    python3 scripts/make_reel.py --keep     # keep the intermediate frames

Five beats, each a still that is slowly zoomed by ffmpeg (Ken Burns):
hook → contrast → city close-up → species → end card. No screen recording, so
it renders in seconds and can be re-run whenever copy changes.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "promo" / "shots"
PLATES = ROOT / "web" / "plates"
ICON = ROOT / "web" / "icon-f-512.png"
FLOWER = ROOT / "promo" / "brand" / "botanisense-flower.png"
OUT = ROOT / "promo" / "instagram" / "reel.mp4"
WORK = ROOT / "data" / "work" / "reel"

W, H = 1080, 1920
CREAM = (247, 240, 225)
INK = (31, 45, 58)
MUTED = (108, 120, 131)
ACCENT = (184, 64, 22)
PINK = (153, 28, 106)
DOMAIN = "treecolors.botanisense.app"

ZH_BOLD = "/usr/share/fonts/wenquanyi/wqy-microhei/wqy-microhei.ttc"
ZH = "/usr/share/fonts/wenquanyi/wqy-microhei/wqy-microhei.ttc"
EN_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
EN = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def stats() -> dict:
    data = json.loads((ROOT / "web" / "species_stats.json").read_text())
    bay = {"berkeley", "concordca", "cupertino", "fremontca", "palo_alto", "sf",
           "san_jose", "sanleandroca", "mountain_view_ca"}
    rows = {c["slug"]: c for c in data["cities"] if c["slug"] in bay}
    fall = {slug: sum(e["count"] for e in c["species"]
                      if e.get("color_range") in ("red", "orange")) for slug, c in rows.items()}
    return {
        "bay_trees": sum(c["total"] for c in rows.values()),
        "bay_fall": sum(fall.values()),
        "sf": (rows["sf"]["total"], fall["sf"]),
        "cupertino": (rows["cupertino"]["total"], fall["cupertino"]),
        "mv": (rows["mountain_view_ca"]["total"], fall["mountain_view_ca"]),
    }


def cover(path: Path, size: tuple[int, int], radius: int = 28) -> Image.Image:
    image = Image.open(path).convert("RGB")
    target = size[0] / size[1]
    if image.width / image.height > target:
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


def brand(canvas: Image.Image) -> None:
    draw = ImageDraw.Draw(canvas)
    plate = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(plate).rounded_rectangle([64, 1742, 470, 1842], radius=18, fill=(255, 252, 245, 240))
    canvas.alpha_composite(plate.filter(ImageFilter.GaussianBlur(0.4)))
    logo = Image.open(ICON).convert("RGBA").resize((56, 56), Image.LANCZOS)
    canvas.alpha_composite(logo, (80, 1758))
    draw.text((148, 1756), "TreeColors", font=font(EN_BOLD, 30), fill=INK)
    draw.text((148, 1792), DOMAIN, font=font(EN_BOLD, 22), fill=ACCENT)

    tag = "a sense for plants"
    f = font(EN, 20)
    w = draw.textlength(tag, font=f)
    draw.text((1008 - w, 1766), tag, font=f, fill=MUTED)
    flower = Image.open(FLOWER).convert("RGBA")
    flower.thumbnail((24, 24), Image.LANCZOS)
    by = "by BotaniSense"
    bw = draw.textlength(by, font=f)
    canvas.alpha_composite(flower, (int(1008 - bw - flower.width - 10), 1800))
    draw.text((1008 - bw, 1800), by, font=f, fill=INK)


def frame_hook(s: dict) -> Image.Image:
    canvas = Image.new("RGBA", (W, H), CREAM + (255,))
    draw = ImageDraw.Draw(canvas)
    draw.text((72, 150), "湾区 · 秋色", font=font(ZH_BOLD, 30), fill=ACCENT)
    draw.text((72, 210), "湾区看秋色", font=font(ZH_BOLD, 108), fill=INK)
    draw.text((72, 340), "别整条街白走", font=font(ZH_BOLD, 108), fill=ACCENT)
    draw.text((72, 500), "点开一棵树，就知道它秋天会变成什么颜色", font=font(ZH, 34), fill=MUTED)
    canvas.alpha_composite(cover(SHOTS / "map-all-sf.png", (936, 1000), 30), (72, 600))
    brand(canvas)
    return canvas


def frame_contrast(s: dict) -> Image.Image:
    canvas = Image.new("RGBA", (W, H), CREAM + (255,))
    draw = ImageDraw.Draw(canvas)
    draw.text((72, 150), "同一片湾区，三倍的秋色", font=font(ZH_BOLD, 62), fill=INK)
    canvas.alpha_composite(cover(SHOTS / "map-all-sf.png", (936, 440), 24), (72, 290))
    draw.text((72, 748), "San Francisco", font=font(ZH_BOLD, 34), fill=INK)
    draw.text((72, 796), "15%", font=font(EN_BOLD, 104), fill=PINK)
    draw.text((320, 844), "的树会变色", font=font(ZH, 30), fill=MUTED)
    canvas.alpha_composite(cover(SHOTS / "cmp-cupertino.png", (936, 440), 24), (72, 960))
    draw.text((72, 1418), "Cupertino", font=font(ZH_BOLD, 34), fill=INK)
    draw.text((72, 1466), "50%", font=font(EN_BOLD, 104), fill=ACCENT)
    draw.text((320, 1514), "的树会变色", font=font(ZH, 30), fill=MUTED)
    draw.text((72, 1636), "绿的可以跳过，橙的是银杏", font=font(ZH, 28), fill=MUTED)
    brand(canvas)
    return canvas


def frame_city(s: dict) -> Image.Image:
    canvas = Image.new("RGBA", (W, H), CREAM + (255,))
    draw = ImageDraw.Draw(canvas)
    draw.text((72, 150), "城市特写", font=font(ZH_BOLD, 34), fill=ACCENT)
    draw.text((72, 210), "Mountain View", font=font(EN_BOLD, 84), fill=INK)
    total, fall = s["mv"]
    draw.text((72, 320), f"{total:,} 棵行道树，{fall:,} 棵会变色", font=font(ZH, 32), fill=MUTED)
    canvas.alpha_composite(cover(SHOTS / "mv-close.png", (936, 1080), 28), (72, 400))
    draw.text((72, 1520), "紫点会变色，橙点是银杏，绿点是常绿", font=font(ZH_BOLD, 32), fill=INK)
    brand(canvas)
    return canvas


def frame_species(s: dict) -> Image.Image:
    canvas = Image.new("RGBA", (W, H), CREAM + (255,))
    draw = ImageDraw.Draw(canvas)
    draw.text((72, 150), "常见树种都配了图示", font=font(ZH_BOLD, 34), fill=ACCENT)
    draw.text((72, 210), "出门前先认一眼", font=font(ZH_BOLD, 74), fill=INK)
    picks = ["pistacia_chinensis.png", "liquidambar_styraciflua.png",
             "ginkgo_biloba.png", "lagerstroemia_indica.png"]
    names = ["中国黄连木", "枫香", "银杏", "紫薇"]
    size, gap = 440, 56
    for i, (file, name) in enumerate(zip(picks, names)):
        col, row = i % 2, i // 2
        x = 72 + col * (size + gap)
        y = 340 + row * (size + 90)
        canvas.alpha_composite(cover(PLATES / file, (size, size), 24), (x, y))
        draw.text((x, y + size + 12), name, font=font(ZH_BOLD, 30), fill=INK)
    brand(canvas)
    return canvas


def frame_end(s: dict) -> Image.Image:
    canvas = Image.new("RGBA", (W, H), CREAM + (255,))
    draw = ImageDraw.Draw(canvas)
    draw.text((72, 240), "找秋色。", font=font(ZH_BOLD, 96), fill=INK)
    draw.text((72, 370), "走过去。", font=font(ZH_BOLD, 96), fill=ACCENT)
    draw.text((72, 520), f"湾区 {s['bay_fall']:,} 棵会变色的树，每一棵都有位置",
              font=font(ZH, 34), fill=MUTED)
    draw.text((72, 600), "免费，不用注册", font=font(ZH, 30), fill=MUTED)
    draw.text((72, 700), DOMAIN, font=font(EN_BOLD, 46), fill=ACCENT)
    canvas.alpha_composite(cover(SHOTS / "map-all-sj.png", (936, 780), 30), (72, 820))
    brand(canvas)
    return canvas


BEATS = [("01-hook", frame_hook, 3.2), ("02-contrast", frame_contrast, 3.2),
         ("03-city", frame_city, 3.0), ("04-species", frame_species, 3.0),
         ("05-end", frame_end, 3.4)]


def render_frames(s: dict, work: Path) -> list[tuple[Path, float]]:
    work.mkdir(parents=True, exist_ok=True)
    out = []
    for name, builder, seconds in BEATS:
        path = work / f"{name}.png"
        builder(s).convert("RGB").save(path)
        out.append((path, seconds))
    return out


def encode(frames: list[tuple[Path, float]], target: Path) -> None:
    """Slow Ken Burns on each still, then cross-fade them together."""
    inputs, filters, labels = [], [], []
    fade = 0.5
    for index, (path, seconds) in enumerate(frames):
        inputs += ["-loop", "1", "-t", f"{seconds}", "-i", str(path)]
        # zoom from 1.0 to 1.06 over the clip, always filling the frame
        filters.append(
            f"[{index}:v]scale=1350:2400,zoompan=z='min(zoom+0.0009,1.06)':"
            f"d={int(seconds*30)}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"s={W}x{H}:fps=30,setsar=1[v{index}]"
        )
        labels.append(f"[v{index}]")

    chain = labels[0]
    offset = 0.0
    for index in range(1, len(frames)):
        offset += frames[index - 1][1] - fade
        out = f"[x{index}]"
        filters.append(f"{chain}{labels[index]}xfade=transition=fade:duration={fade}:offset={offset:.2f}{out}")
        chain = out

    script = WORK / "filter.txt"
    script.write_text(";\n".join(filters))
    total = sum(seconds for _, seconds in frames) - fade * (len(frames) - 1)
    subprocess.run([
        "ffmpeg", "-y", *inputs,
        "-filter_complex_script", str(script),
        "-map", chain, "-t", f"{total:.2f}", "-r", "30",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(target),
    ], check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keep", action="store_true")
    args = parser.parse_args()
    frames = render_frames(stats(), WORK)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    encode(frames, OUT)
    size = OUT.stat().st_size / 1024 / 1024
    print(f"wrote {OUT.relative_to(ROOT)} ({size:.1f} MB)")
    if not args.keep:
        shutil.rmtree(WORK, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
