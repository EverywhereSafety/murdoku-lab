"""Preset names preserve IDs, reproducibility, and the formal puzzle."""

import json
from dataclasses import replace
from pathlib import Path

from murdoku_lab.core.instance import Case
from murdoku_lab.core.name_library import FEMININE, MASCULINE, preset_theme
from murdoku_lab.environment.queries import make_record


def case():
    return Case.from_json(
        json.loads(
            (Path(__file__).parent / "fixtures/quality_base_case.json").read_text()
        )
    )


def test_library_covers_alphabet_with_matching_initials():
    for pool in (FEMININE, MASCULINE):
        assert set(pool) == set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        assert all(
            len(names) >= 2 and all(name.startswith(initial) for name in names)
            for initial, names in pool.items()
        )


def test_names_are_reproducible_unique_and_vary_between_seeds():
    puzzle = case()
    before = puzzle.to_json()
    themes = [preset_theme(puzzle, seed=seed) for seed in range(10)]
    assert themes[0] == preset_theme(puzzle, seed=0)
    assert len({tuple(th.names.values()) for th in themes}) > 1
    for theme in themes:
        assert all(name[0] == symbol for symbol, name in theme.names.items())
        assert len({name[0] for name in theme.names.values()}) == len(puzzle.characters)
        record = make_record(puzzle, theme)
        assert record["murdoku_case"]["solution"] == before["solution"]
        assert all(
            name in record["messages"][1]["content"] for name in theme.names.values()
        )
    assert puzzle.to_json() == before


def test_structural_gender_tags_select_matching_names():
    puzzle = case()
    a, b = puzzle.characters[:2]
    theme = preset_theme(
        replace(puzzle, tags={a: frozenset({"woman"}), b: frozenset({"man"})})
    )
    assert theme.names[a] in FEMININE[a] and theme.pronouns[a] == "she"
    assert theme.names[b] in MASCULINE[b] and theme.pronouns[b] == "he"
