# Queries and model rollouts

The release uses one `query_rollouts.jsonl` for both text and visual records.
Each line has two fields:

```json
{"query": {"...": "environment record"}, "rollout": {"...": "model interaction"}}
```

`query` contains the model prompt, tool schemas, environment settings and trusted
case state used by the grader. `rollout` contains the recorded messages and tool
interactions. RL reads `query`; SFT reads the assistant outputs in `rollout`.
A query without a stored interaction has `"rollout": null`.

Split and observation type live inside `query`. Text and visual views of the same
formal case share `paired_case_id` and stay in the same split. Generated held-out
cases provide validation; official puzzles provide the transfer test.

Visual messages reference relative PNG paths in `images/`, distributed alongside
the JSONL. No separate query or rollout file is needed.

## Download

[Hugging Face dataset](https://huggingface.co/datasets/EverywhereSafety/murdoku-lab)

```bash
pip install -r requirements/data.txt
python scripts/download_data.py --repo EverywhereSafety/murdoku-lab --output data
```

The downloader fetches `query_rollouts.jsonl`, its image assets and license notices. Authenticate
with `hf auth login` or `HF_TOKEN` for access-controlled datasets. The downloader
resolves the requested revision once and writes a local `receipt.json` containing
the resolved revision and delivered file checksums. An existing different snapshot
or incomplete snapshot is rejected; choose a fresh directory. Files are
staged before publishing a new directory, so a copy failure preserves existing data.

## License

Generated queries and recorded rollouts are released by Everywhere Safety under
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). The dataset includes
the license text and retains the separate MIT notice for Microsoft Fluent Emoji artwork.
Project code remains AGPL-3.0-only.

## Export

```bash
python -m murdoku_lab.environment.release source.jsonl --output release/query_rollouts.jsonl
```

The exporter keeps the environment interface and recorded interaction, removes
collection bookkeeping and requires replay-qualified rollouts with original tool
schemas. It checks case-level split exclusivity and declared paired identities.
It accepts verified records; it does not rerun the model or replay on each export.
It rejects
internal paths or credential patterns in retained content for review. Copy the
referenced image assets into the release directory without changing their paths or bytes.

Generation produces verified cases, themed cases and text/visual observations;
these are intermediate inputs to the unified release. The grader retains the
verified solution, while model-facing messages contain the puzzle observations.

[Generate queries](queries.md) · [Trained model example](model.md) ·
[Repository overview](../../README.md)
