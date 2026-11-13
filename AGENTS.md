# AGENTS.md — TreeColors / Fall Color map

Project: TreeColors, live at `https://treecolors.botanisense.app/`.
Read **`docs/PROJECT_NOTES.md`** first — architecture, product decisions, and the
mistakes that already cost us a day. `docs/DATA_SOURCES.md` defines which file is
ground truth for every number.

## Hard rules

- **Numbers come from `web/species_stats.json`**, never from `data/output/qa/`
  (only 20 of the current cities have a QA file) and never typed by hand into
  artwork or copy.
- **Preview before deploy.** Build the asset, drop it in `web/preview/`, push,
  and show the URL. `/preview/` is excluded from `push.sh` and must never reach
  production. Cloudflare caches 4 h — use a new filename per revision.
- **Every layout change gets a browser check**: `python3 tests/ui/check_ui.py`.
- **No `/tmp` for anything reused.** Scratch lives in `data/work/`; large
  intermediates are not allowed in `/tmp` at all (tmpfs = RAM).
- **Batch only** for artwork runs; standard tier is for single samples.
- Merge duplicate species keys *before* generating artwork, then rebuild tiles.

## Layout of the repo

```
py/tree_pipeline/     fetch → process → export → web assets (CLI: python3 -m tree_pipeline)
scripts/              artwork, icons, promo, QA helpers
web/                  the site (index.html is the whole app; no build step)
docs/                 ground truth, promo spec, project notes
tests/ui/check_ui.py  headless-Chrome regression checks
assets/iconography/   shipped icons + their vectors, per version
```

## UI principles

1. Bottom sheet for species details (never an anchored popup); pan the map so
   the picked tree stays visible above it.
2. The search filter and the map agree: non-matching trees dim and are not
   clickable.
3. Locate → if the viewport has no data, zoom out (min z7) until it does; wait
   for the tiles first.
4. Legend order: title, colour key, then About · BotaniSense · install · locate.
5. Colour legend uses the literal palette from `export.py`, split 50/50 —
   ginkgo is a single `orange`.

## Copy principles

- Lead with the job ("find the colour"), not the artefact ("a tree map").
- Contrast beats feature lists: 15% vs 50% of trees turn.
- Define loaded terms once; keep city names in English inside Chinese copy.
- 小红书: no links, so the domain must be readable in the image; describe the
  tool, then what changed this year; one sentence about the BotaniSense app.

## Related skills

`treecolors-artwork` (plates, leaves, data rules), `treecolors-promo`
(Instagram / 小红书 images and captions).
