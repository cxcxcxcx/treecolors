# Data sources — what is ground truth

Several files look like they describe the same thing. They do not have equal
authority. Read this before computing any number about the map.

## Authority order

| Rank | File | What it is | Use it for |
|---|---|---|---|
| 1 | `data/output/geojson/trees_<slug>.geojson` | Every kept tree: lng/lat, `species`, `species_key`, `color`, `source_key`, traits | The actual map content. Tiles are built from this. |
| 2 | `web/species_stats.json` | Per-city species list with counts, colour, `key`, `plate`, `leaf`; generated from the GeoJSON by `web-assets` | **All coverage and cost maths.** The site reads this file. |
| 3 | `data/output/qa/<slug>.json` | Pipeline report for one city: raw records → kept, deduped, outside bbox, invalid placeholders, species top | Data-quality triage. Only exists for cities in the pipeline config. |
| 4 | `data/output/qa/derived/<slug>.json` | Report computed after the fact from the GeoJSON | Coverage sanity checks for the 11 legacy imports. **Not** raw accounting. |
| 5 | `data/tree_info/species_info.json`, `species_aliases.json` | Species knowledge base: traits, common names, alias → canonical key | Resolution, display names, artwork prompts |

## Rules

- **Never compute coverage from `qa/`.** It exists for the 28 cities in the
  registry; the 11 legacy imports (Bay Area, Los Angeles, San Diego, Vancouver —
  1,043,559 trees) predate the city config, so counting from QA silently drops
  about 16% of the map (that mistake produced an 84.4% figure where the real
  number was 75.4%).
- **`qa/derived/` is derived, not authoritative.** `raw_records`, `deduped`,
  `invalid_placeholders` are `null` there because the raw source is gone.
- **`species_stats.json` is regenerated**, so run `web-assets` after any
  `process` run, and check it in.
- **Artwork is keyed by `slug(canonical species key)`**, e.g.
  `Acer rubrum` → `acer_rubrum.png`. Renaming a species key means renaming the
  artwork files too (`scripts/merge_duplicate_keys.py` does this).
- **Missing artwork is normal.** The UI hides the plate block / leaf thumbnail
  when the file is absent; nothing breaks.

## Regenerating things

```bash
cd py
python3 -m tree_pipeline process --all      # raw → GeoJSON + QA
python3 -m tree_pipeline web-assets         # GeoJSON → species_stats.json
cd .. && ./build_tiles.sh                   # GeoJSON → web/trees.pmtiles
python3 scripts/derive_qa.py                # derived QA for legacy cities
./push.sh                                   # rsync web/ to the server
```

Coverage check (single source of truth):

```bash
python3 - <<'PY'
import json, os
stats = json.load(open('web/species_stats.json'))
have = {p[:-4] for p in os.listdir('web/plates')}
slug = lambda k: ''.join(c if c.isalnum() else '_' for c in (k or '').lower()).strip('_')
total = covered = 0
for city in stats['cities']:
    for s in city['species']:
        total += s['count']
        covered += s['count'] if slug(s.get('key')) in have else 0
print(f'{covered/total*100:.1f}% of {total:,} trees have a plate')
PY
```
