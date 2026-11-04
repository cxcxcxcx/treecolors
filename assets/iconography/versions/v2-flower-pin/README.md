# Icon v2 — "Flower pin" (Option C)

Map pin containing a small scene: a house, a flowering tree, an orange and a
yellow autumn tree, grass and soil, plus the BotaniSense badge. In production
from 2026-11-04.

- Source artwork: user-supplied Option C sheet, 2752×1536 (`source.jpg`)
- Built with `scripts/build_icon_flower.py` (vtracer colour trace + background
  knockout + brand flower composited into the badge)
- Large art → 1024/512/192/maskable/apple-touch
- **Favicons come from the sheet's simplified small variant**, not a downscale
  of the detailed art (see `favicon-32.png`)
- Tooling: `tools/setup_icon_tools.sh` recreates the Python 3.12 + vtracer venv
  (the cp314 wheel segfaults on some inputs)

Rebuild:
    bash tools/setup_icon_tools.sh
    python3 scripts/build_icon_flower.py --source source.jpg --prefix f
