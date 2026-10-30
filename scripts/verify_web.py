#!/usr/bin/env python3
"""Reusable browser smoke test for the tree map.

Examples::

    # Chrome already running with --remote-debugging-port=9222
    scripts/verify_web.py --url http://127.0.0.1:8767/?v=1

    # Launch headless Chrome for the check
    scripts/verify_web.py --launch --url http://127.0.0.1:8767/

The page must be served by a Range-capable server; use scripts/serve_local.sh.
Requires: websocket-client, google-chrome-stable (or chromium).
"""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

try:
    import websocket
except ImportError:  # pragma: no cover - dependency hint
    raise SystemExit("Install websocket-client: pip install websocket-client")


def _json(url: str):
    with urllib.request.urlopen(url, timeout=5) as response:
        return json.load(response)


def _wait_for_cdp(cdp: str, timeout: float = 20.0) -> dict:
    deadline = time.time() + timeout
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            return _json(f"{cdp}/json/version")
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(0.5)
    raise SystemExit(f"Chrome DevTools endpoint not available at {cdp}: {last_error}")


def _launch_chrome(cdp: str, chrome: str, profile: str) -> subprocess.Popen:
    port = cdp.rsplit(":", 1)[-1]
    command = [
        chrome,
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        "--enable-unsafe-swiftshader",
        f"--remote-debugging-port={port}",
        "--remote-allow-origins=*",
        f"--user-data-dir={profile}",
        "about:blank",
    ]
    process = subprocess.Popen(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    _wait_for_cdp(cdp)
    return process


def _new_tab(cdp: str, url: str) -> dict:
    request = urllib.request.Request(
        f"{cdp}/json/new?{url}",
        method="PUT",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.load(response)


class Session:
    def __init__(self, ws_url: str):
        self.ws = websocket.create_connection(ws_url, timeout=120)
        self.next_id = 0
        self.events: list[dict] = []

    def send(self, method: str, params: dict | None = None) -> dict:
        self.next_id += 1
        self.ws.send(json.dumps({"id": self.next_id, "method": method, "params": params or {}}))
        while True:
            message = json.loads(self.ws.recv())
            if message.get("id") == self.next_id:
                return message
            if message.get("method"):
                self.events.append(message)

    def evaluate(self, expression: str):
        response = self.send(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True},
        )
        result = response.get("result", {}).get("result", {})
        if "exceptionDetails" in response.get("result", {}):
            raise RuntimeError(f"JS exception for {expression!r}: {response['result']['exceptionDetails']}")
        return result.get("value")

    def close(self) -> None:
        self.ws.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8767/")
    parser.add_argument("--cdp", default="http://127.0.0.1:9222")
    parser.add_argument("--wait", type=float, default=15.0)
    parser.add_argument("--screenshot", type=Path, default=None)
    parser.add_argument("--launch", action="store_true", help="Launch headless Chrome")
    parser.add_argument("--chrome", default="google-chrome-stable")
    parser.add_argument("--profile", default="/tmp/opencode/tree-map-chrome-profile")
    args = parser.parse_args()

    process = None
    if args.launch:
        process = _launch_chrome(args.cdp, args.chrome, args.profile)

    try:
        _wait_for_cdp(args.cdp)
        tab = _new_tab(args.cdp, args.url)
        session = Session(tab["webSocketDebuggerUrl"])
        session.send("Runtime.enable")
        session.send("Page.enable")
        time.sleep(args.wait)

        errors = []
        for event in session.events:
            if event.get("method") == "Runtime.exceptionThrown":
                errors.append(event["params"].get("exceptionDetails", {}).get("text", "JS exception"))
            elif event.get("method") == "Runtime.consoleAPICalled":
                params = event.get("params", {})
                if params.get("type") == "error":
                    text = " ".join(str(arg.get("value", "")) for arg in params.get("args", []))
                    if "Error getting location" not in text:
                        errors.append(text)

        checks = {
            "title": "document.title",
            "map_defined": "typeof map !== 'undefined'",
            "layer_exists": "!!map.getLayer('trees-points')",
            "species_rows": "document.querySelectorAll('.species-row').length",
            "species_scope": "document.querySelector('#species-scope')?.textContent",
            "source_link": "sourceForFeature({source_key:'washington_dc:ufa_street_trees'}, null)?.url || null",
        }
        values = {name: session.evaluate(expr) for name, expr in checks.items()}

        if args.screenshot:
            response = session.send("Page.captureScreenshot", {"format": "png"})
            data = response.get("result", {}).get("data")
            if data:
                args.screenshot.parent.mkdir(parents=True, exist_ok=True)
                args.screenshot.write_bytes(base64.b64decode(data))

        session.close()

        failures = []
        if "Fall Color Map" not in str(values["title"]):
            failures.append(f"unexpected title: {values['title']!r}")
        if not values["map_defined"]:
            failures.append("map is not defined")
        if not values["layer_exists"]:
            failures.append("trees-points layer is missing")
        if not isinstance(values["species_rows"], int) or values["species_rows"] == 0:
            failures.append("species panel has no rows")
        if not values["source_link"]:
            failures.append("sourceForFeature did not return a URL")
        if errors:
            failures.append(f"browser errors: {errors[:3]}")

        print(json.dumps(values, ensure_ascii=False, indent=2))
        if failures:
            print("\nFAIL", file=sys.stderr)
            for failure in failures:
                print(f"  - {failure}", file=sys.stderr)
            return 1
        print("\nOK")
        return 0
    finally:
        if process is not None:
            process.terminate()


if __name__ == "__main__":
    sys.exit(main())
