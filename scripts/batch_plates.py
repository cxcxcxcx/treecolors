#!/usr/bin/env python3
"""Generate species artwork through the Batch API, one 3x3 sheet at a time.

Two modes:
    plate  — one full botanical plate per species (popup illustration)
    leaf   — one single leaf per species (thumbnail in the species list)

A 3x3 sheet is one billed image, so a sheet costs $0.0168 in Batch instead of
nine separate images.  Every step is resumable through data/work/batch_*.json.

Workflow:
    python3 scripts/batch_plates.py plan   --mode leaf --top 108
    python3 scripts/batch_plates.py submit --mode leaf --top 108
    python3 scripts/batch_plates.py status --mode leaf
    python3 scripts/batch_plates.py download --mode leaf
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import math
import os
import sys
import time
import urllib.request
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "py"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from gen_plates import GUIDE_PROMPT, _describe, _kb  # noqa: E402
from merge_duplicate_keys import slugify  # noqa: E402

MODEL = "gemini-nano-banana-2.1"
API = "https://generativelanguage.googleapis.com/v1beta"
COLUMNS = 3
BATCH_PRICE = 0.0168  # per 1K image, Batch tier
RESOLVE_ALIASES = ("samples/plates80", "web/plates")

MODES = {
    "plate": {
        "samples": PROJECT_ROOT / "samples" / "plates80",
        "web": PROJECT_ROOT / "web" / "plates",
        "resize": 0,
        "state": PROJECT_ROOT / "data" / "work" / "batch_plates.json",
    },
    "leaf": {
        "samples": PROJECT_ROOT / "samples" / "leaves",
        "web": PROJECT_ROOT / "web" / "leaves",
        "resize": 256,
        "state": PROJECT_ROOT / "data" / "work" / "batch_leaves.json",
    },
}

PLATE_PROMPT = """Botanical illustration sheet: a {rows}x{cols} grid of {count} separate botanical studies, one per species, each study centred inside its own equal cell on a plain off-white background, vintage natural-history style, watercolour with fine ink linework, muted natural colours.

Nothing may cross, overlap or touch a cell boundary: every cell holds exactly one complete illustration with generous empty margin on all four sides. Do not draw grid lines, frames or dividers.

The species, in reading order (left to right, top to bottom):
{listing}

For each one show what makes that species recognisable: correct leaf shape, margin and venation, its real foliage colour in its most characteristic season (autumn colour for deciduous species, normal green for evergreen ones), and flower or fruit where diagnostic. Every species must look clearly different from the others.

There must be NO text, NO letters, NO numbers, NO captions and NO watermark anywhere on the image."""

LEAF_PROMPT = """Botanical illustration sheet: a {rows}x{cols} grid of {count} small plant icons, one per species, each centred inside its own equal cell on a plain cream background, flat botanical illustration with fine ink linework and solid muted colours. For most species this is one detached leaf; for conifers, palms and other plants whose single leaf is not recognisable, use a small sprig, needle cluster or frond instead.

Nothing may cross, overlap or touch a cell boundary: every cell holds exactly one complete plant icon with generous empty margin on all four sides. Do not draw grid lines, frames, dividers, branches, whole trees, flowers or fruit.

The species, in reading order (left to right, top to bottom):
{listing}

Draw each one in its true shape, margin, tip and venation, isolated and facing the viewer. Colour it in its characteristic autumn colour if the species is deciduous; evergreen species stay in their normal green.

Where a single detached leaf would not represent the plant clearly - conifers, palms, ginkgo and similar - draw instead the smallest recognisable sprig, needle cluster or frond of that species, kept inside its cell. Each one must look clearly different from the others and be identifiable at thumbnail size.

There must be NO text, NO letters, NO numbers, NO captions and NO watermark anywhere on the image."""


def _api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        raise SystemExit("GEMINI_API_KEY is not set")
    return key


def _request(path: str, data: dict | None = None) -> dict:
    url = path if path.startswith("http") else f"{API}/{path}"
    body = json.dumps(data).encode() if data is not None else None
    request = urllib.request.Request(url, data=body, method="POST" if body else "GET")
    request.add_header("x-goog-api-key", _api_key())
    request.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(request, timeout=120) as response:
        payload = response.read()
    return json.loads(payload) if payload else {}


def _species_counts() -> tuple[Counter, dict[str, str]]:
    """Tree counts per canonical species key, from the site's own data file.

    web/species_stats.json is the ground truth: it is built from every city's
    GeoJSON and therefore covers cities whose QA report was never produced.
    """
    stats = json.loads((PROJECT_ROOT / "web" / "species_stats.json").read_text())
    counts: Counter = Counter()
    display: dict[str, str] = {}
    for city in stats["cities"]:
        for entry in city.get("species", []):
            key = entry.get("key")
            if not key:
                continue
            counts[key] += entry["count"]
            display.setdefault(key, entry["species"])
    return counts, display


def _target_species(mode: str, top: int, keys: set[str] | None = None) -> list[dict]:
    kb = _kb()
    counts, display = _species_counts()
    have = {path.stem for path in MODES[mode]["samples"].glob("*.png")}
    have |= {path.stem for path in MODES[mode]["web"].glob("*.png")}
    chosen: list[dict] = []
    for key, count in counts.most_common():
        if " spp" in key:
            continue
        slug = slugify(key)
        if keys is not None:
            if key not in keys:
                continue
        elif slug in have:
            continue
        spec = _describe(display[key], kb) or {"common": display[key], "features": ""}
        spec["key"] = key
        spec["slug"] = slug
        spec["count"] = count
        spec["Scientific"] = spec.get("Scientific") or display[key]
        chosen.append(spec)
        if top and len(chosen) >= top:
            break
    return chosen


def _listing(chunk: list[dict], mode: str) -> str:
    lines = []
    for position, spec in enumerate(chunk, 1):
        if mode == "plate":
            lines.append(f"{position}. {spec['Scientific']} ({spec['common']}) — {spec.get('features', '')}")
        else:
            lines.append(f"{position}. {spec['Scientific']} ({spec['common']})")
    return "\n".join(lines)


def _grid_plan(count: int) -> list[int]:
    """Split N species into square grids: 9 (3x3), then 4 (2x2), then singles.

    A rectangular split of a square image would squash every cell, so a tail of
    two or three species is cheaper and cleaner as single-image requests.
    """
    sizes: list[int] = []
    while count >= 9:
        sizes.append(9)
        count -= 9
    if count >= 4:
        sizes.append(4)
        count -= 4
    sizes.extend([1] * count)
    return sizes


def _build_requests(specs: list[dict], mode: str) -> tuple[list[dict], dict[str, list[str]]]:
    template = PLATE_PROMPT if mode == "plate" else LEAF_PROMPT
    requests, mapping = [], {}
    cursor = 0
    for sheet_index, size in enumerate(_grid_plan(len(specs)), 1):
        chunk = specs[cursor:cursor + size]
        cursor += size
        key = f"sheet-{sheet_index:03d}"
        mapping[key] = [spec["slug"] for spec in chunk]
        if size == 1:
            text = GUIDE_PROMPT.format(**chunk[0])
        else:
            rows = cols = int(math.sqrt(size))
            text = template.format(rows=rows, cols=cols, count=len(chunk),
                                   listing=_listing(chunk, mode))
        requests.append({
            "key": key,
            "request": {
                "contents": [{"parts": [{"text": text}]}],
                "generation_config": {
                    "response_modalities": ["TEXT", "IMAGE"],
                    "image_config": {"aspect_ratio": "1:1", "image_size": "1K"},
                },
            },
        })
    return requests, mapping


def _upload(jsonl: bytes, display_name: str) -> str:
    start = urllib.request.Request(
        "https://generativelanguage.googleapis.com/upload/v1beta/files",
        data=json.dumps({"file": {"display_name": display_name}}).encode(),
        method="POST",
    )
    start.add_header("x-goog-api-key", _api_key())
    start.add_header("X-Goog-Upload-Protocol", "resumable")
    start.add_header("X-Goog-Upload-Command", "start")
    start.add_header("X-Goog-Upload-Header-Content-Length", str(len(jsonl)))
    start.add_header("X-Goog-Upload-Header-Content-Type", "application/jsonl")
    start.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(start, timeout=120) as response:
        url = response.headers.get("X-Goog-Upload-URL")
    if not url:
        raise SystemExit("no X-Goog-Upload-URL in the upload-start response")

    upload = urllib.request.Request(url, data=jsonl, method="POST")
    upload.add_header("x-goog-api-key", _api_key())
    upload.add_header("X-Goog-Upload-Command", "upload, finalize")
    upload.add_header("X-Goog-Upload-Offset", "0")
    upload.add_header("Content-Type", "application/jsonl")
    with urllib.request.urlopen(upload, timeout=180) as response:
        payload = json.loads(response.read())
    return payload["file"]["name"]


def _keys(args: argparse.Namespace) -> set[str] | None:
    raw = getattr(args, "keys", "") or ""
    return {part.strip().lower() for part in raw.split(",") if part.strip()} or None


def cmd_plan(args: argparse.Namespace) -> int:
    specs = _target_species(args.mode, args.top, _keys(args))
    sheets = len(_grid_plan(len(specs)))
    print(f"mode={args.mode}  species={len(specs)}  sheets={sheets}  "
          f"batch cost=${sheets * BATCH_PRICE:.2f}")
    for spec in specs[:12]:
        print(f"  {spec['count']:8,d}  {spec['Scientific']}")
    return 0


def cmd_submit(args: argparse.Namespace) -> int:
    specs = _target_species(args.mode, args.top, _keys(args))
    if not specs:
        print("nothing to generate")
        return 0
    requests, mapping = _build_requests(specs, args.mode)
    jsonl = ("\n".join(json.dumps(request) for request in requests) + "\n").encode()
    print(f"mode={args.mode}: {len(specs)} species in {len(requests)} sheets "
          f"({len(jsonl)/1024:.0f} KB) ...", flush=True)
    file_name = _upload(jsonl, f"treecolors-{args.mode}")
    print(f"input file: {file_name}")
    if args.dry_run:
        print("dry run: not creating the batch")
        return 0
    created = _request(
        f"models/{MODEL}:batchGenerateContent",
        data={"batch": {"display_name": f"treecolors-{args.mode}",
                        "input_config": {"file_name": file_name}}},
    )
    state = {
        "mode": args.mode,
        "batch": created.get("name"),
        "input_file": file_name,
        "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "sheets": len(requests),
        "species": len(specs),
        "mapping": mapping,
    }
    state_path = MODES[args.mode]["state"]
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2))
    print(f"batch created: {state['batch']} ({len(specs)} species, {len(requests)} sheets)")
    return 0


def _batch_state(batch: dict) -> str:
    return batch.get("state") or batch.get("metadata", {}).get("state") or ""


def _batch_output(batch: dict) -> dict:
    return batch.get("output") or batch.get("metadata", {}).get("output") or {}


def cmd_status(args: argparse.Namespace) -> int:
    state = json.loads(MODES[args.mode]["state"].read_text())
    batch = _request(state["batch"])
    stats = batch.get("metadata", {}).get("batchStats", {})
    print(f"{state['batch']}: {_batch_state(batch)}  {stats}")
    return 0


def cmd_download(args: argparse.Namespace) -> int:
    config = MODES[args.mode]
    state = json.loads(config["state"].read_text())
    batch = _request(state["batch"])
    current = _batch_state(batch)
    if current not in {"BATCH_STATE_SUCCEEDED", "JOB_STATE_SUCCEEDED", "SUCCEEDED"}:
        raise SystemExit(f"batch not ready: {current}")
    output = _batch_output(batch)
    file_name = output.get("responsesFile") or output.get("file_name") or output.get("fileName")
    if not file_name:
        raise SystemExit(f"no responses file in {json.dumps(output)[:300]}")

    request = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/{file_name}:download?alt=media")
    request.add_header("x-goog-api-key", _api_key())
    with urllib.request.urlopen(request, timeout=300) as response:
        payload = response.read()

    _load_slug_index()
    for directory in (config["samples"], config["web"]):
        directory.mkdir(parents=True, exist_ok=True)
    written = 0
    for line in payload.decode().splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        key = entry.get("key") or entry.get("metadata", {}).get("key")
        slugs = state["mapping"].get(key) or []
        candidates = entry.get("response", {}).get("candidates") or []
        image = None
        for part in (candidates[0].get("content", {}).get("parts", []) if candidates else []):
            if "inlineData" in part:
                image = base64.b64decode(part["inlineData"]["data"])
                break
        if not image:
            print(f"  [skip] {key}: no image")
            continue
        side = max(1, int(round(math.sqrt(len(slugs)))))
        cells = _slice_grid(image, side, side)
        for slug, cell in zip(slugs, cells):
            if args.mode == "plate":
                scientific = _scientific_for(slug)
                if scientific:
                    # Always caption on a padded band: the model sometimes puts
                    # a tree silhouette exactly where the old band used to be.
                    cell = _caption_grid_cell(cell, scientific)
            if config["resize"]:
                cell = _resize(cell, config["resize"])
            (config["samples"] / f"{slug}.png").write_bytes(cell)
            (config["web"] / f"{slug}.png").write_bytes(cell)
            written += 1
    print(f"wrote {written} {args.mode} images")
    return 0


def _bottom_is_empty(image_bytes: bytes, threshold: int = 18) -> bool:
    from PIL import Image

    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    background = image.getpixel((2, 2))
    band = image.crop((0, int(image.height * 0.9), image.width, image.height))
    pixels = list(band.getdata())
    busy = sum(1 for pixel in pixels
               if abs(pixel[0] - background[0]) + abs(pixel[1] - background[1])
               + abs(pixel[2] - background[2]) > threshold)
    return busy < len(pixels) * 0.02


def _caption_grid_cell(image_bytes: bytes, scientific: str) -> bytes:
    """Add the Latin caption below a sliced cell without covering the drawing."""
    from PIL import Image, ImageDraw, ImageFont

    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    band = max(26, int(image.height * 0.085))
    background = image.getpixel((2, 2))
    canvas = Image.new("RGB", (image.width, image.height + band), background)
    canvas.paste(image, (0, 0))
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSerifCondensed-Italic.ttf",
                                  max(16, image.width // 22))
    except OSError:
        font = ImageFont.load_default()
    box = draw.textbbox((0, 0), scientific, font=font)
    draw.text(((canvas.width - (box[2] - box[0])) / 2, image.height + (band - (box[3] - box[1])) / 2 - box[1] / 2),
              scientific, font=font, fill=(45, 45, 45))
    buffer = io.BytesIO()
    canvas.save(buffer, format="PNG")
    return buffer.getvalue()


def _scientific_for(slug: str) -> str:
    key = _SLUG_TO_KEY.get(slug, "")
    if not key:
        return ""
    words = key.split()
    return words[0].capitalize() + (" " + " ".join(words[1:]) if len(words) > 1 else "")


_SLUG_TO_KEY: dict[str, str] = {}


def _load_slug_index() -> None:
    if not _SLUG_TO_KEY:
        for key in _kb():
            _SLUG_TO_KEY[slugify(key)] = key


def _resize(image_bytes: bytes, size: int) -> bytes:
    from PIL import Image

    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image = image.resize((size, size), Image.LANCZOS)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def _slice_grid(image_bytes: bytes, rows: int, cols: int, inset: float = 0.02) -> list[bytes]:
    from PIL import Image

    sheet = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    width, height = sheet.width / cols, sheet.height / rows
    pad_x, pad_y = int(width * inset), int(height * inset)
    cells = []
    for row in range(rows):
        for col in range(cols):
            box = (
                int(col * width) + pad_x,
                int(row * height) + pad_y,
                int((col + 1) * width) - pad_x,
                int((row + 1) * height) - pad_y,
            )
            buffer = io.BytesIO()
            sheet.crop(box).save(buffer, format="PNG")
            cells.append(buffer.getvalue())
    return cells


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name, func in (("plan", cmd_plan), ("submit", cmd_submit),
                       ("status", cmd_status), ("download", cmd_download)):
        part = sub.add_parser(name)
        part.set_defaults(func=func)
        part.add_argument("--mode", default="plate", choices=sorted(MODES))
        if name in {"plan", "submit"}:
            part.add_argument("--top", type=int, default=0,
                              help="Only the N most common species still missing artwork")
            part.add_argument("--keys", default="",
                              help="Comma-separated species keys to redraw, ignoring existing files")
        if name == "submit":
            part.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
