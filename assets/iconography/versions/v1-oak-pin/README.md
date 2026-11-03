# Icon v1 — "Oak pin" (Option E)

Map pin with a traced bur-oak leaf in a cream circle, plus the BotaniSense
bird-of-paradise badge. In production from 2026-11-01 to 2026-11-03.

- Source artwork: user-supplied Option E sheet (2752×1536 upload)
- Leaf: traced from that sheet with potrace; body and veins are separate paths
- Built with `scripts/build_icon_e.py`
- Commit that shipped it: 88a5fd4

Files here are the exact deployed rasters plus the leaf vector. Rebuilding is
`python3 scripts/build_icon_e.py` while `OAK_SVG` points at `leaf.svg`.
