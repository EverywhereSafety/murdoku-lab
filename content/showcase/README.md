# Frozen player showcase

`player-bundles.jsonl` contains the 24 `kind: "themed"` bundles listed by
`murdoku/exp/cases/index.json` in the website PR
[EverywhereSafety.github.io #1](https://github.com/EverywhereSafety/EverywhereSafety.github.io/pull/1),
commit `6e2e41c`. They were copied from the reviewed website checkout on 2026-10-18.
The JSON bundles are unchanged from that commit; later player fixes redraw their SVGs.

Each of the eight settings has a 6×6, 7×7 and 8×8 puzzle. These are the existing
release puzzles, not newly generated replacements. The original generator JSONL lived
under the ignored `outputs/showcase/` directory and was absent from the source checkout.
Freezing the complete player bundles preserves their IDs, content hashes, public clues,
metadata and sealed solutions/hints so a clean build keeps the same puzzles and saves.
These bundles are player-format release inputs, not formal cases for generator research
or training. As with every static player bundle, sealing prevents accidental spoilers;
it does not make the embedded answers secret from a determined reader.

`python -m murdoku_lab.visual.play_export` includes these bundles alongside the tutorial
and five classic cases. It redraws day/night scenes and thumbnails from each bundle's
public observation using the current renderer; no old SVG files are needed. A missing
release input fails the default export before replacing existing output.

For a custom library, `--records path/to/cases.jsonl` uses explicit formal case/theme
records in place of this showcase. Generate and review replacements separately; do not
regenerate puzzles as an incidental part of a website build.
