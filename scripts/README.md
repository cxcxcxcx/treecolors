# Reusable development scripts

These are the checks that were useful while building the multi-city map. They
are intentionally small and dependency-light.

## Local preview (PMTiles needs HTTP Range)

```bash
scripts/serve_local.sh 8767
```

`python3 -m http.server` is not enough: PMTiles asks for byte ranges. Use
`lighttpd` (the script checks for it).

## Browser smoke test

```bash
# Chrome already running with --remote-debugging-port=9222
scripts/verify_web.py --url 'http://127.0.0.1:8767/?v=1'

# Or let the script launch headless Chrome
scripts/verify_web.py --launch --url 'http://127.0.0.1:8767/'
```

Checks: page title, `map` exists, `trees-points` layer exists, species panel has
rows, a known `source_key` resolves to a source URL, and no uncaught browser
errors. Optional `--screenshot out.png`.

## Data QA

```bash
python3 scripts/qa_summary.py
python3 scripts/qa_summary.py --missing-limit 20
```

Reads `data/output/qa/*.json` and prints kept/invalid/outside/missing counts.

## Tiles

```bash
python3 scripts/check_tiles.py
```

Verifies the PMTiles file exists, is not tiny, has max zoom 12, and has bounds.

## Tests

```bash
PYTHONPATH=py python3 -m pytest -q py/tests
```
