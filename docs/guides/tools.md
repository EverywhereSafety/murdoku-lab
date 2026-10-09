# Native tool-solving harness

Use a unified `query_rollouts.jsonl` or exported query records from the [query guide](queries.md).
The evaluator reads only `query` from unified rows.
Run the harness from the Murdoku Lab checkout with its `.venv` active.
Model sampling needs an OpenAI-compatible endpoint; isolated Python tool calls
need Linux with `bwrap` and the separate scientific runtime described below.

`murdoku_lab/environment/protocol.py` defines the public function schemas and protocol.
`murdoku_lab/environment/tools.py` executes direct scratchpad actions using the existing
strict scorer. Call `murdoku` with `action=board/place/unplace/check/submit`.
Submission takes a `placements` mapping and `murderer` (or `answer` for victim-cell
cases). Include every character, including the victim. The native interface uses function calls and tool arguments.
Strict validation requires a complete correct arrangement and verdict. Training
can opt into terminal reward `0.2 * correct_positions / character_count +
0.8 * strict_solved`. Check reports only base-rule breaches; position correctness
is scored only when the episode ends.

The model gets `run_python` with NumPy, SciPy/HiGHS and OR-Tools CP-SAT. It builds its own constraints from visible clues. `murdoku_lab/environment/python.py` uses bubblewrap with no network,
an empty workspace and a read-only scientific runtime. Code executes separately
from the trusted scorer. Python exceptions return the traceback, failing model-code line number and a
five-line source excerpt, plus captured stdout. Tracebacks are bounded to 8k
characters and show package basenames rather than host paths. Python calls are
stateless, limited to 30 seconds and 2 GiB address space in the inline profile.
Workspace mode below provides persistent files and configurable execution budgets.

Create a separate Python >=3.11 scientific environment, install
`requirements/tools.txt`, and set `MURDOKU_TOOL_RUNTIME` to that environment's
absolute path (default `.tool-env`). This runtime must not contain the repository
or data. Tool execution and trusted puzzle grading use separate runtimes.

For example, from the checkout root:

```bash
python3 -m venv .tool-env
.tool-env/bin/python -m pip install -r requirements/tools.txt
export MURDOKU_TOOL_RUNTIME="$PWD/.tool-env"
```

`scripts/benchmark_tools.py` calls the shared text/vision runner in
`murdoku_lab/evaluation/tools.py`, also imported by the Agent Horizon demo. It uses the standard library's OpenAI-compatible HTTP
client and vLLM's `/tokenize` endpoint. Serve Qwen3.5-4B with auto tool choice and
`--tool-call-parser qwen3_xml`. Pass an endpoint JSON file with `base_url` and
`model`, a query or unified query/rollout JSONL input and a fresh attempt directory:

```bash
MURDOKU_TOOL_RUNTIME=/absolute/path/to/scientific-env \
.venv/bin/python scripts/benchmark_tools.py \
  --endpoint endpoint.json --input validation.rl.jsonl --out results \
  --tokens 10240 --turns 100 --context 65536 --context-clear \
  --clear-trigger 49152 --clear-target 32768 --generation-limit 0
```

Only the record's public messages and schemas are sent to the model. Private
case data remains in the trusted scorer. The default benchmark uses a 16,384-token
context, one attempt per case, temperature 0.7/top-p 0.9, up to 10k tokens per
turn (limited by remaining context) and a 32k cumulative stopping threshold.
With `--context-clear`, complete old assistant/tool groups are removed at the
configured trigger until the target size is reached. The puzzle, scratchpad and
external notes remain. Clearing removes complete interaction groups.
`--generation-limit 0` disables the cumulative generation cap. Both
final transcripts and partial progress are saved. Tool errors, terminal
submissions, exact-placement diagnostics and solved counts are reported
separately. Infrastructure failures must not be interpreted as model failures.
Missing images, paths outside the asset root and image checksum mismatches are
recorded as `invalid_input` before an environment starts. Initialization and cleanup
failures are recorded separately as infrastructure failures. These attempts have
`reward: null`; the summary reports `invalid_inputs` and `infrastructure_failures`.
Other cases continue, and each created environment is closed.

Keep held-out cases separate from training.


## Title/content memory

The tool protocol exposes `memory(action=write/read/list/delete, title=..., content=...)`.
Write creates or replaces a note; read returns its body; list returns only titles;
delete removes the note. Note content is not automatically added to prompts.
Each evaluated episode owns a separate atomic `<case-id>.memory.json` file in
its output directory, so context clears do not delete notes. This file persists
notes; it alone is not a full episode/environment recovery checkpoint.
The RL adapter implements the same note operations and includes note state in
its episode continuation checkpoint. Training segments before clears remain
trainable. The harness reuses Agent Horizon’s CPU-only tool package; veRL and GPU training
dependencies are not needed for generation or evaluation.


## Optional context feedback

Use `--context-feedback` with managed clearing to warn near the trigger and show
clear notifications with a bounded memory-title preview. `--warning-margin`
defaults to the per-turn token cap and `--memory-title-limit` defaults to 32.
The system notice is part of full-input token accounting and contains no note
bodies. This profile is opt-in; runs should not mix feedback settings between
cases. The environment imports the shared Agent Horizon context policy directly.


## Workspace mode

New queries enable a persistent Python workspace. The evaluator preserves each
query’s recorded system prompt, tool schemas and execution settings by default. Each puzzle has a private persistent `/workspace`: write/edit/read/list/delete
files with `workspace`, then execute a saved program with `run_python(path="solver.py")`.
Inline `code` is also supported; supply exactly one of `code` or `path`.
Files survive tool calls and context clears; interpreter variables do not.
Default execution time is 120 seconds, with an optional per-call `timeout` up to 300.
Elapsed time and actual budget are returned. Timeouts kill the isolated process but
preserve files already written. Programs cannot access the host grader or solution data.
Managed files and recovery snapshots support 128 files / 16 MiB; generated code retains
per-process limits, including 32 MiB per file (not a filesystem-wide quota).
No solver library is prescribed. Actual submissions still use `murdoku(action="submit", ...)`.
Legacy inline-only queries retain their 30-second execution budget.

New text and visual queries use the same prompt builder in `murdoku_lab/environment/protocol.py`.
The visual profile adds screenshot instructions and `case_note`. Teacher preparation
sets the assistant-turn limit and strict reward on this same contract.
`murdoku_lab/environment/replay.py` replays the original query messages, schemas and capabilities
unchanged, including previously collected records with legacy version metadata.

`--keep-input-protocol` is the default. To explicitly convert input records to
the current prompt, use `--no-keep-input-protocol --workspace --python-timeout 120`;
use `--no-workspace` only when intentionally selecting inline-only execution.
Protocol changes belong in separate evaluation outputs. Use `--asset-root` when
screenshot references are relative to another bundle directory. Existing attempt
artifacts are rejected to keep repeated samples independent.

## Evaluation protocol

A strict solve requires the complete correct placement and the requested verdict.
Run generated training, generated held-out validation and official transfer cases
as separate splits. Keep all views and attempts of a formal case in one split.

Record model/checkpoint, input view, tool schemas, sampling parameters and turn,
token, context and time budgets. Report strict success, submissions, partial
placement accuracy, turns and generated tokens. Distinguish model failures from
transport or execution errors.

For pass@k, use k independent attempts per case under the same configuration.
Replay accepted tool trajectories in a fresh environment. For comparisons, use
matching cases and budgets and retain unfinished attempts in the report.
