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

PLATE_PROMPT = """Botanical illustration plate, vintage natural-history style, on a plain off-white background, for the tree {scientific} ({common}).
Four labeled studies arranged in a clean 2x2 grid with thin rules: (1) summer leaf, front and underside, with a vein-detail inset; (2) autumn foliage showing {fall_desc}; (3) {flower_desc}; (4) {fruit_desc}. A small whole-tree silhouette sits centered at the bottom.
Accurate morphology above all: correct leaf shape, venation, flower structure and fruit for this exact species. Watercolor with fine ink linework, muted natural colors. The ONLY text on the plate is one small elegant Latin caption "{scientific}" in correct italics at the bottom center, with lowercase species epithet. No figure numbers, no other words, no dates, no watermark. Every panel must show the foliage of THIS species only, with the same leaf shape in all panels."""


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
    fall = "brilliant red autumn foliage" if info.get("fall_colors") else "typical late-season foliage"
    return {
        "key": hit.key,
        "scientific": hit.key,
        "common": common,
        "fall_desc": fall,
        "flower_desc": f"characteristic flowers of {hit.key} ({info.get('blooming_season', 'N/A')} blooming)".replace("  ", " "),
        "fruit_desc": f"characteristic fruit and seed of {hit.key}",
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
        prompt = PLATE_PROMPT.format(**spec)
        print(f"  [gen] {name} ...", flush=True)
        try:
            target.write_bytes(_generate(prompt, spec["key"]))
            done += 1
        except RuntimeError as exc:
            print(f"  [error] {name}: {exc}")
            failed += 1
        time.sleep(2)
    print(f"done={done} skipped={skipped} failed={failed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
