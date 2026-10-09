# Generate text and visual queries

Run these commands from the Murdoku Lab checkout with Python 3.11+.
Generation, solving and text export use the CPU package; PNG export also uses
Node.js and npm. A model endpoint is needed when adding LLM themes.

## Create cases

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m murdoku_lab.setter.generate --variant classic --size 6 --band easy \
  --seed 1 --n 1 --out data/cases.jsonl
python -m murdoku_lab.solver.oracle data/cases.jsonl --case-index 0
```

The oracle prints the solution and solver checks. Use `--size 8 --band medium`
to generate a larger case after this first run.

Generation establishes a solved formal puzzle and applies solution and quality
gates. The optional LLM setter adds rich semantic settings, names and labels.
Configure its endpoint using `config/llm.example.json` and `--llm-theme`.
`murdoku_lab/resources/theme_styles.txt` supplies setting prompts; `murdoku_lab/core/name_library.py`
supplies seeded names with distinct character initials.

## Export queries

```bash
# Text only
python -m murdoku_lab.setter.export_queries --input data/cases.jsonl \
  --out data/text-queries --views text

# Paired text and visual inputs
npm ci
python -m murdoku_lab.setter.export_queries --input data/cases.jsonl \
  --out data/paired-queries --views text,vision --artwork-style fluent
```

| Output | Contents |
|---|---|
| `text.rl.jsonl` | Text messages, tools and trusted environment fields |
| `vision.rl.jsonl` | Image references, public clues, tools and trusted environment fields |
| `public/` | Answer-free model inputs |
| `images/` | PNG observations |

`paired_case_id` joins views of the same case. Keep paired views in the same split.
Each export creates a new output directory; choose a new `--out` path when
exporting another bundle.
The image shows the board, object footprints, blocked cells and legends; the text
supplies clues, rules and public attributes.

## Send visual inputs to a model

```python
import json
from pathlib import Path
from murdoku_lab.environment.queries import model_inputs

bundle = Path("data/paired-queries")
record = json.loads((bundle / "vision.rl.jsonl").read_text().splitlines()[0])
inputs = model_inputs(record, asset_root=bundle)
```

`model_inputs` selects public messages and tool schemas and resolves local PNG
references. During an episode, `murdoku(action="board")` requests a current board
image; `frame_message` constructs the corresponding image message.

## Add semantic variety

```bash
python scripts/diversify_rl_data.py \
  --input data/text-queries/text.rl.jsonl --out data/themed \
  --endpoint http://localhost:8000/v1 --model YOUR_SERVED_MODEL --workers 4
```

`MURDOKU_LOCAL_API_KEY` supplies API authentication; `--api-key-var` selects another
variable. Themes retain the formal case. Asset selection is configured separately
through [the artwork catalog](../reference/artwork.md).

[Prepared queries and rollouts](data.md) · [Model example](model.md) ·
[Training integration](rl.md)

## Large boards and scene configuration

For larger boards, use the constraint-first strategy and a scene specification:

```bash
python -m murdoku_lab.setter.farm --strategy constraint-first --variant course --size 16 \
  --bands expert --n 1 --shots 3 --attempts 1 --workers 3 \
  --scene-spec config/scene_specs/paired_anchors_16.json \
  --out data/course-cases.jsonl
```

Scene specifications configure area counts, prop density and standable anchors.
Example:

```json
{"schema":"murdoku.scene_spec/1","area_count":8,"anchors_per_area":{"flag":1,"tee":1}}
```

The generator validates scene requirements and admits cases through solution,
difficulty and clue-quality gates. Semantic themes and artwork control the
presentation; the verified case supplies the gold answer.
