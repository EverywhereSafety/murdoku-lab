# Setting packs and skins

[Artwork](artwork.md) · [Daily case](../guides/daily.md) · [Architecture](architecture.md)

A setting pack gives a case its words and its look: room names, what each prop is called
and how it is drawn, wallpapers, floors, the board frame, titles, blurbs and the closing
paragraph. It never touches the puzzle. The content hash ignores themes, so dressing a case
cannot change its solution, certificate or difficulty (`tests/test_theme_invariance.py`,
`tests/test_settings.py`).

Eight packs ship in `murdoku_lab/setter/settings/`:

| Pack         | Setting                | Frame and look                                          |
| ------------ | ---------------------- | ------------------------------------------------------- |
| `manor`      | Alderwick Manor        | Walnut frame, damask, stripes and panelling, parquet     |
| `liner`      | RMS Aurelia            | Riveted hull frame, portholes and deco gold, teak deck   |
| `museum`     | The Halloway Museum    | Gilt frame, gallery red and portrait green, marble       |
| `theatre`    | The Rosalind Theatre   | Velvet frame, red curtains, blackbox, poster brick       |
| `chalet`     | Edelweiss Lodge        | Log frame, log walls, knotty pine, tartan                |
| `glasshouse` | Thornbury Glasshouses  | Iron frame, glass panes, trellis, terracotta             |
| `train`      | The Midnight Meridian  | Livery frame, walnut panels, night windows, green velvet |
| `library`    | St Aldhelm's College   | Leather frame, book walls, gothic windows, parquet       |

## Pack format: `murdoku.setting/1`

```json
{
  "schema": "murdoku.setting/1",
  "id": "library",
  "name": "St Aldhelm's College",
  "eyebrow": "End of term at St Aldhelm's",
  "titles": ["Overdue", "Silence, Please", "…"],
  "blurbs": ["The bell has rung for dinner. One scholar is still among the books, …"],
  "rooms": [
    {"name": "Reading Room", "suits": ["table", "chair", "shelf", "carpet"],
     "finish": "parquet", "wallpaper": "book_wall"}
  ],
  "objects": {"bed": "chesterfield sofa", "chair": "leather armchair", "…": "…"},
  "visual": {
    "accent": "#7d2a2e",
    "finishes": ["parquet", "herringbone", "planks", "carpet"],
    "wallpapers": ["book_wall", "oak_panel", "gothic_window", "crimson"],
    "variants": {"carpet": ["plum", "rose", "sage"], "planks": ["walnut", "oak"]},
    "frame": "library",
    "skins": {"bed": "chesterfield", "chair": "leather_armchair", "…": "…"}
  },
  "motives": ["a thesis had been copied, word for word, thirty years ago"],
  "epilogues": ["{murderer} and {victim} were the only two in the {area} … because {motive}."]
}
```

| Field       | Meaning                                                                                 |
| ----------- | --------------------------------------------------------------------------------------- |
| `name`, `eyebrow` | Setting name on cards and the line above a case title                              |
| `titles`, `blurbs` | Read before the case is solved, so they must carry no information (see checks)   |
| `rooms`     | At least nine. `suits` lists the prop kinds a room fits; `finish` and `wallpaper` dress it |
| `objects`   | A distinct noun for each of the 20 classic prop kinds                                   |
| `visual.accent` | Page accent while the case is open, also used for cards                             |
| `visual.finishes`, `variants` | Floor finishes the pack prefers, and the colourways to use for them  |
| `visual.wallpapers` | Optional: wallpapers for rooms that do not name one                          |
| `visual.frame` | A frame from `art/frames.py`                                                         |
| `visual.skins` | Prop kind → drawing. Kinds without a skin use the base drawing                       |
| `motives`, `epilogues` | The closing paragraph, shown only after the case is solved. Epilogues may use `{murderer}`, `{victim}`, `{area}` and `{motive}` |

## Dressing a case

`settings.dress(case, setting_id, salt="")` returns a `Theme`:

- **Rooms**: a maximum-weight matching gives each area the room that best suits the props
  inside it, so a piano lands in the music room. Ties follow the pack's order.
- **Cast**: suspects A–H are the recurring cast in `murdoku_lab/resources/cast.json`, with
  the same name and face in every case. The victim is always a member of the Vane family.
- **Title, blurb, epilogue**: chosen by hashing the setting, the case's content hash and the
  salt. The daily lock tries other salts to avoid repeating a title or a recent victim.
- **Look**: the pack's `visual`, plus each area's finish and wallpaper from its room.

## Checks a pack must pass

`settings.validate` runs whenever a pack loads:

- schema, required fields, at least nine distinct room names;
- room `suits` name real prop kinds; finishes, wallpapers, floor variants, skins and the
  frame all exist; colours are `#rrggbb`;
- every classic prop kind has a noun, and nouns are distinct;
- titles and blurbs mention no room, object, cast member or spatial word (north, left,
  beside, corner, row, alone, …);
- epilogues use only the four known fields.

## Adding a pack

1. Copy a pack in `murdoku_lab/setter/settings/` and rename `id`. Write the rooms with their
   `suits` first: they decide which room each area becomes.
2. Reuse existing skins, wallpapers and a frame, or add new ones (below).
3. Run the checks and look at the result:

   ```bash
   python -m pytest tests/test_settings.py tests/test_theme_invariance.py
   python scripts/build_showcase.py               # three cases per pack
   python scripts/art_gallery.py --showcase outputs/showcase/cases.jsonl
   python scripts/check_vision_legibility.py      # outputs/legibility/report.md
   python -m murdoku_lab.visual.art.design_tokens --write
   ```

   The gallery (`outputs/gallery/themes.html`) shows each pack's boards, object sheet and
   wall strips. The design-token step adds the pack's accent and frame to the web tokens.
4. To use the pack for daily cases, add its id to `settings` in the season config.

## Skins, wallpapers and frames

Each module in `murdoku_lab/visual/art/skins/` (one per setting) exports:

```python
SKINS = {"chesterfield": chesterfield, ...}  # drawer(w, h) -> SVG markup
WALLPAPERS = {"book_wall": book_wall, ...}   # pattern(pid) -> <pattern id=pid …>
TALL = {"grandfather_clock", ...}             # may rise in front of the wall above
STRETCH = {"reading_table", ...}              # drawn once over a rectangular footprint
GRADIENTS = {"leather": ("#9a5634", "#6f3a22"), ...}  # mk-g-* gradients the drawings use
```

The registry in `skins/__init__.py` merges every module and refuses a skin name defined
twice or a gradient defined twice with different stops.

- **Drawers** work in their footprint's frame, (0, 0)–(w, h), where w and h are multiples of
  100. The floor contact sits around h − 12, light comes from the upper left and outlines
  are 2.2 px ink. Tall skins may rise up to `OVERHANG` (36 px) above the footprint.
  Helpers such as `shadow`, `block`, `armchair`, `bed`, `wheel` and `lying` are in
  `skins/_kit.py`.
- **Wallpapers** are drawn on the wall's front face. Only the band from y≈7 to y≈19 of each
  tile is visible between the wall cap and the skirting board, so put the motif there.
- **Frames** live in `art/frames.py`: `FRAMES[name] = {fill, edge, rim, axis, halo, caps}`,
  where `fill` names a gradient, `axis` colours the coordinate letters and `halo` outlines
  them so they stay legible over tall furniture.

Every skin must draw at every footprint (`test_every_skin_draws_at_every_footprint`) and
stay recognisable in exported images: `scripts/check_vision_legibility.py` rasterises each
setting's twenty object drawings side by side and fails when two of them are closer than
an RMS distance of 0.06 between their 16×16 colour signatures.
