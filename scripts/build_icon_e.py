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
LEAF = "#d99b2b"
LEAF_DARK = "#b87c1e"
RING = "#e8dcc2"


OAK_SVG = ROOT / "samples" / "icons" / "oak_leaf_cc0.svg"
OAK_VIEWBOX = (68.185349, 112.6434)  # width, height of the source drawing


def _leaf_geometry(cx: float, cy: float, height: float) -> tuple[str, str]:
    """Return (svg transform, outline path) for the CC0 bur oak leaf."""
    import xml.etree.ElementTree as ET

    ns = {"svg": "http://www.w3.org/2000/svg"}
    root = ET.fromstring(OAK_SVG.read_text())
    paths = root.findall(".//svg:path", ns)
    group = root.find(".//svg:g", ns)
    inner = group.get("transform", "") if group is not None else ""

    src_w, src_h = OAK_VIEWBOX
    scale = height / src_h
    width = src_w * scale
    x = cx - width / 2
    y = cy - height / 2
    transform = f"translate({x:.2f} {y:.2f}) scale({scale:.4f}) {inner}"
    return transform, paths[0].get("d")


def leaf_shapes(cx: float, cy: float, height: float) -> str:
    """Bur oak leaf (CC0) with veins drawn inside its own outline.

    The source drawing carries a second path for veins that sits on a different
    scale, which is why copying it produced a drifting midrib. The outline is
    kept and the veins are generated here, clipped to the leaf shape.
    """
    transform, outline = _leaf_geometry(cx, cy, height)

    # Rasterise the outline once to get its real bounds in icon coordinates.
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

    left, right = x0, x1
    top, bottom = y0, y1
    mid_x = (left + right) / 2
    stem_top = bottom - (bottom - top) * 0.10

    veins = [f'<path d="M {mid_x:.1f},{top + 6:.1f} L {mid_x:.1f},{stem_top:.1f}"/>']
    for fraction in (0.12, 0.26, 0.40, 0.54, 0.68, 0.80):
        y = top + (stem_top - top) * fraction
        for side in (-1, 1):
            end_x = mid_x + side * (right - left) * 0.30
            end_y = y - (stem_top - top) * 0.10
            veins.append(
                f'<path d="M {mid_x:.1f},{y:.1f} Q {mid_x + side * (right - left) * 0.13:.1f},'
                f'{y - (stem_top - top) * 0.05:.1f} {end_x:.1f},{end_y:.1f}"/>'
            )

    return (
        f'<defs><clipPath id="leafClip">'
        f'<path d="{outline}" transform="{transform}"/></clipPath></defs>'
        f'<g transform="{transform}">'
        f'<path d="{outline}" fill="{LEAF}" stroke="{LEAF_DARK}" stroke-width="0.9" stroke-linejoin="round"/>'
        f'</g>'
        f'<g clip-path="url(#leafClip)" fill="none" stroke="{LEAF_DARK}" '
        f'stroke-width="2.2" stroke-linecap="round" opacity="0.75">'
        + "".join(veins)
        + "</g>"
    )


def build_svg(with_badge: bool, background: str | None, pad: float = 0.0) -> str:
    flower = base64.b64encode(FLOWER.read_bytes()).decode()
    leaf = leaf_shapes(256, 190, 176)
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
    <circle cx="392" cy="104" r="52" fill="{CREAM}" stroke="{PIN_LIGHT}" stroke-width="6"/>
    <clipPath id="badgeClip"><circle cx="392" cy="104" r="45"/></clipPath>
    <image x="352" y="58" width="82" height="92" preserveAspectRatio="xMidYMid meet"
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
    <path d="M106 196 A150 150 0 1 1 406 196 C406 300 300 380 256 470 C212 380 106 300 106 196 Z"
          fill="{PIN_LIGHT}" clip-path="url(#leftHalf)"/>
    <path d="M106 196 A150 150 0 1 1 406 196 C406 300 300 380 256 470 C212 380 106 300 106 196 Z"
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
