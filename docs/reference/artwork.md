# Color artwork

Murdoku Lab bundles 47 Microsoft [Fluent Emoji Flat](https://github.com/microsoft/fluentui-emoji)
SVGs. Their MIT license and attribution are retained in
[`murdoku_lab/visual/assets/fluent/LICENSE`](../../murdoku_lab/visual/assets/fluent/LICENSE).

## Catalog

Each entry in `murdoku_lab/visual/assets/fluent/catalog.json` records an asset ID, concept,
category, aliases, source and compatible formal roles. Search local candidates:

```bash
python -m murdoku_lab.visual.asset_catalog --query cactus --role plant
```

Geometry, object footprints and standability are defined by the formal board.
The selected concept supplies the public object label and image; board and legend
use the same asset. Rectangular multi-cell objects render inside their formal
footprint frame.

## Selection

Artwork defaults live in `murdoku_lab/resources/visual_assets.json`. Pass an
`asset_config` dictionary to `llm_theme` to override them:

| Setting | Values |
|---|---|
| `enabled` | Enable catalog selection |
| `pack` | `fluent-color` |
| `selection` | `llm` or `deterministic` |
| `compatibility` | `explicit_formal_roles` or `prop_classes` |
| `search_limit` | Candidate count per prop |
| `allow_missing` | Permit original-art fallback for missing roles |
| `online_search` | `false`: retrieval uses the bundled catalog |

The LLM selects IDs from supplied candidates. Exact-role mode uses curated
object-role assignments; class mode uses standable/blocking compatibility.
Distinct prop IDs receive distinct concepts. Repeated occurrences share artwork.
The mapping is stored in `Theme.assets` and survives JSON export and board requests.

## Render

```bash
python -m murdoku_lab.setter.export_queries --input cases.jsonl --out bundle \
  --views text,vision --artwork-style fluent
```

Preview assets and boards through the [frontend](../guides/play.md). To extend the pack,
add licensed source files and catalog metadata, retain upstream attribution, and
validate labels, compatibility and rendering at the intended cell sizes.

Other color libraries include [Twemoji](https://github.com/twitter/twemoji),
[OpenMoji](https://openmoji.org/) and [Noto Emoji](https://github.com/googlefonts/noto-emoji).
Review each library's artwork license before adding assets.
