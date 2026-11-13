#!/usr/bin/env python3
"""Record promo/reel/index.html to promo/instagram/reel.mp4.

The animation lives in HTML/CSS, so what gets recorded is exactly the artwork we
ship — no re-layout, no second implementation of the branding. Frames come from
the DevTools screencast and are re-timed with their own timestamps.

    python3 scripts/record_reel.py --seconds 16
"""

from __future__ import annotations

import argparse
import base64
import json
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

import websocket

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "assets" / "promo" / "reel.html"
OUT = ROOT / "promo" / "instagram" / "reel.mp4"
WORK = ROOT / "data" / "work" / "reel-frames"
CHROME = shutil.which("google-chrome-stable") or shutil.which("google-chrome")


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def start_chrome(port: int, profile: str) -> subprocess.Popen:
    if not CHROME:
        raise SystemExit("Chrome not found")
    proc = subprocess.Popen(
        [CHROME, "--headless=new", f"--remote-debugging-port={port}",
         f"--remote-allow-origins=http://127.0.0.1:{port}",
         f"--user-data-dir={profile}", "--no-first-run", "--disable-gpu",
         "--disable-dev-shm-usage", "--hide-scrollbars",
         "--window-size=1080,1920", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(80):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=1).read()
            return proc
        except Exception:
            time.sleep(0.5)
    proc.kill()
    raise SystemExit("chrome did not start")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=float, default=16.0)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--keep", action="store_true")
    args = parser.parse_args()

    shutil.rmtree(WORK, ignore_errors=True)
    WORK.mkdir(parents=True)

    port = free_port()
    profile = tempfile.mkdtemp(prefix="reel-")
    proc = start_chrome(port, profile)
    try:
        request = urllib.request.Request(
            f"http://127.0.0.1:{port}/json/new?{PAGE.as_uri()}?v={int(time.time())}", method="PUT")
        tab = json.load(urllib.request.urlopen(request))
        ws = websocket.create_connection(tab["webSocketDebuggerUrl"], timeout=120,
                                         origin=f"http://127.0.0.1:{port}")
        counter = [0]

        def send(method: str, params: dict | None = None) -> dict:
            counter[0] += 1
            ws.send(json.dumps({"id": counter[0], "method": method, "params": params or {}}))
            while True:
                message = json.loads(ws.recv())
                if message.get("id") == counter[0]:
                    return message

        send("Page.enable")
        # deterministic: freeze at t=0 then start the CSS clock ourselves
        time.sleep(2.5)
        # point the scenes at absolute files so the HTML can live anywhere
        scenes = ["01-contrast", "02-species", "04-city", "03-legend", "05-backcover"]
        send("Runtime.evaluate", {"expression": json.dumps([str(ROOT / "promo" / "instagram" / f"{name}.png") for name in scenes]) + """
          .forEach((p, i) => { const img = document.querySelectorAll('.scene img')[i];
            if (img) img.src = 'file://' + p; });"""})
        send("Page.reload", {"ignoreCache": True})
        time.sleep(2.0)
        send("Page.startScreencast", {"format": "jpeg", "quality": 88,
                                      "maxWidth": 1080, "maxHeight": 1920,
                                      "everyNthFrame": 1})

        frames, deadline = [], time.time() + args.seconds
        while time.time() < deadline:
            try:
                message = json.loads(ws.recv())
            except Exception:
                break
            if message.get("method") != "Page.screencastFrame":
                continue
            params = message["params"]
            data = base64.b64decode(params["data"])
            frames.append((time.time(), data))
            send("Page.screencastFrameAck", {"sessionId": params["sessionId"]})
        send("Page.stopScreencast")
        ws.close()
    finally:
        proc.terminate()
        shutil.rmtree(profile, ignore_errors=True)

    if len(frames) < 30:
        raise SystemExit(f"only captured {len(frames)} frames")

    # re-time: write each frame with the gap to the next one
    listing = []
    for index, (stamp, data) in enumerate(frames):
        path = WORK / f"f{index:05d}.jpg"
        path.write_bytes(data)
        nxt = frames[index + 1][0] if index + 1 < len(frames) else stamp + 1 / args.fps
        listing.append(f"file '{path.name}'\nduration {max(1 / args.fps, nxt - stamp):.4f}\n")
    listing.append(f"file '{WORK / f'f{len(frames)-1:05d}.jpg'}'\n")
    (WORK / "list.txt").write_text("".join(listing))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(WORK / "list.txt"),
        "-vf", "scale=1080:1920:flags=lanczos,fps=30",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(OUT),
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    seconds = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(OUT)], capture_output=True, text=True).stdout.strip())
    print(f"{len(frames)} frames → {OUT.relative_to(ROOT)} ({seconds:.1f}s, "
          f"{OUT.stat().st_size / 1024 / 1024:.1f} MB)")
    if not args.keep:
        shutil.rmtree(WORK, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
