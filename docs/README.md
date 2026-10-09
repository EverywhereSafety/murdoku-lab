# Murdoku Lab documentation

[Website](https://everywheresafety.github.io/murdoku/) ·
[Blog](https://everywheresafety.github.io/blog/murdoku-as-vhd/) ·
[Code and quickstart](../README.md)

For a first run, follow the quickstart to generate and solve one small case on
CPU. Then [export that case as a query](guides/queries.md),
[open the playable frontend](guides/play.md), or [run model interactions](guides/tools.md).
The [RL integration guide](guides/rl.md) connects those queries to Agent Horizon
once you have a model and GPU runtime.

## Guides

| I want to…                                             | Guide                                   |
| ------------------------------------------------------ | --------------------------------------- |
| Generate diverse text and visual queries               | [Queries](guides/queries.md)            |
| Download data and understand query + rollout artifacts | [Data](guides/data.md)                  |
| Connect queries, dynamics, tools and rewards to RL     | [RL integration](guides/rl.md)          |
| Sample, evaluate and replay model interactions         | [Tools and evaluation](guides/tools.md) |
| Play locally and inspect query bundles                 | [Frontend](guides/play.md)              |
| Run the trained solver example                         | [Model](guides/model.md)                |

## Reference

- [Architecture and code map](reference/architecture.md)
- [Formal puzzle model](reference/formal-model.md)
- [Reasoning and difficulty profiles](reference/reasoning-profiles.md)
- [Artwork catalog](reference/artwork.md)
