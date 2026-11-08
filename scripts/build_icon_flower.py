#!/usr/bin/env python3
"""Build the app icon from a design sheet, the way the current icon was made.

The sheet (e.g. the Option C upload) contains a large icon and a simplified
small variant. The large one feeds 1024/512/192/maskable/apple-touch; the small
one feeds the favicons, because a naive downscale of the detailed art turns to
mush at 32px.

Usage:
    python3 scripts/build_icon_flower.py --source design.jpg --prefix f

Requires:
    tools/venv-vtrace   python3.12 venv with `vtracer` (see tools/README.md)
    rsvg-convert, Pillow, scipy
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
VT_PYTHON = ROOT / "tools" / "venv-vtrace" / "bin" / "python"
FLOWER_MARK = ROOT / "samples" / "icons" / "bs512.png"
WORK = ROOT / "data" / "work" / "icon-build"

BACKGROUND = (243, 237, 222)
BADGE_FILL = (229, 240, 232)


def find_panels(image: Image.Image) -> tuple[Image.Image, Image.Image]:
    """Split the sheet into (large icon, small icon) by connected components."""
    a = np.asarray(image.convert("RGB")).astype(int)
    mask = np.abs(a - np.array(BACKGROUND)).sum(axis=2) > 40
    labels, count = ndimage.label(mask)
    if not count:
        raise SystemExit("no artwork found on the sheet")
    sizes = ndimage.sum(mask, labels, range(1, count + 1))
    order = np.argsort(sizes)[::-1]
    boxes = []
    for idx in order[:8]:
        component = labels == (idx + 1)
        ys, xs = np.nonzero(component)
        width, height = xs.max() - xs.min(), ys.max() - ys.min()
        if width < 120 or height < 120:
            continue
        boxes.append((xs.min(), ys.min(), xs.max(), ys.max(), width, height))
    if len(boxes) < 2:
        raise SystemExit("expected a large and a small icon on the sheet")
    boxes.sort(key=lambda b: -b[4] * b[5])
    large, small = boxes[0], boxes[1]
    pad = 6
    big = image.crop((large[0] - pad, large[1] - pad, large[2] + pad, large[3] + pad))
    tiny = image.crop((small[0] - pad, small[1] - pad, small[2] + pad, small[3] + pad))
    return big, tiny


def vectorise(image: Image.Image, target: Path) -> Path:
    """Colour-trace one icon with vtracer (3.12 venv: the 3.14 wheel segfaults)."""
    if not VT_PYTHON.exists():
        raise SystemExit(f"missing {VT_PYTHON}; run tools/setup_icon_tools.sh")
    WORK.mkdir(parents=True, exist_ok=True)
    source = WORK / "panel.png"
    image.save(source)
    script = (
        "import vtracer, sys\n"
        "vtracer.convert_image_to_svg_py(sys.argv[1], sys.argv[2], colormode='color',\n"
        "    hierarchical='stacked', mode='spline', filter_speckle=20,\n"
        "    color_precision=6, layer_difference=18, corner_threshold=60, path_precision=2)\n"
    )
    subprocess.run([str(VT_PYTHON), "-c", script, str(source), str(target)], check=True)
    return target


def silhouette(panel: Image.Image, erode: int = 2) -> Image.Image:
    """Binary alpha mask of the artwork, eroded so no background fringe survives."""
    a = np.asarray(panel.convert("RGB")).astype(int)
    mask = np.abs(a - np.array(BACKGROUND)).sum(axis=2) > 24
    mask = ndimage.binary_fill_holes(ndimage.binary_closing(mask, structure=np.ones((7, 7)), iterations=2))
    labels, count = ndimage.label(mask)
    sizes = ndimage.sum(mask, labels, range(1, count + 1))
    mask = labels == (int(np.argmax(sizes)) + 1)
    if erode:
        mask = ndimage.binary_erosion(mask, iterations=erode)
    return Image.fromarray((mask * 255).astype(np.uint8))


def knockout_background(svg: Path, panel: Image.Image, size: int) -> Image.Image:
    """Render the trace, then punch out everything outside the pin silhouette."""
    png = WORK / "render.png"
    subprocess.run(["rsvg-convert", "-w", str(size), str(svg), "-o", str(png)], check=True)
    icon = Image.open(png).convert("RGB")
    alpha = silhouette(panel).resize(icon.size, Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.6))
    rgba = icon.convert("RGBA")
    rgba.putalpha(alpha)
    return rgba


def replace_badge(icon: Image.Image) -> Image.Image:
    """Put the crisp brand flower back into the badge circle."""
    a = np.asarray(icon).astype(int)
    r, g, b, alpha = a[:, :, 0], a[:, :, 1], a[:, :, 2], a[:, :, 3]
    light = (b > 225) & (g > 230) & (r > 210) & (r < 248) & (alpha > 180)
    ys, xs = np.nonzero(light)
    if not len(xs):
        return icon
    cx = int((xs.min() + xs.max()) / 2)
    cy = int((ys.min() + ys.max()) / 2)
    radius = int((xs.max() - xs.min()) / 2)
    draw = ImageDraw.Draw(icon)
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=BADGE_FILL + (255,))
    flower = Image.open(FLOWER_MARK).convert("RGBA")
    side = int(radius * 1.55)
    flower = flower.resize((side, side), Image.LANCZOS)
    icon.alpha_composite(flower, (cx - side // 2, cy - side // 2 - int(radius * 0.05)))
    return icon


def square_master(icon: Image.Image, size: int = 1024, margin: float = 0.07,
                  opaque: bool = False) -> Image.Image:
    content = icon.crop(icon.getbbox())
    inner = int(size * (1 - 2 * margin))
    ratio = min(inner / content.width, inner / content.height)
    resized = content.resize((int(content.width * ratio), int(content.height * ratio)), Image.LANCZOS)
    canvas = Image.new("RGBA", (size, size), BACKGROUND + (255,) if opaque else (0, 0, 0, 0))
    canvas.alpha_composite(resized, ((size - resized.width) // 2, (size - resized.height) // 2))
    return canvas if opaque else canvas


def write_outputs(master: Image.Image, small: Image.Image, prefix: str) -> list[Path]:
    """Transparent where the platform allows it, opaque where it does not.

    1024/512/192 and the favicons keep alpha; maskable and apple-touch need a
    solid background or iOS/Android paint transparency black.
    """
    written = []
    for size, name in ((1024, f"icon-{prefix}-1024.png"), (512, f"icon-{prefix}-512.png"),
                       (192, f"icon-{prefix}-192.png")):
        master.resize((size, size), Image.LANCZOS).save(WEB / name)
        written.append(WEB / name)

    opaque = Image.new("RGB", (512, 512), BACKGROUND)
    safe = master.resize((410, 410), Image.LANCZOS)
    opaque.paste(safe, (51, 51), safe)
    opaque.save(WEB / f"icon-{prefix}-maskable-512.png")
    written.append(WEB / f"icon-{prefix}-maskable-512.png")

    apple = Image.new("RGB", (180, 180), BACKGROUND)
    icon180 = master.resize((180, 180), Image.LANCZOS)
    apple.paste(icon180, (0, 0), icon180)
    apple.save(WEB / f"apple-touch-{prefix}-180.png")
    written.append(WEB / f"apple-touch-{prefix}-180.png")

    favicons = []
    for size in (16, 32, 48):
        path = WEB / f"favicon-{prefix}-{size}.png"
        image = small.resize((size, size), Image.LANCZOS)
        image.save(path)
        favicons.append(image)
        written.append(path)
    favicons[-1].save(WEB / f"favicon-{prefix}.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    written.append(WEB / f"favicon-{prefix}.ico")
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="design sheet image")
    parser.add_argument("--prefix", default="f", help="filename suffix, e.g. 'f'")
    parser.add_argument("--keep-work", action="store_true")
    args = parser.parse_args()

    sheet = Image.open(args.source)
    big_panel, small_panel = find_panels(sheet)
    WORK.mkdir(parents=True, exist_ok=True)
    big_panel.save(WORK / "big-panel.png")
    small_panel.save(WORK / "small-panel.png")

    svg = vectorise(big_panel, WORK / "big.svg")
    traced = knockout_background(svg, big_panel, 1024)
    traced = replace_badge(traced)
    master = square_master(traced)

    # favicons come from the simplified small panel, not a downscale
    small_rgba = small_panel.convert("RGBA")
    small_rgba.putalpha(silhouette(small_panel, erode=1).filter(ImageFilter.GaussianBlur(0.5)))
    small = square_master(small_rgba, size=192, margin=0.04).resize((192, 192), Image.LANCZOS)

    written = write_outputs(master, small, args.prefix)
    for path in written:
        print(f"  wrote {path.name} ({path.stat().st_size} bytes)")
    if not args.keep_work:
        shutil.rmtree(WORK, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
