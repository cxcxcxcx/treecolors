#!/usr/bin/env python3
"""Build the Option E app icon (map pin + oak leaf + BotaniSense badge).

Vector source of truth, rendered with rsvg-convert. Produces:
    out/icon-e-1024.png          master, transparent background
    out/icon-e-512.png           PWA any
    out/icon-e-192.png           PWA any
    out/icon-e-maskable-512.png  safe-zone padded, opaque
    out/apple-touch-180.png      opaque cream square
    out/favicon-32.png / 16.png  pin + leaf only (badge removed at tiny sizes)
    out/favicon.ico              multi-size

Usage: python3 scripts/build_icon_e.py
"""

from __future__ import annotations

import base64
import math
import subprocess
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "samples" / "icons" / "e"
FLOWER = ROOT / "samples" / "icons" / "bs512.png"

PIN_LIGHT = "#c8552a"
PIN_DARK = "#a8401f"
CREAM = "#f8f1de"
LEAF = "#e6a639"
LEAF_DARK = "#c0872c"
RING = "#e8dcc2"


OAK_SVG = ROOT / "assets" / "iconography" / "oak_leaf_traced.svg"  # potrace of the Option E leaf


def _mask_for(outline: str, transform: str) -> "Image.Image":
    probe = (f'<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">'
             f'<g transform="{transform}"><path d="{outline}" fill="#000"/></g></svg>')
    probe_path = OUT / "_probe.svg"
    probe_path.write_text(probe)
    subprocess.run(["rsvg-convert", "-w", "512", "-h", "512", "-o",
                    str(OUT / "_probe.png"), str(probe_path)], check=True)
    probe_path.unlink(missing_ok=True)
    mask = Image.open(OUT / "_probe.png").convert("RGBA").split()[-1]
    (OUT / "_probe.png").unlink(missing_ok=True)
    return mask


def _principal_angle(mask: "Image.Image") -> float:
    """Angle of the leaf's long axis, in degrees, measured from the x axis."""
    import numpy as np

    ys, xs = np.nonzero(np.array(mask) > 40)
    xs = xs.astype(float) - xs.mean()
    ys = ys.astype(float) - ys.mean()
    mu20 = (xs * xs).mean()
    mu02 = (ys * ys).mean()
    mu11 = (xs * ys).mean()
    return math.degrees(0.5 * math.atan2(2 * mu11, mu20 - mu02))


def _leaf_geometry(cx: float, cy: float, height: float) -> tuple[str, str]:
    """Return (transform, outline) with the leaf straightened automatically.

    The source drawings all lean a little; measuring the mask's principal axis
    beats guessing a rotation constant, and the narrow end is flipped down so
    the stem always points at the bottom.
    """
    import xml.etree.ElementTree as ET
    import numpy as np

    ns = {"svg": "http://www.w3.org/2000/svg"}
    root = ET.fromstring(OAK_SVG.read_text())
    paths = root.findall(".//svg:path", ns)
    inner = paths[0].get("transform", "") if paths else ""
    if not inner:
        group = root.find(".//svg:g", ns)
        inner = group.get("transform", "") if group is not None else ""
    outline = paths[0].get("d")

    box = (root.get("viewBox") or "").replace(",", " ").split()
    if len(box) == 4:
        src_w, src_h = float(box[2]), float(box[3])
        vb_x, vb_y = float(box[0]), float(box[1])
    else:
        src_w, src_h = float(root.get("width", 512)), float(root.get("height", 512))
        vb_x = vb_y = 0.0
    scale = height / src_h

    def build(angle: float) -> str:
        return (f"translate({cx:.2f} {cy:.2f}) rotate({angle:.2f}) scale({scale:.4f}) "
                f"translate({-(vb_x + src_w / 2):.2f} {-(vb_y + src_h / 2):.2f}) {inner}")

    flat = build(0)
    mask = _mask_for(outline, flat)
    angle = 90 - _principal_angle(mask)  # bring the long axis to vertical

    upright = build(angle)
    mask = _mask_for(outline, upright)
    ys, xs = np.nonzero(np.array(mask) > 40)
    if not len(xs):
        return upright, outline
    # width of the top vs bottom fifth tells us which end is the stem
    span = ys.max() - ys.min()
    top_band = xs[ys < ys.min() + span * 0.2]
    bottom_band = xs[ys > ys.max() - span * 0.2]
    top_w = top_band.max() - top_band.min() if len(top_band) else 0
    bottom_w = bottom_band.max() - bottom_band.min() if len(bottom_band) else 0
    if bottom_w > top_w:  # broad end at the bottom -> flip
        upright = build(angle + 180)
    return upright, outline


def leaf_shapes(cx: float, cy: float, height: float) -> str:
    """Solid oak leaf silhouette with a clean stem and clipped veins.

    The source drawing has a thin, slightly detached stem, so the leaf body is
    clipped just above it and a solid stem is drawn underneath.
    """
    transform, outline = _leaf_geometry(cx, cy, height)

    probe = (f'<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">'
             f'<g transform="{transform}"><path d="{outline}" fill="#000"/></g></svg>')
    probe_path = OUT / "_probe.svg"
    probe_path.write_text(probe)
    subprocess.run(["rsvg-convert", "-w", "512", "-h", "512", "-o",
                    str(OUT / "_probe.png"), str(probe_path)], check=True)
    mask = Image.open(OUT / "_probe.png").convert("RGBA").split()[-1]
    x0, y0, x1, y1 = mask.getbbox()
    probe_path.unlink(missing_ok=True)
    (OUT / "_probe.png").unlink(missing_ok=True)

    left, right, top, bottom = x0, x1, y0, y1
    mid_x = (left + right) / 2
    body_bottom = bottom - (bottom - top) * 0.07
    stem_w = max(8.0, (right - left) * 0.06)
    stem_top = body_bottom - (bottom - top) * 0.06
    stem_bottom = bottom + (bottom - top) * 0.05

    veins = [f'<path d="M {mid_x:.1f},{top + 6:.1f} L {mid_x:.1f},{body_bottom - 4:.1f}"/>']
    for fraction in (0.24, 0.44, 0.62, 0.78):
        y = top + (body_bottom - top) * fraction
        for side in (-1, 1):
            veins.append(
                f'<path d="M {mid_x:.1f},{y:.1f} Q {mid_x + side * (right - left) * 0.10:.1f},'
                f'{y - (body_bottom - top) * 0.06:.1f} '
                f'{mid_x + side * (right - left) * 0.25:.1f},{y - (body_bottom - top) * 0.14:.1f}"/>'
            )

    return (
        f'<defs><clipPath id="leafClip"><path d="{outline}" transform="{transform}"/></clipPath></defs>'
        f'<g transform="{transform}">'
        f'<path d="{outline}" fill="{LEAF}" stroke="{LEAF}" stroke-width="5" stroke-linejoin="round"/>'
        f'<path d="{outline}" fill="none" stroke="{LEAF_DARK}" stroke-width="1.2" stroke-linejoin="round"/>'
        f'</g>'
        f'<g clip-path="url(#leafClip)" fill="none" stroke="{LEAF_DARK}" stroke-width="1.7" '
        f'stroke-linecap="round" opacity="0.9">'
        + "".join(veins) + "</g>"
    )


def build_svg(with_badge: bool, background: str | None, pad: float = 0.0) -> str:
    flower = base64.b64encode(FLOWER.read_bytes()).decode()
    leaf = leaf_shapes(256, 190, 202)
    # midrib + side veins
    veins = ['<path d="M256 118 L256 268" stroke="%s" stroke-width="3.2" stroke-linecap="round"/>' % LEAF_DARK]
    for offset in (18, 40, 62):
        veins.append(
            f'<path d="M256 {128 + offset} Q {256 - 26} {136 + offset} {256 - 46} {150 + offset}" '
            f'stroke="{LEAF_DARK}" stroke-width="2.6" fill="none" stroke-linecap="round"/>'
        )
        veins.append(
            f'<path d="M256 {128 + offset} Q {256 + 26} {136 + offset} {256 + 46} {150 + offset}" '
            f'stroke="{LEAF_DARK}" stroke-width="2.6" fill="none" stroke-linecap="round"/>'
        )

    badge = ""
    if with_badge:
        badge = f'''
    <circle cx="394" cy="100" r="60" fill="{CREAM}" stroke="{PIN_LIGHT}" stroke-width="6"/>
    <clipPath id="badgeClip"><circle cx="394" cy="100" r="52"/></clipPath>
    <image x="350" y="46" width="88" height="104" preserveAspectRatio="xMidYMid meet"
           clip-path="url(#badgeClip)" xlink:href="data:image/png;base64,{flower}"/>'''

    bg = ""
    if background:
        bg = f'<rect x="0" y="0" width="512" height="512" fill="{background}"/>'

    scale = 1 - 2 * pad
    transform = f'translate({256 * pad * 2} {256 * pad * 2}) scale({scale})' if pad else ""

    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="512" height="512" viewBox="0 0 512 512">
  {bg}
  <g transform="{transform}">
    <defs>
      <clipPath id="leftHalf"><rect x="0" y="0" width="256" height="512"/></clipPath>
      <clipPath id="rightHalf"><rect x="256" y="0" width="256" height="512"/></clipPath>
    </defs>
    <path d="M100 196 A156 156 0 1 1 412 196 C412 302 306 384 256 472 C206 384 100 302 100 196 Z"
          fill="{PIN_LIGHT}" clip-path="url(#leftHalf)"/>
    <path d="M100 196 A156 156 0 1 1 412 196 C412 302 306 384 256 472 C206 384 100 302 100 196 Z"
          fill="{PIN_DARK}" clip-path="url(#rightHalf)"/>
    <circle cx="256" cy="196" r="112" fill="{CREAM}"/>
    <circle cx="256" cy="196" r="112" fill="none" stroke="{RING}" stroke-width="4"/>
    {leaf}

    {badge}
  </g>
</svg>'''


def render(svg: str, size: int, target: Path) -> None:
    svg_path = OUT / "_tmp.svg"
    svg_path.write_text(svg)
    subprocess.run(["rsvg-convert", "-w", str(size), "-h", str(size),
                    "-o", str(target), str(svg_path)], check=True)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    master = build_svg(with_badge=True, background=None)
    render(master, 1024, OUT / "icon-e-1024.png")
    render(master, 512, OUT / "icon-e-512.png")
    render(master, 192, OUT / "icon-e-192.png")

    maskable = build_svg(with_badge=True, background=CREAM, pad=0.12)
    render(maskable, 512, OUT / "icon-e-maskable-512.png")

    apple = build_svg(with_badge=True, background=CREAM)
    render(apple, 180, OUT / "apple-touch-180.png")

    small = build_svg(with_badge=False, background=None)
    render(small, 48, OUT / "favicon-48.png")
    render(small, 32, OUT / "favicon-32.png")
    render(small, 16, OUT / "favicon-16.png")

    icons = [Image.open(OUT / name).convert("RGBA")
             for name in ("favicon-16.png", "favicon-32.png", "favicon-48.png")]
    icons[-1].save(OUT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])

    (OUT / "_tmp.svg").unlink(missing_ok=True)
    for path in sorted(OUT.glob("*")):
        print(path.name, path.stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
