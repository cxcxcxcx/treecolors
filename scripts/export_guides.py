#!/usr/bin/env python3
"""Export numbers and images for the fall-colour guides on botanisense.app.

    python3 scripts/export_guides.py
    python3 scripts/export_guides.py --web-home /path/to/web_home

The guide pages live in the BotaniSense marketing site (Astro, `web_home/`),
next to the watering guide, so they share its layout. This script is the only
bridge: it writes `src/data/fall-colors.json` (all numbers, from
web/species_stats.json — never typed by hand) and the images under
`public/imgs/fall-colors/`. Rebuild and deploy web_home afterwards
(`push_botaniq_home.sh`).
"""

from __future__ import annotations

import argparse
import json
import math
import random
import re
import time
import urllib.request
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
DEFAULT_WEB_HOME = Path("./web_home")

# Region membership by city name as it appears in species_stats.json.
# Santa Clara County is left out: its inventory may overlap the cities in it.
# Santa Clara (city) is left out too: its open inventory is a small, plum-heavy
# sample (~10k trees) that ranks it far above its neighbours.
REGIONS = {
    "bay": ["San Francisco", "Berkeley", "Concord", "Fremont", "San Leandro",
            "San Mateo", "Burlingame", "Brisbane", "Palo Alto", "Mountain View",
            "Cupertino", "San Jose", "Milpitas", "Los Gatos"],
    "vancouver": ["Vancouver"],
    "la": ["Los Angeles"],
    "san_diego": ["San Diego"],
}
# Small inventories swing wildly in share; keep them out of the city table.
MIN_TABLE_TREES = 5000

# Spots: for each headline tree, the densest patches of it in the Bay, on a grid of CELL
# degrees (~440 m), at most one per city. Each gets a map snapshot drawn like the app with
# that species selected. Centroids are reverse-geocoded once with OSM Nominatim.
CELL = 0.004
SPOT_GROUPS = {"Chinese pistache": "pistache", "sweetgum": "sweetgum", "maple": "maple", "ginkgo": "ginkgo"}
SPOTS_PER_GROUP = 3
QUIET_MIN_TREES = 300  # a "quiet" SF cell must be well planted, just not with turning trees
GEOJSON = ROOT / "data" / "output" / "geojson"
WORK = ROOT / "data" / "work" / "guides"
GEOCODE_CACHE = WORK / "geocode_cache.json"
NOMINATIM = "https://nominatim.openstreetmap.org/reverse?format=jsonv2&zoom=17&lat={lat}&lon={lng}"
OSM_TILE = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
USER_AGENT = "BotaniSense-guides/1.0 (https://botanisense.app)"
# Snapshot: VIEW css px of zoom-ZOOM map, written at 2x. Dot size follows the app's
# circle-radius curve at that zoom; the selected species at 0.95 opacity as in the app,
# everything else faint (the app uses 0.05; a little more keeps the streets readable).
ZOOM, VIEW, SCALE = 16, 400, 2
DOT_RADIUS = 3 + (ZOOM - 14) / 3 * 5
SELECTED_ALPHA, OTHER_ALPHA = 0.95, 0.18
# Hero: the whole Bay at zoom 11, every street tree in its map colour, the base map washed
# out so the dots carry the picture. Labelled cities get their share from the same data.
HERO_ZOOM, HERO_BOUNDS = 11, (-122.53, 37.20, -121.73, 37.915)  # w, s, e, n
# Labelled cities and which side of the city the label sits on, so it covers empty ground.
HERO_LABELS = {"sf": "below", "berkeley": "right", "san_mateo_ca": "left", "palo_alto": "left",
               "fremontca": "right", "cupertino": "left", "san_jose": "center"}
FONT_BOLD = "/usr/share/fonts/noto/NotoSans-Bold.ttf"

# City inventories name the same tree a dozen ways ("Crepe Myrtle", "Muskogee crape myrtle",
# "Lagerstroemia indica"). For prose, fold them into the street tree a visitor would recognise.
# First match wins, on whole words of the raw species name plus its first common name.
TREE_GROUPS = [
    (r"pistacia|pistache", "Chinese pistache"), (r"liquidambar|sweetgum", "sweetgum"),
    (r"ginkgo|maidenhair", "ginkgo"), (r"lagerstroemia|crape|crepe|crapemyrtle", "crape myrtle"),
    (r"cherry", "flowering cherry"), (r"plum|cerasifera", "flowering plum"), (r"prunus", "flowering cherry"),
    (r"pyrus|pear", "ornamental pear"), (r"acer|maple", "maple"), (r"ulmus|elm", "elm"),
    (r"zelkova", "zelkova"), (r"quercus|oak", "oak"), (r"platanus|plane|sycamore", "plane tree"),
    (r"fraxinus|ash", "ash"), (r"koelreuteria|goldenrain|goldenraintree", "goldenrain tree"),
    (r"liriodendron|tulip", "tulip tree"), (r"triadica|sapium|tallow", "Chinese tallow"),
    (r"cercis|redbud", "redbud"), (r"nyssa|tupelo", "tupelo"),
]

PLATES = ["pistacia_chinensis", "liquidambar_styraciflua", "acer_rubrum", "ginkgo_biloba", "lagerstroemia_indica"]
SHOTS = {"sf": "map-all-sf.png", "cupertino": "cmp-cupertino.png"}


def fall_of(city: dict) -> int:
    return sum(e["count"] for e in city["species"] if e.get("color_range") in ("red", "orange"))


def city_row(city: dict) -> dict:
    fall = fall_of(city)
    return {"slug": city["slug"], "name": city["name"].split(",")[0], "total": city["total"],
            "fall": fall, "pct": round(100 * fall / city["total"])}


def evergreens(city: dict, n: int = 3) -> list[str]:
    green = sorted((e for e in city["species"] if e.get("color_range") == "green"),
                   key=lambda e: -e["count"])[:n]
    return [(e.get("common") or e["species"]).lower() for e in green]


class Geocoder:
    """Nominatim reverse geocoding, 1 request/second, cached by rounded coordinate."""

    def __init__(self) -> None:
        self.cache = json.loads(GEOCODE_CACHE.read_text()) if GEOCODE_CACHE.exists() else {}
        self.last = 0.0

    def address(self, lat: float, lng: float, zoom: int) -> dict:
        key = f"{lat:.5f},{lng:.5f}" + ("" if zoom == 17 else f":{zoom}")
        if key not in self.cache:
            time.sleep(max(0.0, 1.1 - (time.time() - self.last)))
            url = NOMINATIM.format(lat=lat, lng=lng).replace("zoom=17", f"zoom={zoom}")
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=30) as resp:
                self.cache[key] = json.load(resp).get("address", {})
            self.last = time.time()
            GEOCODE_CACHE.parent.mkdir(parents=True, exist_ok=True)
            GEOCODE_CACHE.write_text(json.dumps(self.cache, indent=1, ensure_ascii=False))
        return self.cache[key]

    def place(self, lat: float, lng: float) -> dict:
        area = lambda a: a.get("neighbourhood") or a.get("quarter") or a.get("suburb")  # noqa: E731
        a = self.address(lat, lng, 17)
        return {"road": a.get("road"), "area": area(a) or area(self.address(lat, lng, 14))}


def tree_group(props: dict) -> str:
    common = (props.get("common_names") or [""])[0]
    text = f"{props['species']} {common}".lower()
    for pattern, label in TREE_GROUPS:
        if re.search(rf"\b(?:{pattern})\b", text):
            return label
    return (common or props["species"]).lower()


def load_trees(slugs: list[str]) -> list[tuple]:
    """(lng, lat, rgb, group or None, turns, slug) for every tree in these cities."""
    trees = []
    for slug in slugs:
        for f in json.loads((GEOJSON / f"trees_{slug}.geojson").read_text())["features"]:
            p = f["properties"]
            x, y = f["geometry"]["coordinates"][:2]
            turns = p.get("color_range") in ("red", "orange")
            try:
                rgb = ImageColor.getrgb(p.get("color") or "#888888")[:3]
            except ValueError:
                rgb = (136, 136, 136)
            trees.append((x, y, rgb, tree_group(p) if turns else None, turns, slug))
    return trees


def world_px(lng: float, lat: float, zoom: int = ZOOM) -> tuple[float, float]:
    """Web-Mercator pixel position at `zoom` (256 px tiles)."""
    n = 256 * 2 ** zoom
    return (lng + 180) / 360 * n, (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n


def tile(x: int, y: int, zoom: int = ZOOM) -> Image.Image:
    path = WORK / "tiles" / str(zoom) / str(x) / f"{y}.png"
    if not path.exists():
        req = urllib.request.Request(OSM_TILE.format(z=zoom, x=x, y=y), headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        time.sleep(0.2)
    return Image.open(path).convert("RGB")


def snapshot(trees: list[tuple], lat: float, lng: float, group: str | None, out: Path,
             color: tuple | None = None) -> dict:
    """Draw the map around (lat, lng) like the app, with `group` selected. Counts what is in view.
    `color` paints every selected tree the same, so one tree reads as one color across snapshots."""
    cx, cy = world_px(lng, lat)
    x0, y0 = cx - VIEW / 2, cy - VIEW / 2
    base = Image.new("RGB", (VIEW + 512, VIEW + 512))
    tx0, ty0 = int(x0 // 256), int(y0 // 256)
    for tx in range(tx0, int((x0 + VIEW) // 256) + 1):
        for ty in range(ty0, int((y0 + VIEW) // 256) + 1):
            base.paste(tile(tx, ty), ((tx - tx0) * 256, (ty - ty0) * 256))
    ox, oy = x0 - tx0 * 256, y0 - ty0 * 256
    size = VIEW * SCALE
    base = base.crop((round(ox), round(oy), round(ox) + VIEW, round(oy) + VIEW)).resize((size, size), Image.LANCZOS)

    ss = 2  # supersample the dots, then scale down for smooth edges
    layers = {k: Image.new("RGBA", (size * ss, size * ss)) for k in ("other", "selected")}
    pens = {k: ImageDraw.Draw(v) for k, v in layers.items()}
    r = DOT_RADIUS * SCALE * ss
    count = {"trees": 0, "turn": 0, "selected": 0}
    for x, y, rgb, g, turns, _ in trees:
        px, py = world_px(x, y)
        u, v = (px - x0) * SCALE * ss, (py - y0) * SCALE * ss
        if not (-r <= u <= size * ss + r and -r <= v <= size * ss + r):
            continue
        if 0 <= u < size * ss and 0 <= v < size * ss:
            count["trees"] += 1
            count["turn"] += turns
            count["selected"] += g == group
        layer = "selected" if group is None or g == group else "other"
        fill = color if color and g == group else rgb
        pens[layer].ellipse((u - r, v - r, u + r, v + r), fill=fill + (255,))
    img = base.convert("RGBA")
    for name, alpha in (("other", OTHER_ALPHA), ("selected", SELECTED_ALPHA if group else 0.8)):
        layer = layers[name].resize((size, size), Image.LANCZOS)
        layer.putalpha(layer.getchannel("A").point(lambda a, k=alpha: round(a * k)))
        img = Image.alpha_composite(img, layer)
    pen = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=11 * SCALE)
    label = "© OpenStreetMap contributors"
    w = pen.textlength(label, font=font)
    pen.rectangle((size - w - 12 * SCALE, size - 16 * SCALE, size, size), fill=(255, 255, 255, 200))
    pen.text((size - w - 6 * SCALE, size - 15 * SCALE), label, font=font, fill=(60, 60, 60, 255))
    out.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out, quality=78)
    return count


def hero(trees: list[tuple], labels: dict, out: Path) -> None:
    """The whole Bay, every tree in its map colour, a few cities labelled with their share."""
    w, s, e, n = HERO_BOUNDS
    x0, y0 = world_px(w, n, HERO_ZOOM)
    x1, y1 = world_px(e, s, HERO_ZOOM)
    vw, vh = round(x1 - x0), round(y1 - y0)
    tx0, ty0 = int(x0 // 256), int(y0 // 256)
    base = Image.new("RGB", ((int(x1 // 256) - tx0 + 1) * 256, (int(y1 // 256) - ty0 + 1) * 256))
    for tx in range(tx0, int(x1 // 256) + 1):
        for ty in range(ty0, int(y1 // 256) + 1):
            base.paste(tile(tx, ty, HERO_ZOOM), ((tx - tx0) * 256, (ty - ty0) * 256))
    ox, oy = round(x0 - tx0 * 256), round(y0 - ty0 * 256)
    base = base.crop((ox, oy, ox + vw, oy + vh)).resize((vw * SCALE, vh * SCALE), Image.LANCZOS)
    base = Image.blend(base.convert("L").convert("RGB"), Image.new("RGB", base.size, (250, 248, 244)), 0.55)

    ss, r = 2, 1.4 * SCALE * 2
    dots = Image.new("RGBA", (vw * SCALE * ss, vh * SCALE * ss))
    pen = ImageDraw.Draw(dots)
    where: dict = defaultdict(list)
    order = list(range(len(trees)))
    random.Random(0).shuffle(order)  # file order clusters species; drawn in it, the last one wins
    for x, y, rgb, _, _, slug in (trees[i] for i in order):
        px, py = world_px(x, y, HERO_ZOOM)
        u, v = (px - x0) * SCALE * ss, (py - y0) * SCALE * ss
        if 0 <= u < dots.width and 0 <= v < dots.height:
            pen.ellipse((u - r, v - r, u + r, v + r), fill=rgb + (255,))
            where[slug].append((u / ss, v / ss))
    dots = dots.resize(base.size, Image.LANCZOS)
    dots.putalpha(dots.getchannel("A").point(lambda a: round(a * 0.85)))
    img = Image.alpha_composite(base.convert("RGBA"), dots)

    # The hero is shown ~300 css px wide, so labels are sized to the image, not to the map:
    # city name over its share, kept inside the frame.
    pen = ImageDraw.Draw(img)
    small = ImageFont.load_default(size=11 * SCALE)
    name_font, pct_font = (ImageFont.truetype(FONT_BOLD, round(img.width / k)) for k in (26, 15))
    for slug, (name, pct) in labels.items():
        pts = where.get(slug)
        if not pts:
            continue
        us, vs = sorted(p[0] for p in pts), sorted(p[1] for p in pts)
        u, v = us[len(us) // 2], vs[len(vs) // 2]
        half = max(pen.textlength(name, font=name_font), pen.textlength(pct, font=pct_font)) / 2 + img.width / 60
        tall = (name_font.size + pct_font.size) / 2 + img.width / 80
        side = HERO_LABELS[slug]
        # bounding box without the stray outliers (5th to 95th percentile)
        lo, hi = (lambda a: (a[len(a) // 20], a[-len(a) // 20 - 1]))(us), (lambda a: (a[len(a) // 20], a[-len(a) // 20 - 1]))(vs)
        u = {"left": lo[0] - half, "right": lo[1] + half}.get(side, u)
        v = {"below": hi[1] + tall}.get(side, v)
        u = min(max(u, half), img.width - half)
        v = min(max(v, tall), img.height - tall)
        for text, font, dy in ((name, name_font, -0.55), (pct, pct_font, 0.45)):
            pen.text((u, v + dy * font.size), text, font=font, anchor="mm", fill=(40, 34, 28, 255),
                     stroke_width=round(font.size / 6), stroke_fill=(255, 255, 255, 240))
    label = "© OpenStreetMap contributors"
    tw = pen.textlength(label, font=small)
    pen.rectangle((img.width - tw - 12 * SCALE, img.height - 16 * SCALE, img.width, img.height), fill=(255, 255, 255, 200))
    pen.text((img.width - tw - 6 * SCALE, img.height - 15 * SCALE), label, font=small, fill=(60, 60, 60, 255))
    img = img.convert("RGB")
    img.thumbnail((1400, 1600), Image.LANCZOS)  # shown at most ~360 css px wide, so 2x plus margin
    img.save(out, quality=80)
    print(f"hero: {img.width}x{img.height} -> {out.name}")


def spots(trees: list[tuple], names: dict, img_dir: Path) -> tuple[list[dict], dict]:
    """Densest patches of each headline tree (one per city), and SF's quietest planted patch."""
    geo = Geocoder()
    cells: dict = defaultdict(lambda: [0, 0.0, 0.0])  # (group, slug, i, j) -> n, sum lng, sum lat
    sf: dict = defaultdict(lambda: [0, 0])  # (i, j) -> trees, turning
    totals = Counter(t[3] for t in trees if t[3])
    # A group can span species (red and Japanese maple), so a snapshot paints the whole group in the
    # color most of its trees carry Bay-wide; species_color() keeps each species one color everywhere.
    colors: dict = defaultdict(Counter)
    for t in trees:
        if t[3] in SPOT_GROUPS:
            colors[t[3]][t[2]] += 1
    for x, y, _, g, turns, slug in trees:
        ij = (int(y // CELL), int(x // CELL))
        if g in SPOT_GROUPS:
            c = cells[(g, slug) + ij]
            c[0] += 1
            c[1] += x
            c[2] += y
        if slug == "sf":
            sf[ij][0] += 1
            sf[ij][1] += turns
    out = []
    for group, key in SPOT_GROUPS.items():
        ranked = sorted(((k, v) for k, v in cells.items() if k[0] == group), key=lambda kv: -kv[1][0])
        places, used = [], set()
        for (_, slug, *_), (n, sx, sy) in ranked:
            if slug in used:
                continue
            used.add(slug)
            lat, lng = sy / n, sx / n
            image = f"spot-{key}-{len(places) + 1}.webp"
            count = snapshot(trees, lat, lng, group, img_dir / image, colors[group].most_common(1)[0][0])
            places.append({"city": names[slug], **geo.place(lat, lng), "lat": round(lat, 5), "lng": round(lng, 5),
                           "inView": count["selected"], "image": image})
            if len(places) == SPOTS_PER_GROUP:
                break
        places.sort(key=lambda p: -p["inView"])
        out.append({"group": group, "key": key, "total": totals[group], "places": places})
        print(f"spots: {group}: " + "; ".join(f"{p['city']} / {p['road']} ({p['inView']})" for p in places))
    (i, j), _ = min(((k, v) for k, v in sf.items() if v[0] >= QUIET_MIN_TREES), key=lambda kv: kv[1][1] / kv[1][0])
    inside = [t for t in trees if t[5] == "sf" and (int(t[1] // CELL), int(t[0] // CELL)) == (i, j)]
    lat, lng = sum(t[1] for t in inside) / len(inside), sum(t[0] for t in inside) / len(inside)
    count = snapshot(trees, lat, lng, None, img_dir / "quiet-sf.webp")
    quiet = {"city": names["sf"], **geo.place(lat, lng), "lat": round(lat, 5), "lng": round(lng, 5),
             "inView": count["trees"], "turnInView": count["turn"], "image": "quiet-sf.webp"}
    return out, quiet


def build_data(img_dir: Path) -> dict:
    cities = json.loads((WEB / "species_stats.json").read_text())["cities"]
    by_name = {c["name"].split(",")[0].strip().lower(): c for c in cities}
    regions = {}
    for region, names in REGIONS.items():
        members = [by_name[n.lower()] for n in names if n.lower() in by_name]
        missing = [n for n in names if n.lower() not in by_name]
        if missing:
            print(f"warning: {region}: not in species_stats.json: {', '.join(missing)}")
        rows = [city_row(c) for c in members]
        total, fall = sum(r["total"] for r in rows), sum(r["fall"] for r in rows)
        regions[region] = {
            "total": total, "fall": fall, "pct": round(100 * fall / total),
            "cities": sorted((r for r in rows if r["total"] >= MIN_TABLE_TREES),
                             key=lambda r: -r["fall"] / r["total"]),
        }
    by_slug = {c["slug"]: c for c in cities}
    bay = regions["bay"]["cities"]
    trees = load_trees([r["slug"] for r in bay])
    hero(trees, {r["slug"]: (r["name"], f"{r['pct']}%") for r in bay if r["slug"] in HERO_LABELS},
         img_dir / "hero-bay.webp")
    spot_list, quiet = spots(trees, {r["slug"]: r["name"] for r in bay}, img_dir)
    return {
        "generated": date.today().isoformat(),
        "regions": regions,
        "city": {slug: city_row(by_slug[slug]) for slug in ("sf", "cupertino", "berkeley", "san_jose")},
        "sfEvergreens": evergreens(by_slug["sf"]),
        "groupTotals": {g["key"]: g["total"] for g in spot_list},
        "spots": spot_list,
        "sfQuiet": quiet,
        "mapTrees": sum(c["total"] for c in cities),
        "mapCities": len(cities),
    }


def export_images(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for key in PLATES:
        im = Image.open(WEB / "plates" / f"{key}.png").convert("RGB")
        im.thumbnail((480, 520))
        im.save(out / f"{key}.webp", quality=82)
    for slug, name in SHOTS.items():
        im = Image.open(ROOT / "promo" / "shots" / name).convert("RGB")
        side = min(im.size)  # square crop from the centre so the pair lines up
        left, top = (im.width - side) // 2, (im.height - side) // 2
        im = im.crop((left, top, left + side, top + side)).resize((720, 720), Image.LANCZOS)
        im.save(out / f"map-{slug}.webp", quality=80)
    print(f"wrote {len(PLATES) + len(SHOTS)} images to {out}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--web-home", type=Path, default=DEFAULT_WEB_HOME)
    args = parser.parse_args()
    data_file = args.web_home / "src" / "data" / "fall-colors.json"
    data_file.parent.mkdir(parents=True, exist_ok=True)
    img_dir = args.web_home / "public" / "imgs" / "fall-colors"
    data_file.write_text(json.dumps(build_data(img_dir), indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {data_file}")
    export_images(img_dir)


if __name__ == "__main__":
    main()
