"""Invariant I1: the LLM's theme layer cannot touch the math.

De-theming a case — replacing every name with its canonical symbol — must leave the content hash,
the solution set, the deduction certificate and the difficulty band bit-identical.
"""

import random

import pytest

from murdoku_lab.core.theme import Theme, canonical_theme
from murdoku_lab.core.render import render_case
from murdoku_lab.setter.pipeline import make_case
from murdoku_lab.solver.difficulty import classify
from murdoku_lab.solver.exact import enumerate_cp
from murdoku_lab.solver.logic import certify


@pytest.fixture(scope="module")
def cases():
    out = []
    for i, band in enumerate(("easy", "medium")):
        a = make_case(
            variant="classic",
            size=6,
            band=band,
            seed=4000 + i * 31,
            attempts=25,
            time_limit_s=5.0,
        )
        if a.ok and a.case is not None:
            out.append(a.case)
    if not out:
        pytest.skip("setter produced no case in budget")
    return out


def test_theme_does_not_change_the_math(cases):
    for case in cases:
        themed = case.__class__(**{**case.__dict__, "theme_id": "manor"})
        assert themed.content_hash() == case.content_hash()
        c1, c2 = certify(case), certify(themed)
        assert c1.to_json() == c2.to_json()
        assert classify(c1) == classify(c2)
        assert enumerate_cp(case, cap=3).count == enumerate_cp(themed, cap=3).count


def test_both_renderings_are_produced_and_differ_only_in_words(cases):
    for case in cases:
        th = Theme.load("manor")
        th.validate(case)
        themed = render_case(case, th)
        plain = render_case(case, canonical_theme(case))
        assert themed != plain  # the words changed
        assert themed.count("CLUES") == plain.count("CLUES") == 1
        # same number of clue lines: the logical content is identical
        n1 = len(
            [l for l in themed.splitlines() if l.strip()[:2].rstrip(".").isdigit()]
        )
        n2 = len([l for l in plain.splitlines() if l.strip()[:2].rstrip(".").isdigit()])
        assert n1 == n2


def test_theme_validation_rejects_a_short_cast(cases):
    bad = Theme(theme_id="bad", title="Bad", names={"A": "Only One"}, areas=("X",))
    with pytest.raises(ValueError):
        bad.validate(cases[0])
