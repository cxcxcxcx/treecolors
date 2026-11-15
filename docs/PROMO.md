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
python3 scripts/record_reel.py                    # promo/instagram/zh/reel.mp4 + reel.mp4 (en)
python3 scripts/record_reel.py --lang zh --peek 1,6,13   # a few stills in data/work/reel/
python3 scripts/record_reel.py --data-only        # refresh numbers, then open the HTML for a live preview
```

The animation lives in **`assets/promo/reel.html`** — a motion piece, not a
slideshow of the stills. Open it in Chrome (`?lang=en` for English) to watch a
looping preview. Every motion is a CSS animation on one clock; the recorder
seeks that clock frame by frame (`window.render(t)`) and screenshots each
frame, so the file is perfectly smooth on a slow machine.

Storyboard (1080×1920, 18 s, 30 fps, silent — add music in the app):

| Time | Scene | Motion |
|---|---|---|
| 0–3.3 s | Hook: 在湾区住了六七年 / 才知道树会变色 | characters pop in, line 2 slams; grey map below turns colour with a circular wipe |
| 3.3–7.9 s | SF vs Cupertino | maps slide in, % counters and bars run, “×3” stamp |
| 7.9–11.4 s | The app | phone rises, map pushes in, tree count runs, legend chips pop out |
| 11.4–14.8 s | Tap any tree | finger tap + ripple, species sheet slides up, three plates fly out |
| 14.8–18 s | End card | icon, 找秋色。走过去。, domain, falling leaves |

- Numbers (percentages, ×N, tree count, plate count) come from
  `promo/instagram/reel-data.js`, which the recorder writes from
  `web/species_stats.json` via `make_promo.stats()`.
- Keep text out of the platform overlays: top ~150 px, bottom ~400 px, right
  ~130 px below mid-height.
- Copy for both languages is the `COPY` object in the HTML.
- Alternative openings live in `HOOKS` (`?hook=…`). `planted` (English):
  *Bay Area fall colour isn't random. / It was planted. / street by street*, and
  the grey map turns colour row by row instead of the circular wipe.
  `python3 scripts/record_reel.py --lang en --hook planted` → `reel-planted.mp4`.

### Voiceover

```bash
python3 scripts/voiceover.py --print            # show the script (numbers from species_stats.json)
python3 scripts/voiceover.py --check            # zh + en × Aoede, Sulafat, Achird; Gemini transcribes each result
python3 scripts/voiceover.py --lang en --voices Achird
```

Gemini TTS (`gemini-3.8-flash-tts`) on `GOOGLE_API_KEY`, the no-billing key.
The free tier allows **10 requests per day per model**: one voice in one language
is one request. Responses are cached in `data/work/voiceover/`, so re-mixing
after a script or timing change is free; only `--fresh` or a new voice costs
quota. Each line is placed at its scene's start time in the reel.

The `planted` opening has its own script lines (`HOOKS` in `voiceover.py`).
It was voiced with the second model, whose quota is separate. That model speaks
more slowly, so it is sped up to keep the voice in step:

```bash
python3 scripts/voiceover.py --lang en --hook planted --voices Aoede \
    --model gemini-2.5-flash-preview-tts --max-pause 0.3 --tempo 1.12
```

Outputs next to the reel: `reel-vo-<voice>.mp4` (video + voice) and
`vo-<voice>.wav` (voice only — upload the plain `reel.mp4` and add this plus
music in the app if you want to balance them yourself). With `--hook H`:
`reel-H-vo-<voice>.mp4` and `vo-H-<voice>.wav`.

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

### 小红书标题（≤20 字，feed 会截断，前 8 字要能立住）

| 用途 | 标题 | 字数 |
|---|---|---|
| 主推（配封面 C） | 在湾区住了七年，才知道树会变色 | 17 |
| 备选·利益点 | 湾区看秋色，别整条街白走 | 12 |
| 备选·疑问 | 湾区哪条街的秋色最浓？ | 11 |
| 备选·对比 | 同一片湾区，秋色差三倍 | 11 |

封面 C 上的字是同一句的变体（"在湾区住了六七年 / 才知道树会变色"），标题
不要逐字重复，换个语序即可。

### 中文（小红书）

```
湾区的行道树，现在能在地图上一棵一棵看

颜色代表树种类型：
紫红 / 红 = 秋天会变色、颜色好看的
橙 = 银杏，一整条街一起变黄
绿 = 常绿，冬天也绿，可以跳过
褐 = 其他落叶树，也会变，但颜色不显眼

点开任意一棵树，能看到树种、叶片图示、实拍照片，还有市政府自己的记录。
常见树种基本都配了图示，出门可以对照着认。

覆盖 9 个城市：San Francisco、Berkeley、Concord、Fremont、San Leandro、
Palo Alto、Mountain View、Cupertino、San Jose。

明年春天会再加一个「去哪看花」。

免费，不用下载 App，浏览器打开就能用：treecolors.botanisense.app

BotaniSense 的 App 也上线了，可以帮植物爱好者整理自己的植物照片，应用商店可下载。

#湾区 #MountainView #SanFrancisco #Cupertino #SanJose #湾区周末 #赏秋 #秋色 #城市漫步 #行道树
```

### English (Instagram)

```
Same bay. Three times the colour.

San Francisco: 15% of its street trees turn in autumn.
Cupertino: 50%. Twenty minutes apart.

The map shows every tree, species by species, so you can follow the purple dots
and skip the green ones.

Tap any tree for its species, a botanical plate, photos and the city's own
record.

Nine Bay Area cities so far, including San Francisco, Berkeley, Concord,
Fremont, San Leandro, Palo Alto, Mountain View, Cupertino and San Jose.

Free, nothing to install → treecolors.botanisense.app

#bayarea #fallfoliage #autumn #cupertino #mountainview #sanfrancisco
#urbanforestry #citywalk #treelovers #dataviz
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
