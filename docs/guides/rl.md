# Use Murdoku queries for RL

Murdoku Lab supplies the **query, puzzle dynamics, tools and gold reward**.
[Agent Horizon](https://github.com/EverywhereSafety/agent-horizon) runs long-horizon
episodes and connects them to veRL training. The optional Murdoku demo is the
bridge between these two packages.

First [generate and export a small case](queries.md), then follow the setup
below in order: prepare train/validation queries, install the bridge, convert
the queries to Parquet, and launch a training update.

## What a task must provide

For another task, use Agent Horizon's [environment contract](https://github.com/EverywhereSafety/agent-horizon/blob/main/docs/guides/environments.md).
There are two routes: embed executable dynamics and tool implementations in each
query, or register a task environment once and let queries provide its initial state.
Murdoku uses the registered-environment route.

| Requirement | What Murdoku provides | Source |
| --- | --- | --- |
| Initial query | Public rules, clues and text / board PNG | `murdoku_lab/environment/queries.py` |
| Prompt and tool schemas | One prompt builder with text / vision observation profiles | `murdoku_lab/environment/protocol.py` |
| Initial environment state | Board, characters, clues, semantic theme and answer reference | `murdoku_lab/core/instance.py`, `murdoku_lab/core/theme.py` |
| Dynamics | Persistent placements and marks; submit ends the episode | `murdoku_lab/environment/state.py`, `murdoku_lab/environment/actions.py` |
| Reward | Placement and verdict checked against the solution reference | `murdoku_lab/environment/scoring.py`, `murdoku_lab/environment/rewards.py` |
| Replay | Fresh execution using the exact collected query and tool configuration | `murdoku_lab/environment/replay.py` |
| RL environment plugin | `environment_type="murdoku"`, isolated grader and recovery | Agent Horizon demo's `murdoku_demo/murdoku.py` |

The generic RL core has no puzzle-specific imports. Common Python execution,
workspace, notes and context notices come from its CPU-only `long_horizon_rl`
package. `MurdokuPythonTool` subclasses the shared Python tool to select the task
runtime and memory budget. Puzzle transitions and grading have one implementation,
used by both the local harness and the isolated training grader.

## Query format

An exported record has this shape; `murdoku_case` and `murdoku_theme` contain the
complete serialized task objects:

```json
{
  "prompt_uid": "case-id",
  "paired_case_id": "case-id",
  "environment_type": "murdoku",
  "murdoku_observation": "text",
  "messages": [
    {"role": "system", "content": "Task instructions"},
    {"role": "user", "content": "Board, people, rules and clues"}
  ],
  "tool_schemas": [{"name": "murdoku", "parameters": {"type": "object"}}],
  "murdoku_case": {},
  "murdoku_theme": {},
  "python_workspace": true,
  "python_timeout_seconds": 120,
  "agent_info": {"max_turn": 1000},
  "murdoku_reward": {"mode": "strict"}
}
```

Generate complete records with `make_record(case, theme)` or the export CLI;
use the generated schemas rather than the abbreviated schema above.
`messages` and `tool_schemas` are model-facing. `murdoku_case` includes the hidden
answer reference and remains in the trusted environment. For a direct model call,
`model_inputs(record, asset_root=...)` extracts only public inputs and resolves PNGs.

| Tool | Effect |
| --- | --- |
| `murdoku` | Inspect, place/unplace, mark/unmark, check basic rules or submit |
| `workspace` | Read/write/edit episode-private files |
| `run_python` | Execute inline code or a saved path in an isolated process |
| `memory` | Persist and retrieve title/content notes |
| `case_note` | Optional visual explanation; adds no grading feedback |

A submit maps every character to a cell and supplies the requested verdict.
Strict reward is `1` for the complete correct solution and `0` otherwise.
Optional `placement_shaped` reward with weight `w` is
`w * correct_cells / character_count + (1-w) * strict_solved`.
Checks return basic placement-rule feedback. Grading metadata stays separate from
model-facing replay messages.

## Export training and validation queries

Split verified cases before exporting so each case's text/vision variants and
rollouts belong to the same split. From the Murdoku Lab checkout:

```bash
source .venv/bin/activate
npm ci
python -m murdoku_lab.setter.export_queries \
  --input data/train.cases.jsonl --out data/train-queries
python -m murdoku_lab.setter.export_queries \
  --input data/validation.cases.jsonl --out data/validation-queries
```

Each bundle contains `text.rl.jsonl`, `vision.rl.jsonl` and referenced PNG assets.
Current Agent Horizon veRL training uses the text records. Visual records support
screenshot sampling and replay; visual training needs a multimodal backend adapter.

## Install the RL bridge

Set up Agent Horizon's pinned GPU runtime, then switch to its demo branch and
install the bridge in that runtime:

```bash
# From the Agent Horizon checkout:
git switch refactor/murdoku-demo
source .venv/bin/activate
export LONG_HORIZON_MURDOKU_ROOT=/absolute/path/to/murdoku-lab
python -m pip install -e . -e "$LONG_HORIZON_MURDOKU_ROOT" -e examples/murdoku
python -m pip check
export LONG_HORIZON_TOOL_RUNTIME=/absolute/path/to/scientific-python-runtime
```

The three editable packages are resolved together from these checkouts. This CPU
package installation does not install the GPU training stack; bootstrap selects
that pinned runtime separately. To check the local combination without GPUs:

```bash
python -m pip check
python -c 'import long_horizon_rl, murdoku_lab, murdoku_demo; print(long_horizon_rl.__file__, murdoku_lab.__file__, murdoku_demo.__file__)'
python -c 'from importlib.metadata import entry_points; p = [e for e in entry_points(group="long_horizon_rl.environments") if e.name == "murdoku"]; assert len(p) == 1; print(p[0].load())'
```

For a remote installation of the same package combination, install all three
matching release tags together:

```bash
python -m pip install \
  "long-horizon-rl @ git+https://github.com/EverywhereSafety/agent-horizon.git@v0.1.0" \
  "murdoku-lab @ git+https://github.com/EverywhereSafety/murdoku-lab.git@v0.1.0" \
  "long-horizon-murdoku-demo @ git+https://github.com/EverywhereSafety/agent-horizon.git@v0.1.0-murdoku#subdirectory=examples/murdoku"
```

Murdoku Lab's `.venv` is the trusted grading runtime. Override it with
`MURDOKU_ENV_RUNTIME` if needed. The tool runtime is a separate environment
**directory** containing `bin/python`; install `requirements/tools.txt` there.
Agent Horizon's `scripts/bootstrap.sh` creates `.sandbox-env` with the
scientific dependencies, so you can set
`LONG_HORIZON_TOOL_RUNTIME="$PWD/.sandbox-env"` from that checkout.
Model-written Python runs separately from puzzle grading. Deployment-specific
read-only mounts use `LONG_HORIZON_SANDBOX_BINDS` (a JSON array of absolute paths).

Standalone sampling selects `MURDOKU_TOOL_RUNTIME`, falling back to
`LONG_HORIZON_TOOL_RUNTIME` and then `.tool-env`. The shared training tool uses
`LONG_HORIZON_TOOL_RUNTIME`.

## Prepare data and run a first update

From the Agent Horizon demo checkout, with the plugin installed:

```bash
python scripts/prepare_queries.py \
  "$LONG_HORIZON_MURDOKU_ROOT/data/train-queries/text.rl.jsonl" \
  --output outputs/data/train.parquet
python scripts/prepare_queries.py \
  "$LONG_HORIZON_MURDOKU_ROOT/data/validation-queries/text.rl.jsonl" \
  --output outputs/data/val.parquet
export LONG_HORIZON_TRAIN_FILE="$PWD/outputs/data/train.parquet"
export LONG_HORIZON_VAL_FILE="$PWD/outputs/data/val.parquet"
export LONG_HORIZON_MODEL_PATH=/absolute/path/to/model
bash scripts/train_long_horizon.sh \
  data.train_batch_size=2 actor_rollout_ref.actor.ppo_mini_batch_size=2 \
  actor_rollout_ref.rollout.n=4 trainer.total_training_steps=1
```

Agent Horizon's [training guide](https://github.com/EverywhereSafety/agent-horizon#get-started)
explains model/runtime configuration, context limits, asynchronous rollout and
GPU layout. Queries provide task state and grading; GPU allocation, model serving
and scheduling come from the deployment.

## Reuse query + rollout data

The [unified JSONL](data.md) stores `query` and an optional accepted
`rollout` together. RL consumes the query and samples fresh episodes; SFT consumes
verified assistant messages and tools from train rollouts. Agent Horizon's loader
accepts nested query rows as well as raw query JSONL.

Text and visual replay share `murdoku_lab/environment/replay.py`. It preserves collected
prompts and schemas, including records carrying legacy protocol metadata. New
queries use one current protocol, configured by observation type and capabilities.
See [tool harness](tools.md), [artifact formats](data.md) and the
[dataset guide](data.md) for local execution and released data.
