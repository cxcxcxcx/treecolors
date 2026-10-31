#!/usr/bin/env python3
"""Generate app-icon concept sheets with nano-banana, grounded on reference art.

Example:
    python3 scripts/gen_icons.py \
      --ref /tmp/opencode/bs512.png --ref /tmp/opencode/old_leaf.png \
      --prompt-file /tmp/opencode/icon_brief_a.txt \
      --out samples/icons/grid_a.png

Requires GEMINI_API_KEY. 1K images, ~$0.0336 each standard.
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

MODEL = "gemini-nano-banana-2.1"


def _generate(parts: list[dict], retries: int = 3) -> bytes:
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise SystemExit("GEMINI_API_KEY is not set")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
    body = {
        "contents": [{"parts": parts}],
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
            last_error = RuntimeError("no image in response")
        except Exception as exc:  # noqa: BLE001 - retry transient failures
            last_error = exc
            time.sleep(2 ** (attempt + 1))
    raise RuntimeError(f"failed after {retries} attempts: {last_error}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", action="append", default=[])
    parser.add_argument("--prompt", default="")
    parser.add_argument("--prompt-file", default="")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    prompt = args.prompt or (Path(args.prompt_file).read_text() if args.prompt_file else "")
    if not prompt:
        raise SystemExit("Provide --prompt or --prompt-file")
    parts: list[dict] = []
    for ref in args.ref:
        data = Path(ref).read_bytes()
        suffix = Path(ref).suffix.lower()
        mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(
            suffix.lstrip("."), "image/png")
        parts.append({"inline_data": {"mime_type": mime, "data": base64.b64encode(data).decode()}})
    parts.append({"text": prompt})

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(_generate(parts))
    print(f"wrote {out} ({out.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
