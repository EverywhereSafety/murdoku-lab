"""The solver-facing artefact must be prose, and must not contain its own answer.

The architecture: the mathematics is the *warrant* (uniqueness, guess-freedom, difficulty), the
natural language is the *artefact* a solver is given, and the key is kept in a separate file. That
separation has to be structural rather than a convention — "just don't read the solution field" is not
a guarantee when both live in one record, which is what `Case.to_json` does.
"""

import json
import re

import pytest

from murdoku_lab.core.theme import Theme, canonical_theme
from murdoku_lab.core.render import cell_label
from murdoku_lab.setter.emit import emit, grade, load_key, load_puzzle
from murdoku_lab.setter.pipeline import gate, make_case


@pytest.fixture(scope="module")
def case():
    a = make_case(variant="classic", size=6, band="medium", seed=5, attempts=25)
    assert a.case is not None and gate(a.case, expect_band="medium").ok
    return a.case


@pytest.fixture(scope="module")
def parts(case):
    return emit(case, Theme.load("manor"))


def test_the_puzzle_file_carries_no_atoms_and_no_solution(parts):
    """Structural, not editorial: the fields simply are not there.

    The prose is exempt from the word check, because the statement has to *say* what the goal is —
    "the murderer is the one person who was alone with the victim" is the rules, not a leak. That the
    prose does not give the answer away is the next test's job.
    """
    p = parts.puzzle
    assert set(p) == {
        "schema",
        "id",
        "theme_id",
        "title",
        "cast",
        "victim",
        "statement",
    }
    structural = {k: v for k, v in p.items() if k != "statement"}
    blob = json.dumps(structural).lower()
    for banned in (
        "solution",
        "answer_key",
        "murderer",
        "atom",
        "clue",
        "certificate",
        "band",
    ):
        assert (
            banned not in blob
        ), f"the solver-facing file mentions {banned!r} outside the prose"


@pytest.mark.parametrize("theme_id", ["manor", "canonical"])
def test_the_statement_never_pairs_a_person_with_their_square(theme_id, case):
    """The strong property. The grid and the names both appear — they have to — but no line may put a
    person next to the square they actually occupied, which is what would give the answer away.

    Only the CLUES section is searched. The AREAS list enumerates cell labels ("Area 3: e1 f1 g1 e2
    e3 ..."), and under the canonical theme people are single letters, so "F within 14 characters of
    e3" fires on every board — the `f1` there is a column label, not a person. A leak audit reported
    four such hits and all four were this. Searching the whole statement makes the check useless
    rather than strict.
    """
    from murdoku_lab.core.theme import canonical_theme

    theme = canonical_theme(case) if theme_id == "canonical" else Theme.load(theme_id)
    statement = emit(case, theme).puzzle["statement"]
    clues = statement.split("CLUES", 1)[1] if "CLUES" in statement else statement
    for x, k in case.solution.items():
        cell = cell_label(case, k)
        name = theme.name(x)
        for part in {name, name.split()[0]}:
            if len(part) < 2:
                continue  # a one-letter name cannot be told from a column label
            pat = (
                rf"\b{re.escape(part)}\b\W{{0,12}}\b{re.escape(cell)}\b"
                rf"|\b{re.escape(cell)}\b\W{{0,12}}\b{re.escape(part)}\b"
            )
            assert not re.search(
                pat, clues, re.I
            ), f"a clue pairs {name} with {cell}, which is where they actually stood"


def test_the_statement_carries_no_internal_metadata(case):
    """The content hash, the band and the seed are ours, not the player's. The canonical theme used to
    title every puzzle "Case <content_hash>", which put it straight into the solver-facing prose.
    """
    from murdoku_lab.core.theme import canonical_theme

    for theme in (canonical_theme(case), Theme.load("manor")):
        st = emit(case, theme).puzzle["statement"]
        assert case.content_hash() not in st
        assert str(case.target_band or "\0") not in st.lower()


def test_the_statement_is_self_contained(parts):
    """A solver gets this and nothing else, so it must carry the rules, the map, the cast and the
    clues. Missing any one of them makes the puzzle unanswerable rather than hard."""
    s = parts.puzzle["statement"]
    for section in ("RULES", "GOAL", "PEOPLE", "SCENE", "AREAS", "CLUES"):
        assert section in s, f"the statement has no {section} section"


def test_the_key_records_why_the_puzzle_is_well_posed(parts):
    """A published corpus should carry its own justification rather than asking for trust."""
    w = parts.key["warrant"]
    assert w["guess_free"] is True
    assert w["band"] == parts.key["case"]["target_band"]
    assert w["certificate"]["depth"] > 0
    assert w["explanation_steps"]
    assert all("kind" in step and "text" in step for step in w["explanation_steps"])
    assert "prose_roundtrip" in w


def test_puzzle_and_key_are_tied_by_content_hash(parts):
    """The id is the hash of the DE-THEMED case, so a key cannot be silently paired with the wrong
    puzzle, and two themings of one puzzle share it."""
    assert parts.puzzle["id"] == parts.key["id"]


def test_a_theme_does_not_change_the_id(case):
    a = emit(case, Theme.load("manor"))
    b = emit(case, canonical_theme(case))
    assert a.puzzle["id"] == b.puzzle["id"]
    assert a.puzzle["statement"] != b.puzzle["statement"], "the prose should differ"
    assert a.key["solution"] == b.key["solution"]


def test_loaders_refuse_the_wrong_file(parts, tmp_path):
    p, k = parts.write(tmp_path)
    assert load_puzzle(p)["id"] == parts.puzzle["id"]
    assert load_key(k)["id"] == parts.key["id"]
    with pytest.raises(ValueError, match="not a murdoku puzzle"):
        load_puzzle(k)
    with pytest.raises(ValueError, match="not a murdoku key"):
        load_key(p)


def test_grading_accepts_what_a_player_would_actually_write(parts):
    """Themed names and cell labels, any case, any surrounding whitespace."""
    k = parts.key
    perfect = {n.upper(): f"  {c}  " for n, c in k["solution_named"].items()}
    g = grade(k, perfect, (k["murderer_named"] or "").lower())
    assert g["solved"] and g["verdict_correct"] and g["placement_accuracy"] == 1.0


def test_a_named_murderer_without_the_grid_scores_nothing(parts):
    """With a handful of suspects, naming one is not evidence of having solved anything."""
    k = parts.key
    g = grade(k, {}, k["murderer_named"])
    assert not g["solved"]
    assert g["cells_correct"] == 0
    assert g[
        "verdict_correct"
    ], "the verdict itself was right, and on its own it earns no solve"


def test_a_correct_grid_with_the_wrong_murderer_scores_nothing(parts):
    k = parts.key
    wrong = next(n for n in k["solution_named"] if n != k["murderer_named"])
    g = grade(k, k["solution_named"], wrong)
    assert g["placement_accuracy"] == 1.0
    assert not g["verdict_correct"]
    assert not g["solved"]
