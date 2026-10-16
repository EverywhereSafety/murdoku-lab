# Artwork

Murdoku Lab draws every board itself, as SVG, from the public observation. Nothing in
`murdoku_lab/visual/art/` can see a solution. Callers import from `murdoku_lab.visual.art` only.

## Styles

| Style | Use | Status |
|---|---|---|
| `casebook` | Player app, previews, opt-in RL exports; selectable in the Lab | Default for Python callers (`DEFAULT_STYLE`) |
| `classic` | The Lab's default style; published RL datasets | Legacy renderer, `art/legacy.py` |
| `art`, `diagram`, `fluent` | Published RL datasets | Legacy renderer, `art/legacy.py` |

`tests/test_legacy_art.py` guards the legacy styles with 351 SVG digests, so casebook work can
never change them by accident. When the legacy renderer changes on purpose, as the Classic
presentation update did, regenerate the digests: `python tests/test_legacy_art.py --write`.

RL exports choose their style explicitly and keep it. `export_queries` and `farm` take
`--artwork-style` (default `art` and `classic`, unchanged until casebook exports are evaluated
with a vision model). The vision record stores `artwork_style`, and every later frame of its
episode is drawn in that style (`styles.record_style`). Records without the field are drawn as
`art`, exactly as before.

```bash
python -m murdoku_lab.setter.export_queries --input cases.jsonl --out bundle \
  --views text,vision --artwork-style casebook
```

Casebook PNGs are rasterised with the bundled OFL fonts only (`raster.profile_for`), so they
match on every machine. Legacy styles keep system fonts. A vision bundle's `manifest.json`
records `artwork`: style, renderer version, resvg version and the font digest.

## The casebook board

A 3/4 dollhouse floor plan. The geometry contract is shared with every frontend: `CELL=100`,
`PAD=40`, one `g.cell-hit[data-cell]` per square, axis labels at `x=20` and `y=25`.

- **Floors** are materials (oak planks, herringbone, carpet, checker, terrazzo, …). Touching
  rooms always differ by at least ΔE00 12. A setting may prefer some colourways of a finish.
- **Walls** show a wallpapered south face under every horizontal wall, then a capped top.
  Painting is row by row, so furniture in a row stands in front of the wall behind it.
- **Props** are drawn in `props.py`. Each drawer works in its footprint frame `(0,0)–(w,h)` and
  keeps its base inside the footprint. Tall pieces may rise `OVERHANG=36` above it.
- **Plaques** carry every area's number and, when it fits, its name.
- **Frames** come from `frames.py` and are themed per setting. Ornaments sit only at cell
  boundaries and in corners. Axis letters carry a halo, so they stay legible over tall furniture.
- **Layers**: `scene_svg(..., layers=STATIC_LAYERS, cell_labels="none")` draws the static scene
  the player app paints once. People, notes, axes and hit targets are the dynamic layers.
- **Night**: `theme="night"` dims the board and keeps the frame.

`board_svg` adds an object key and a ground key under the board. `observation_svg` is the
full case-file page with clues. Both draw each key glyph with the board's own drawer and skin.

## Setting packs

A setting pack, `murdoku_lab/setter/settings/<id>.json` (`murdoku.setting/1`), changes the
words and the look of a case, never its maths. Eight ship today: manor, liner, museum, theatre,
chalet, glasshouse, train and library.

| Field | Meaning |
|---|---|
| `rooms[]` | `name`, the kinds it `suits`, a floor `finish` and an optional `wallpaper` |
| `objects` | A noun for each of the 20 classic kinds |
| `titles`, `blurbs` | Pre-solve text. It must name no room, object, person or direction |
| `motives`, `epilogues` | Post-solve text, with `{murderer}`, `{victim}`, `{area}` and `{motive}` |
| `visual.skins` | kind → drawing, so the picture matches the noun |
| `visual.frame` | Board frame (`frames.FRAMES`) |
| `visual.finishes`, `visual.variants` | Allowed floors and preferred colourways |
| `visual.wallpapers` | Fallback wallpapers for rooms without one |
| `visual.accent` | Accent colour for the player page and share cards |

`settings.dress(case, setting_id)` assigns rooms by weighted matching (a piano lands in the
music room), names the recurring cast and returns a `Theme`. `settings.validate` runs the lint.
`tests/test_settings.py` checks every pack.

## Skins

Theme drawings live in `art/skins/<setting>.py`. Each module exports:

```python
SKINS = {"deck_chair": drawer, ...}       # drawer(w, h) -> SVG in the footprint frame
WALLPAPERS = {"portholes": pattern, ...}  # pattern(pid) -> <pattern>; use _kit.face_pattern
TALL = {...}                              # rises in front of the wall behind it
STRETCH = {...}                           # drawn once over a rectangular footprint
GRADIENTS = {"teak": (top, bottom), ...}  # extra mk-g-* gradients
```

`skins/__init__.py` merges the modules and rejects duplicate names. `skins/_kit.py` holds the
shared helpers (`block`, `bed`, `armchair`, `lying`, `wheel`, `outlined`, `face_pattern`). The
visible part of a wallpaper is about `y` 7–19: the wall cap covers the top and the skirting
board covers the bottom. Every skin must draw well-formed SVG at 1×1, 2×1 and 1×2, and at
larger footprints when it stretches.

## Legibility gate

Vision models read these boards, so `art/legibility.py` checks each one:

- every prop appears in the key;
- every area has a plaque;
- text meets WCAG AA (axes on every frame, plaque names on brass and wood);
- touching floors differ by ΔE00 ≥ 10;
- coordinates stay at least 9px tall at 1568 and 1024px wide.

`scripts/check_vision_legibility.py` also rasterises each setting's 20 object drawings and
fails when two look alike. It writes `outputs/legibility/report.md`.

```bash
python scripts/check_vision_legibility.py --records outputs/showcase/cases.jsonl
```

## Cards, thumbnails, brand and tokens

- `art.share_card_svg(card, layout)` draws sticker-style share cards (1200×630 `og`, 1080×1350
  `portrait`) from public facts only. They never name the culprit or show a square.
- `art.thumbnail_svg(observation, px=320)` draws the static scene for a case library.
- `brand.py` draws the mascot, the Everywhere Safety donut-and-friend mark with a deerstalker on
  the donut, and the app icon. `scripts/build_brand_assets.py` writes the favicon, app icons
  and mascot SVGs to `web/public/`. Set `resources/brand.json` to `placeholder` to swap in a
  neutral mark.
- `python -m murdoku_lab.visual.art.design_tokens --write` exports the palettes, geometry, token
  layout and per-setting accents to `web/src/generated/tokens.{json,css}`.
  `tests/test_design_tokens.py` fails on drift.

## Previews

```bash
python scripts/build_showcase.py            # one 6×6, 7×7 and 8×8 case per setting
python scripts/art_gallery.py --showcase outputs/showcase/cases.jsonl
open outputs/gallery/themes.html
python -m murdoku_lab.visual.server --records outputs/showcase/cases.jsonl   # play them in the Lab
```

## Legacy Fluent emoji assets

The `fluent` style uses 47 Microsoft [Fluent Emoji Flat](https://github.com/microsoft/fluentui-emoji)
SVGs. The MIT license and attribution are kept in
[`murdoku_lab/visual/assets/fluent/LICENSE`](../../murdoku_lab/visual/assets/fluent/LICENSE).
`catalog.json` lists each asset's concept, aliases and compatible formal roles. Search it with
`python -m murdoku_lab.visual.asset_catalog --query cactus --role plant`. Selection defaults are
in `murdoku_lab/resources/visual_assets.json`, and the chosen mapping is stored in
`Theme.assets`.
