# Promo kit — Instagram / 小红书

Everything here is generated from the live site, so numbers never drift from the
app. One command rebuilds the whole set.

```bash
python3 scripts/make_promo.py            # both languages
python3 scripts/make_promo.py --lang zh  # Chinese only
```

Outputs land in `promo/instagram/` (English) and `promo/instagram/zh/`
(Chinese). Both are git-ignored, like the rest of `promo/`; the generator and
this document are tracked.

## The set

| File | Size | Purpose |
|---|---|---|
| `01-contrast` | 1080×1350 | Same bay, different streets: SF 15% vs Cupertino 50% of trees turn, with bars and green dots visible. |
| `02-species` | 1080×1350 | Four species that carry the season, with botanical plates. |
| `03-legend` | 1080×1350 | What each colour on the map means. |
| `04-city` | 1080×1350 | "City close-up" — what one neighbourhood looks like (Mountain View). |
| `05-backcover` | 1080×1350 | Share card: full domain, one line of promise. |
| `xhs-cover-a` | 1080×1440 | 小红书 cover, numbers hook: 旧金山 15% vs 库比蒂诺 50%. |
| `xhs-cover-b` | 1080×1440 | 小红书 cover, question hook: 湾区哪条街秋色最浓？ |
| `story` | 1080×1920 | Story / reel cover. |

Carousel order: 01 → 02 → 03 → 04, back cover last (or as the share card).
小红书 posts a 3:4 cover instead: use `xhs-cover-a` (numbers) as the default and
`xhs-cover-b` as the A/B alternative.

## Branding rules

- One consistent bottom bar on **every** slide.
- Left: a soft cream plate holding the TreeColors mark, **TreeColors** and the
  **full domain** in accent colour. This is the only highlighted element —
  小红书 cannot carry links, so the domain has to be readable.
- Right: the positioning line in two short lines (EN *AI that is actually useful
  / for plant lovers.*, 中文 *让 AI 对植物爱好者 / 真正有用。*) with the small
  flower + **by BotaniSense** underneath, all right-aligned. No card, no box —
  the product stays the loudest thing on the slide.
- No "map" in headlines, no city-count selling points.

## Short video (reel)

```bash
python3 scripts/record_reel.py --seconds 16   # promo/instagram/reel.mp4
```

The animation lives in **`assets/promo/reel.html`** (CSS keyframes over the real
promo PNGs), and `record_reel.py` records it from headless Chrome with the
DevTools screencast. That way what ships in the video is exactly the artwork we
deploy — no second implementation of the layout or the branding, which is what
went wrong in the first, ffmpeg-only version.

- Stage 1080×1920, five scenes, ~14 s, 30 fps, H.264 ~2 MB, silent.
- Frames are re-timed with their own screencast timestamps, so a slow machine
  produces a smooth file rather than a fast one.
- Music/voice is added in the app afterwards.

## Regenerating the screenshots

`promo/shots/*.png` are headless Chrome captures of the live site with the UI
hidden. Pattern used:

1. Open `https://treecolors.botanisense.app/` in headless Chrome at
   1000×1000 (the box is memory-tight; 1.5× DPR often OOMs).
2. `document.querySelectorAll('.map-overlay, .species-panel, .species-sheet, .maplibregl-ctrl').forEach(el => el.style.display = 'none')`
3. `map.jumpTo({center: [...], zoom: ...})`, wait ~12 s for tiles.
4. `Page.captureScreenshot`.

Keep the OSM basemap on — dots without a basemap are unreadable. Do **not**
filter out green trees: the contrast depends on both colours being visible.

## Copy

### English (Instagram)

```
Same bay. Three times the colour.

San Francisco: 15% of its street trees turn in autumn.
Cupertino: 50%. Twenty minutes apart.

The map shows every tree, species by species, so you can follow the purple dots
and skip the green ones.

Tap any tree for its species, a botanical plate and Wikipedia photos.

Free, no account → link in bio.

#bayarea #fallfoliage #autumn #cupertino #mountainview #sanfrancisco
#urbanforestry #citywalk #treelovers #dataviz
```

### 中文（小红书）

```
湾区的行道树，现在能在地图上一棵一棵看

颜色代表树种类型：
紫红 / 红 = 秋天会变色、颜色好看的
橙 = 银杏，一整条街一起变黄
绿 = 常绿，冬天也绿，可以跳过
褐 = 其他落叶树，颜色没那么出挑

点开任意一棵树，能看到树种、叶片图示、实拍照片，还有市政府自己的记录。
常见树种基本都配了图示，出门可以对照着认。

今年比去年：
· 城市更多了——San Francisco、Berkeley、Concord、Fremont、San Leandro、
  Palo Alto、Mountain View、Cupertino、San Jose，一共 9 个
· 树种展示更完整，界面也重做过

明年春天会再加一个「去哪看花」。

免费，不用注册：treecolors.botanisense.app

BotaniSense 的 App 也上线了，可以帮植物爱好者整理自己的植物照片，应用商店可下载。

#湾区 #MountainView #SanFrancisco #Cupertino #SanJose #湾区周末 #赏秋 #秋色 #城市漫步 #行道树
```

## Numbers used by the art (from `web/species_stats.json`)

| City | Trees | Turn | Share |
|---|---:|---:|---:|
| San Francisco | 95,051 | 14,489 | 15% |
| Palo Alto | 30,258 | 11,226 | 37% |
| San Jose | 204,593 | 93,635 | 46% |
| Cupertino | 16,584 | 8,253 | 50% |
| Berkeley | 30,316 | 15,650 | 52% |

Bay Area total (9 cities incl. Mountain View): 573,398 trees, 226,847 of them turn.

## Editing

- Text, sizes and colours: constants at the top of `scripts/make_promo.py`.
- A new slide: add a `build_*` function and call it in `main()`.
- A new city close-up: capture it into `promo/shots/`, then pass the path to
  `rounded_photo()`.
