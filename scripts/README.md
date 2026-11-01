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


## Species artwork

```bash
python3 scripts/gen_plates.py --grid 3 --species "Acer rubrum" ...   # one-off sheet
python3 scripts/batch_plates.py plan     --mode leaf  --top 108      # cost + list
python3 scripts/batch_plates.py submit   --mode leaf  --top 108      # Batch API
python3 scripts/batch_plates.py status   --mode leaf
python3 scripts/batch_plates.py download --mode leaf                 # slice -> web/leaves
```

`--mode plate` fills the popup illustration, `--mode leaf` fills the species-list
thumbnail. Both send 3x3 species sheets (one billed image per nine species) and
slice them with a 2% inset. Coverage and cost maths must come from
`web/species_stats.json`; see `docs/DATA_SOURCES.md` for why `qa/` alone is
misleading.

```bash
python3 scripts/derive_qa.py            # reports for the legacy cities (qa/derived/)
python3 scripts/merge_duplicate_keys.py --dry-run   # common-name keys vs binomials
```

## Tests

```bash
PYTHONPATH=py python3 -m pytest -q py/tests
```
