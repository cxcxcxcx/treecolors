#!/usr/bin/env python3
"""Cover the remaining species with NxN plate sheets through the Batch API.

One 3x3 sheet costs one image (batch: $0.0168) instead of nine, so the whole
remaining knowledge base is a couple of dollars.

Workflow:
    python3 scripts/batch_plates.py plan                 # what would be sent
    python3 scripts/batch_plates.py submit               # create the batch
    python3 scripts/batch_plates.py status               # poll the job
    python3 scripts/batch_plates.py download             # slice results into plates

State lives in data/work/batch_plates.json so every step can resume.
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

from gen_plates import _describe, _kb  # noqa: E402
from merge_duplicate_keys import find_pairs, genus_tokens, slugify  # noqa: E402

MODEL = "gemini-nano-banana-2.1"
API = "https://generativelanguage.googleapis.com/v1beta"
STATE_PATH = PROJECT_ROOT / "data" / "work" / "batch_plates.json"
PLATE_DIR = PROJECT_ROOT / "samples" / "plates80"
WEB_PLATE_DIR = PROJECT_ROOT / "web" / "plates"
COLUMNS = 3
BATCH_PRICE = 0.0168  # per 1K image, Batch tier

SHEET_PROMPT = """Botanical illustration sheet: a {rows}x{cols} grid of {count} separate botanical studies, one per species, each study centred inside its own equal cell on a plain off-white background, vintage natural-history style, watercolour with fine ink linework, muted natural colours.

Nothing may cross, overlap or touch a cell boundary: every cell holds exactly one complete illustration with generous empty margin on all four sides. Do not draw grid lines, frames or dividers.

The species, in reading order (left to right, top to bottom):
{listing}

For each one show what makes that species recognisable: correct leaf shape, margin and venation, its real autumn foliage colour, and flower or fruit where diagnostic. Every species must look clearly different from the others.

There must be NO text, NO letters, NO numbers, NO captions and NO watermark anywhere on the image."""


def _api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        raise SystemExit("GEMINI_API_KEY is not set")
    return key


def _request(path: str, data: dict | None = None, method: str | None = None,
             headers: dict | None = None, raw: bytes | None = None) -> dict:
    url = path if path.startswith("http") else f"{API}/{path}"
    body = raw if raw is not None else (json.dumps(data).encode() if data is not None else None)
    request = urllib.request.Request(url, data=body, method=method or ("POST" if body else "GET"))
    request.add_header("x-goog-api-key", _api_key())
    request.add_header("Content-Type", "application/json")
    for name, value in (headers or {}).items():
        request.add_header(name, value)
    with urllib.request.urlopen(request, timeout=300) as response:
        payload = response.read()
    return json.loads(payload) if payload else {}


def _missing_species() -> list[dict]:
    """Species with no plate yet, ordered by how many trees they represent."""
    kb = _kb()
    aliases = json.loads((PROJECT_ROOT / "data/tree_info/species_aliases.json").read_text())
    pairs = dict(find_pairs(kb, genus_tokens(kb, aliases)))
    counts: Counter[str] = Counter()
    for path in (PROJECT_ROOT / "data/output/qa").glob("*.json"):
        for entry in json.load(open(path)).get("species", []):
            counts[entry["species"]] += entry["count"]
    have = {path.stem for path in PLATE_DIR.glob("*.png")}
    chosen, seen = [], set()
    for name, count in counts.most_common():
        spec = _describe(name, kb)
        if spec is None:
            continue
        key = pairs.get(spec["key"], spec["key"])
        if key in seen or " spp" in key:
            continue
        seen.add(key)
        spec["key"] = key
        spec["slug"] = slugify(key)
        spec["count"] = count
        if spec["slug"] in have:
            continue
        chosen.append(spec)
    return chosen


def _sheet_prompt(chunk: list[dict]) -> str:
    rows = math.ceil(len(chunk) / COLUMNS)
    listing = "\n".join(
        f"{position}. {spec['Scientific']} ({spec['common']}) — {spec['features']}"
        for position, spec in enumerate(chunk, 1)
    )
    return SHEET_PROMPT.format(rows=rows, cols=COLUMNS, count=len(chunk), listing=listing)


def _build_requests(specs: list[dict]) -> tuple[list[dict], dict[str, list[str]]]:
    requests, mapping = [], {}
    for index in range(0, len(specs), COLUMNS * COLUMNS):
        chunk = specs[index:index + COLUMNS * COLUMNS]
        key = f"sheet-{index // (COLUMNS * COLUMNS) + 1:03d}"
        mapping[key] = [spec["slug"] for spec in chunk]
        rows = math.ceil(len(chunk) / COLUMNS)
        requests.append({
            "key": key,
            "request": {
                "contents": [{"parts": [{"text": _sheet_prompt(chunk)}]}],
                "generation_config": {
                    "response_modalities": ["TEXT", "IMAGE"],
                    "image_config": {"aspect_ratio": "1:1", "image_size": "1K"},
                },
            },
        })
    return requests, mapping


def _upload(jsonl: bytes, display_name: str) -> str:
    start = _request(
        f"https://generativelanguage.googleapis.com/upload/v1beta/files",
        method="POST",
        headers={
            "X-Goog-Upload-Protocol": "resumable",
            "X-Goog-Upload-Command": "start",
            "X-Goog-Upload-Header-Content-Length": str(len(jsonl)),
            "X-Goog-Upload-Header-Content-Type": "application/jsonl",
            "Content-Type": "application/json",
        },
        raw=json.dumps({"file": {"display_name": display_name}}).encode(),
    )
    url = start.get("upload_url") or start.get("file", {}).get("upload_url")
    if not url:
        raise SystemExit(f"no upload url in {json.dumps(start)[:300]}")
    request = urllib.request.Request(url, data=jsonl, method="POST")
    request.add_header("X-Goog-Upload-Command", "upload, finalize")
    request.add_header("X-Goog-Upload-Offset", "0")
    request.add_header("Content-Type", "application/jsonl")
    with urllib.request.urlopen(request, timeout=600) as response:
        payload = json.loads(response.read())
    return payload["file"]["name"]


def cmd_plan(args: argparse.Namespace) -> int:
    specs = _missing_species()
    sheets = math.ceil(len(specs) / (COLUMNS * COLUMNS))
    print(f"species without a plate: {len(specs)}")
    print(f"sheets of {COLUMNS}x{COLUMNS}: {sheets}")
    print(f"estimated batch cost: ${sheets * BATCH_PRICE:.2f}")
    print(f"estimated wall time: {sheets * 2 / 60:.0f}-{sheets * 6 / 60:.0f} min")
    for spec in specs[:10]:
        print(f"  {spec['count']:8,d}  {spec['Scientific']}")
    if args.limit:
        print(f"(submit would cap at {args.limit} species)")
    return 0


def cmd_submit(args: argparse.Namespace) -> int:
    specs = _missing_species()
    if args.limit:
        specs = specs[:args.limit]
    if not specs:
        print("nothing to generate")
        return 0
    requests, mapping = _build_requests(specs)
    jsonl = ("\n".join(json.dumps(request) for request in requests) + "\n").encode()
    print(f"uploading {len(requests)} requests ({len(jsonl)/1024:.0f} KB) ...")
    file_name = _upload(jsonl, "treecolors-plates")
    print(f"input file: {file_name}")
    if args.dry_run:
        print("dry run: not creating the batch")
        return 0
    created = _request(
        f"models/{MODEL}:batchGenerateContent",
        data={"batch": {"display_name": "treecolors-plates", "input_config": {"file_name": file_name}}},
    )
    state = {
        "batch": created.get("name"),
        "input_file": file_name,
        "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "sheets": len(requests),
        "species": len(specs),
        "mapping": mapping,
    }
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2))
    print(f"batch created: {state['batch']} ({len(specs)} species in {len(requests)} sheets)")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    state = json.loads(STATE_PATH.read_text())
    batch = _request(state["batch"])
    print(f"{state['batch']}: {batch.get('state')}  "
          f"({batch.get('batchStats', {})})")
    return 0


def cmd_download(args: argparse.Namespace) -> int:
    state = json.loads(STATE_PATH.read_text())
    batch = _request(state["batch"])
    if batch.get("state") not in {"BATCH_STATE_SUCCEEDED", "JOB_STATE_SUCCEEDED", "SUCCEEDED"}:
        raise SystemExit(f"batch not ready: {batch.get('state')}")
    output = batch.get("output") or {}
    file_name = output.get("responsesFile") or output.get("file_name") or output.get("fileName")
    if not file_name:
        raise SystemExit(f"no responses file in {json.dumps(output)[:300]}")
    url = f"https://generativelanguage.googleapis.com/v1beta/{file_name}:download?alt=media"
    request = urllib.request.Request(url)
    request.add_header("x-goog-api-key", _api_key())
    with urllib.request.urlopen(request, timeout=600) as response:
        payload = response.read()

    PLATE_DIR.mkdir(parents=True, exist_ok=True)
    WEB_PLATE_DIR.mkdir(parents=True, exist_ok=True)
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
            print(f"  [skip] {key}: no image ({json.dumps(entry)[:160]})")
            continue
        rows = math.ceil(len(slugs) / COLUMNS)
        cells = _slice_grid(image, rows, COLUMNS)
        for slug, cell in zip(slugs, cells):
            (PLATE_DIR / f"{slug}.png").write_bytes(cell)
            (WEB_PLATE_DIR / f"{slug}.png").write_bytes(cell)
            written += 1
    print(f"wrote {written} plates")
    return 0


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
        if name in {"plan", "submit"}:
            part.add_argument("--limit", type=int, default=0,
                              help="Only the top N missing species")
        if name == "submit":
            part.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
