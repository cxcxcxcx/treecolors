#!/usr/bin/env python3
"""Browser regression checks for the live map UI.

These are the checks that were being run by hand from /tmp; they now live in
the repo so a layout change cannot silently break the page again.

    python3 tests/ui/check_ui.py                     # against production
    python3 tests/ui/check_ui.py --url http://127.0.0.1:8767/
    python3 tests/ui/check_ui.py --keep-open         # leave the tab for inspection

Needs google-chrome-stable (or $CHROME_BIN) and the `websocket-client` package.
Exits non-zero if any check fails.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

DEFAULT_URL = "https://treecolors.botanisense.app/"
CHROME = os.environ.get("CHROME_BIN") or shutil.which("google-chrome-stable") or shutil.which("google-chrome")


class Cdp:
    def __init__(self, ws_url: str, timeout: int = 180):
        import websocket  # imported here so --help works without the dependency

        self.ws = websocket.create_connection(ws_url, timeout=timeout)
        self._id = 0

    def send(self, method: str, params: dict | None = None) -> dict:
        self._id += 1
        self.ws.send(json.dumps({"id": self._id, "method": method, "params": params or {}}))
        while True:
            message = json.loads(self.ws.recv())
            if message.get("id") == self._id:
                return message

    def eval(self, expression: str, await_promise: bool = False):
        result = self.send("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": await_promise,
        })
        value = result.get("result", {}).get("result", {})
        if value.get("subtype") == "error":
            raise RuntimeError(value.get("description", "evaluation failed"))
        return value.get("value")

    def close(self) -> None:
        try:
            self.ws.close()
        except Exception:  # noqa: BLE001 - best effort
            pass


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def start_chrome(port: int, profile: str) -> subprocess.Popen:
    if not CHROME:
        raise SystemExit("Chrome not found; set CHROME_BIN")
    process = subprocess.Popen(
        [CHROME, "--headless=new", f"--remote-debugging-port={port}",
         "--remote-allow-origins=*", f"--user-data-dir={profile}", "--no-first-run",
         "--disable-gpu", "--window-size=1400,900", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    for _ in range(60):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=1).read()
            return process
        except Exception:  # noqa: BLE001 - still starting
            time.sleep(0.5)
    process.kill()
    raise SystemExit("Chrome did not expose the debugging port")


def open_tab(port: int, url: str) -> str:
    request = urllib.request.Request(f"http://127.0.0.1:{port}/json/new?{url}", method="PUT")
    return json.load(urllib.request.urlopen(request))["webSocketDebuggerUrl"]


def wait_for_map(cdp: Cdp, seconds: int = 45) -> None:
    deadline = time.time() + seconds
    while time.time() < deadline:
        state = cdp.eval("document.readyState")
        rows = cdp.eval("document.querySelectorAll('.species-row').length") or 0
        if state == "complete" and rows > 0:
            return
        time.sleep(1)
    raise SystemExit("map never finished loading (no species rows)")


def checks(cdp: Cdp) -> list[tuple[str, bool, str]]:
    results: list[tuple[str, bool, str]] = []

    rows = cdp.eval("document.querySelectorAll('.species-row').length") or 0
    results.append(("species list renders", rows > 0, f"{rows} rows"))

    thumbs = cdp.eval("""(() => {
      const imgs = Array.from(document.querySelectorAll('img.species-leaf'));
      const loaded = imgs.filter(i => i.complete && i.naturalWidth > 0).length;
      return {total: imgs.length, loaded};
    })()""") or {}
    results.append(("leaf thumbnails load",
                    thumbs.get("total", 0) > 0 and thumbs.get("loaded", 0) > 0,
                    f"{thumbs.get('loaded')}/{thumbs.get('total')} loaded"))

    popup = cdp.eval("""(() => {
      const props = {species:'Acer rubrum', common_names:['Red maple'], city:'DC', deciduous:true,
                     fall_colors:true, beautiful_flowers:false, blooming_season:'Spring'};
      const html = buildPopupContent(props, 'Acer rubrum', null, false, [-77, 38]);
      const marks = [['chips', html.indexOf('info-chips')], ['plate', html.indexOf('plate-wrap')],
                     ['names', html.indexOf('info-meta')],
                     ['wiki', Math.max(html.indexOf('wiki-error'), html.indexOf('wiki-loading'))]];
      marks.sort((a, b) => a[1] - b[1]);
      return {order: marks.map(m => m[0]),
              title: (html.match(/<h4>([^<]*)<\\/h4>/) || [])[1] || '',
              plateHeader: html.includes('Botanical Plate')};
    })()""") or {}
    results.append(("popup order chips -> plate -> details -> wikipedia",
                    popup.get("order") == ["chips", "plate", "names", "wiki"],
                    str(popup.get("order"))))
    results.append(("popup title is a common name", popup.get("title") == "Red maple",
                    str(popup.get("title"))))
    results.append(("plate has no header line", popup.get("plateHeader") is False, ""))

    legend = cdp.eval("""(() => {
      const overlay = document.querySelector('.map-overlay');
      const toggle = document.getElementById('legend-toggle-button');
      if (!overlay || !toggle) return {error: 'missing legend'};
      if (!overlay.classList.contains('collapsed')) toggle.click();
      const collapsed = {
        height: Math.round(overlay.getBoundingClientRect().height),
        locate: !!document.querySelector('.legend-locate-button')?.offsetParent,
        info: !!document.getElementById('legend-info-button')?.offsetParent,
      };
      toggle.click();
      return {collapsed, expandedHeight: Math.round(overlay.getBoundingClientRect().height)};
    })()""") or {}
    collapsed = legend.get("collapsed") or {}
    results.append(("legend collapses to a slim bar",
                    collapsed.get("height", 999) < 90 and not collapsed.get("locate")
                    and not collapsed.get("info"),
                    f"{collapsed.get('height')}px"))

    detail = cdp.eval("""(() => {
      const button = document.querySelector('.species-info-button');
      if (!button) return {opened: false, reason: 'no button'};
      button.click();
      return new Promise(resolve => setTimeout(() => {
        const popup = document.querySelector('.maplibregl-popup');
        resolve({opened: !!popup,
                 title: popup ? (popup.querySelector('h4')?.innerText || '') : ''});
      }, 2000));
    })()""", await_promise=True) or {}
    results.append(("species row opens a detail popup",
                    detail.get("opened") and bool(detail.get("title")),
                    f"title={detail.get('title')!r}"))

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--wait", type=int, default=45)
    parser.add_argument("--keep-open", action="store_true")
    args = parser.parse_args()

    port = free_port()
    profile = tempfile.mkdtemp(prefix="treecolors-ui-")
    chrome = start_chrome(port, profile)
    cdp = None
    failures = 0
    try:
        cdp = Cdp(open_tab(port, args.url))
        cdp.send("Runtime.enable")
        wait_for_map(cdp, args.wait)
        for name, ok, detail in checks(cdp):
            print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail else ""))
            failures += 0 if ok else 1
    finally:
        if cdp:
            cdp.close()
        if not args.keep_open:
            chrome.terminate()
            shutil.rmtree(profile, ignore_errors=True)
    print(f"\n{failures} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
