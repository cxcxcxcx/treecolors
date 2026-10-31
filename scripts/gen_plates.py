#!/usr/bin/env python3
"""Generate botanical-illustration plates with nano-banana via the Gemini API.

One composite plate per species (leaf + autumn color + flower + fruit +
tree silhouette), vintage natural-history style. Intended for small
evaluation batches and, via the Batch API, full-knowledge-base runs.

Usage:
    python3 scripts/gen_plates.py --species "Acer rubrum" --out samples/
    python3 scripts/gen_plates.py --from-qa --limit 4 --out samples/
    python3 scripts/gen_plates.py --all-fall --out samples/   # ~696 images

Requires GEMINI_API_KEY. Pricing (Oct 2026): $0.0336 per 1K image,
$0.0168 via the Batch API. Full KB (~2300 plates) ≈ $77 / $39.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "py"))

MODEL = "gemini-nano-banana-2.1"

GUIDE_PROMPT = """Botanical illustration, vintage natural-history style, single balanced composition on a plain off-white background, for the tree {scientific} ({common}).
Subject guide — show what makes THIS species recognizable, in this priority order: {features}.
Composition guide: one dominant study (the first item above) taking about half the frame, the rest arranged around it with generous white space. Priority: {emphasis}. A small whole-tree silhouette sits at the bottom only if it aids recognition.
Accurate morphology above all: correct leaf shape, margin, venation, flower structure and fruit for this exact species; the same foliage must look consistent everywhere it appears. Watercolor with fine ink linework, muted natural colors.
There must be NO text, NO letters, NO captions, NO numbers and NO watermark anywhere on the image — leave a clean empty band at the bottom for a caption that will be added separately."""


def _kb() -> dict:
    with open(PROJECT_ROOT / "data" / "tree_info" / "species_info.json") as handle:
        return json.load(handle)


def _describe(name: str, kb: dict) -> dict | None:
    from tree_pipeline.species import load_resolver

    resolver = load_resolver()
    hit = resolver.resolve(name)
    if hit is None:
        return None
    info = hit.info
    common = (info.get("common_names") or [name])[0]
    has_fall = bool(info.get("fall_colors"))
    has_flowers = bool(info.get("beautiful_flowers"))
    season = (info.get("blooming_season") or "").strip()
    parts: list[str] = []
    if has_flowers:
        season_txt = f" ({season})" if season and season.lower() != "n/a" else ""
        parts.append(f"flowering branch{season_txt} with correct flower structure")
    if has_fall:
        parts.append("branch in peak autumn color plus a summer-leaf study with vein detail")
    else:
        parts.append("mature leaves, front and underside, with vein detail")
    parts.append("characteristic fruit and seed")
    if has_flowers and has_fall:
        emphasis = "give spring flowers and autumn foliage equal weight"
    elif has_flowers:
        emphasis = "lead with the flowers; leaves and fruit support"
    elif has_fall:
        emphasis = "lead with the autumn color; leaf detail and fruit support"
    else:
        emphasis = "lead with foliage detail and fruit; habit silhouette supports"
    words = hit.key.split()
    scientific = words[0].capitalize() + (" " + " ".join(words[1:]) if len(words) > 1 else "")
    return {
        "key": hit.key,
        "scientific": hit.key,
        "Scientific": scientific,
        "common": common,
        "features": "; ".join(parts),
        "emphasis": emphasis,
    }


def _generate(prompt: str, key: str, retries: int = 3) -> bytes:
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise SystemExit("GEMINI_API_KEY is not set")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "imageConfig": {"aspectRatio": "1:1", "imageSize": "1K"},
        },
    }
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            request = urllib.request.Request(
                url + "?key=" + api_key,
                data=json.dumps(body).encode(),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(request, timeout=300) as response:
                data = json.load(response)
            for part in data.get("candidates", [{}])[0].get("content", {}).get("parts", []):
                if "inlineData" in part:
                    return base64.b64decode(part["inlineData"]["data"])
            last_error = RuntimeError(f"no image in response: {json.dumps(data)[:300]}")
        except Exception as exc:  # noqa: BLE001 - retry transient failures
            last_error = exc
            time.sleep(2 ** (attempt + 1))
    raise RuntimeError(f"failed after {retries} attempts: {last_error}")


CAPTION_FONT = "/usr/share/fonts/TTF/DejaVuSerifCondensed-Italic.ttf"


def _add_caption(image_bytes: bytes, scientific: str) -> bytes:
    """Overlay the Latin caption ourselves — model-rendered text is unreliable."""
    import io
    from PIL import Image, ImageDraw, ImageFont

    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype(CAPTION_FONT, max(28, image.width // 32))
    except OSError:
        font = ImageFont.load_default()
    text = scientific
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    margin = int(image.height * 0.035)
    draw.text(((image.width - tw) / 2, image.height - margin - (bbox[3] - bbox[1])),
              text, font=font, fill=(45, 45, 45))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--species", action="append", default=[],
                        help="Species name (repeatable)")
    parser.add_argument("--from-qa", action="store_true",
                        help="Take top species by tree count across QA files")
    parser.add_argument("--all-fall", action="store_true",
                        help="All fall-color species in the knowledge base")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--out", default="samples")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    kb = _kb()
    names: list[str] = list(args.species)
    if args.from_qa or args.all_fall:
        import glob
        from collections import Counter
        counts: Counter[str] = Counter()
        for path in glob.glob(str(PROJECT_ROOT / "data" / "output" / "qa" / "*.json")):
            with open(path) as handle:
                qa = json.load(handle)
            for entry in qa.get("species", []):
                counts[entry["species"]] += entry["count"]
        if args.all_fall:
            from tree_pipeline.species import load_resolver
            resolver = load_resolver()
            for entry in kb:
                hit = resolver.resolve(entry)
                if hit and hit.info.get("deciduous") and hit.info.get("fall_colors"):
                    names.append(entry)
        else:
            names.extend([name for name, _ in counts.most_common(args.limit or 4)])

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    done = skipped = failed = 0
    for name in names:
        slug = "".join(c if c.isalnum() else "_" for c in name.lower()).strip("_")
        target = out_dir / f"{slug}.png"
        if target.exists() and not args.force:
            print(f"  [skip] {name} (exists)")
            skipped += 1
            continue
        spec = _describe(name, kb)
        if spec is None:
            print(f"  [unresolved] {name}")
            failed += 1
            continue
        prompt = GUIDE_PROMPT.format(**spec)
        print(f"  [gen] {name} ...", flush=True)
        try:
            raw = _generate(prompt, spec["key"])
            target.write_bytes(_add_caption(raw, spec["Scientific"]))
            done += 1
        except RuntimeError as exc:
            print(f"  [error] {name}: {exc}")
            failed += 1
        time.sleep(2)
    print(f"done={done} skipped={skipped} failed={failed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
