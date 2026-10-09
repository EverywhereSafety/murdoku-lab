"""The LLM setter's contract, tested without an API key.

Two things must hold no matter what a model returns:
  * every bundled theme (all LLM-authored bar `manor`) satisfies the invariance property I1;
  * a hostile reply cannot get past `_coerce` + `verify_invariance` into a case.

The network path is exercised by a stub client, so this suite runs offline and in CI.
"""

import json

import pytest

from murdoku_lab.core.theme import Theme, canonical_theme
from murdoku_lab.setter.llm_setter import (
    _coerce,
    _extract_json,
    llm_theme,
    theme_for,
    verify_invariance,
)
from murdoku_lab.setter.llm_client import LLMUnavailable
from murdoku_lab.setter.pipeline import make_case


@pytest.fixture(scope="module")
def case():
    a = make_case(variant="classic", size=6, band="medium", seed=5, attempts=25)
    assert a.case is not None
    return a.case


# ------------------------------------------------------------------- the bundled (LLM) themes
@pytest.mark.parametrize("theme_id", Theme.available())
def test_every_bundled_theme_is_information_free(theme_id, case):
    """I1 per theme. A theme that shifted the hash, the certificate or the band is a theme that
    changed the puzzle — that must be a hard failure, not a rendering quirk.

    A theme written for an ANONYMOUS board names props by board-local id (`p0`, `p1`, ...), which the
    fixture's `classic` board does not have. Skipping is right: the theme is not wrong, it belongs to
    a different board. Themes that name catalogue props are still checked here.
    """
    t = Theme.load(theme_id)
    if set(case.characters) - set(t.names):
        pytest.skip(f"{theme_id} does not cover this cast")
    on_board = {o for o in case.scene.prop_of if o}
    if t.objects and not (set(t.objects) & on_board):
        pytest.skip(
            f"{theme_id} names props of a different board ({sorted(t.objects)[:3]}...)"
        )
    verify_invariance(case, t)


def test_a_theme_for_an_anonymous_board_is_information_free():
    """I1 on the board the theme was actually written for — the check the skip above defers."""
    from murdoku_lab.setter.pipeline import make_case

    a = make_case(variant="anon", size=7, band="medium", seed=5, attempts=25)
    if a.case is None:
        pytest.skip(f"no anon case: {a.reason}")
    for tid in Theme.available():
        t = Theme.load(tid)
        if set(a.case.characters) - set(t.names):
            continue
        if t.objects and set(t.objects) & {o for o in a.case.scene.prop_of if o}:
            verify_invariance(a.case, t)
            return
    pytest.skip("no bundled theme names this board's props")


@pytest.mark.parametrize("theme_id", Theme.available())
def test_bundled_themes_only_rename_real_objects(theme_id):
    """A theme may not introduce a prop the board model has never heard of."""
    Theme.load(theme_id).validate(None)


# ---------------------------------------------------------------------------- reply handling
def test_json_is_extracted_from_prose():
    """Wrapping JSON in chat is the commonest format slip; a retry for it would be waste."""
    d = _extract_json(
        'Sure! Here you go:\n```json\n{"a": {"b": "}"}, "c": 1}\n```\nHope that helps'
    )
    assert d == {"a": {"b": "}"}, "c": 1}


def test_unparseable_reply_is_rejected():
    with pytest.raises(ValueError):
        _extract_json("I would rather not.")


def test_a_theme_missing_a_character_is_refused(case):
    """We repair formatting, never content: an absent name goes back to the model."""
    bad = {
        "theme_id": "x",
        "title": "X",
        "names": {"A": "Ann"},
        "areas": [f"R{i}" for i in range(case.scene.n_areas)],
    }
    with pytest.raises(ValueError, match="no name for"):
        _coerce(bad, case)


def test_duplicate_names_are_refused(case):
    same = {x: "Same Person" for x in case.characters}
    bad = {
        "theme_id": "x",
        "title": "X",
        "names": same,
        "areas": [f"R{i}" for i in range(case.scene.n_areas)],
    }
    with pytest.raises(ValueError, match="distinct"):
        _coerce(bad, case)


def test_too_few_areas_is_refused(case):
    bad = {
        "theme_id": "x",
        "title": "X",
        "names": {x: f"N{x}" for x in case.characters},
        "areas": ["Only One"],
    }
    with pytest.raises(ValueError, match="names 1 areas"):
        _coerce(bad, case)


def test_renaming_an_object_not_on_the_board_is_dropped_not_fatal(case):
    """Harmless overreach: the model dressed a prop this scene does not contain."""
    ok = {
        "theme_id": "x",
        "title": "X",
        "names": {x: f"N{x}" for x in case.characters},
        "areas": [f"R{i}" for i in range(case.scene.n_areas)],
        "objects": {"piano": "harpsichord", "not_a_real_object": "nonsense"},
    }
    t = _coerce(ok, case)
    assert "not_a_real_object" not in t.objects


# ------------------------------------------------------------------------------ the LLM path
class _Stub:
    """Stands in for LLMClient. `replies` are served in order."""

    def __init__(self, replies):
        self.replies, self.calls = list(replies), 0
        self.usage = type("U", (), {"to_json": staticmethod(lambda: {"calls": 0})})()

    def available(self):
        return True

    def chat(self, messages, **kw):
        self.calls += 1
        return self.replies.pop(0)


def _good_reply(case) -> str:
    return json.dumps(
        {
            "theme_id": "stub",
            "title": "A Stub Case",
            "blurb": "b",
            "names": {x: f"Person {x}" for x in case.characters},
            "pronouns": {x: "they" for x in case.characters},
            "areas": [f"Room {i}" for i in range(case.scene.n_areas)],
            "objects": {},
            "victim_note": "was found dead",
        }
    )


def test_llm_path_accepts_a_valid_reply(case):
    r = llm_theme(case, style="stub", client=_Stub([_good_reply(case)]))
    assert r.from_llm and r.attempts == 1
    assert r.theme.names[case.victim] == f"Person {case.victim}"


def test_a_rejected_reply_is_retried_with_the_error(case):
    """The repair loop must actually re-ask, and must succeed when the model fixes itself."""
    stub = _Stub(["not json at all", _good_reply(case)])
    r = llm_theme(case, style="stub", client=stub)
    assert stub.calls == 2 and r.attempts == 2 and r.errors


def test_persistent_failure_raises_rather_than_shipping_a_bad_theme(case):
    with pytest.raises(LLMUnavailable):
        llm_theme(case, style="stub", client=_Stub(["nope"] * 3))


# ------------------------------------------------------------------------------- degradation
def test_theme_for_never_raises_without_a_key(case):
    """A missing key must not be able to stop a verified case from being emitted."""
    r = theme_for(case, seed=3, allow_llm=False)
    assert r.source in {"bundled", "canonical"}
    verify_invariance(case, r.theme)


def test_theme_for_falls_back_when_the_llm_fails(case):
    class Dead(_Stub):
        def chat(self, messages, **kw):
            raise RuntimeError("endpoint down")

    r = theme_for(case, seed=3, client=Dead([]), allow_llm=True)
    assert not r.from_llm and r.errors
    verify_invariance(case, r.theme)


def test_canonical_theme_is_the_identity(case):
    t = canonical_theme(case)
    assert all(t.name(x) == x for x in case.characters)
    verify_invariance(case, t)


import pytest
from murdoku_lab.core.theme import canonical_theme
from murdoku_lab.setter.llm_setter import _coerce


def test_llm_theme_rejects_added_spatial_fact(base_case):
    case = base_case
    data = canonical_theme(case).to_json()
    data["victim_note"] = "was found alone"
    with pytest.raises(ValueError, match="neutral"):
        _coerce(data, case)
    data["victim_note"] = "was found dead"
    assert _coerce(data, case).victim_note == "was found dead"
