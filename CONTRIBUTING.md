# Contributing

## Setup

```bash
cd py
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
```

System tools: `tippecanoe`, `pmtiles`, and (for local preview) `lighttpd`.

`OPENAI_API_KEY` is only needed for `python -m tree_pipeline enrich`.

## Workflow

```bash
cd py
python -m tree_pipeline list
python -m tree_pipeline fetch --city <slug>
python -m tree_pipeline process --city <slug>
python -m tree_pipeline enrich --all --dry-run
python -m tree_pipeline enrich --all
python -m tree_pipeline web-assets
python -m tree_pipeline tiles
```

```bash
PYTHONPATH=py python3 -m pytest -q py/tests
scripts/serve_local.sh 8767
scripts/verify_web.py --launch --url 'http://127.0.0.1:8767/?v=1'
```

## Adding a city

1. Add a `CitySpec` and `SourceSpec` in `py/tree_pipeline/cities.py`.
2. Prefer a source with an observed species field. Document the source URL in
   `homepage` and in `DATA_LICENSES.md`.
3. Fetch and process; inspect `data/output/qa/<slug>.json`.
4. If `missing_species > 0`, run enrichment and process again.
5. Run `web-assets` if you did not use the `all` command.
6. Build tiles and spot-check the city at zoom 12+.
7. Run `python3 scripts/readme_cities.py` so the README city table matches
   `web/species_stats.json` (CI fails on a stale table).

The full walk-through, with commands, is in `README.md` under "Add your city".

## Rules

- Never commit API keys, session cookies, or `.deploy.env`.
- Do not commit `data/raw/`, `data/output/`, or `web/trees.pmtiles`.
- Keep source-specific SQL/filters simple; city WAFs reject some multi-clause
  expressions. Filter invalid records in Python.
- Respect each publisher's data license. Code is MIT; data is not.
- Add a unit test for new name-normalization behavior.
