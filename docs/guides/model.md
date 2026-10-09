# Trained solver example

[Project](../../README.md) · [Dataset formats](data.md) ·
[Training integration](rl.md)

[Murdoku Detective 4B](https://huggingface.co/EverywhereSafety/murdoku-detective-4b)
is the trained solver checkpoint.

The solver example demonstrates a small 4B model solving generated puzzles with
tools. Serve a checkpoint through the environment to record and inspect its
reasoning, actions and final submission.

## Use a checkpoint

Serve the checkpoint with its official tokenizer/processor and chat template.
Send the query's model-facing messages and native tool schemas to the endpoint.
Execute calls in the puzzle environment, append tool observations, and continue
until submission or the configured episode limit. Visual queries additionally
require resolving image references from the dataset's asset directory.

The [demo package](https://github.com/EverywhereSafety/agent-horizon/tree/refactor/murdoku-demo/examples/murdoku)
provides model sampling, SFT preparation and solver evaluation entry points.
Its commands accept local model/endpoint and data paths.

## Evaluate a trained solver

Use case-level held-out splits. Record board size, difficulty, context budget,
assistant turns, generated tokens, tool configuration and timeout. Report exact
solve rate and partial placement metrics separately. For pass@4, collect four
attempts per case rather than extrapolating from one trajectory.

Use the accompanying tokenizer, processor and configuration when serving a
checkpoint. Record the checkpoint and evaluation settings alongside your results.
