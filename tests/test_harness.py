"""The harness must score a perfect solver at 1.0 — otherwise it is measuring itself, not models."""

import pytest

from murdoku_lab.core.theme import Theme
from murdoku_lab.evaluation.agents import ChanceAgent, OracleAgent
from murdoku_lab.evaluation.text_actions import RUNNERS
from murdoku_lab.environment.state import Scratchpad, apply_action
from murdoku_lab.environment.answer_text import absorb_placement
from murdoku_lab.environment.scoring import parse_person
from murdoku_lab.setter.pipeline import make_case


@pytest.fixture(scope="module")
def case():
    a = make_case(
        variant="classic", size=6, band="easy", seed=8000, attempts=30, time_limit_s=5.0
    )
    if not a.ok or a.case is None:
        pytest.skip("no case")
    return a.case


@pytest.mark.parametrize("mode", ["direct", "agentic"])
def test_oracle_scores_perfectly(case, mode):
    th = Theme.load("manor")
    res = RUNNERS[mode](case, OracleAgent(case, th), th)
    assert res.score["answer_correct"], f"oracle failed in {mode} mode: {res.score}"
    assert res.error is None
    if mode == "agentic":
        assert res.score["placement_exact"]
        assert res.score["base_rule_violations"] == 0


def test_actions_are_bookkeeping_not_oracles(case):
    th = Theme.load("manor")
    pad = Scratchpad(case, th)
    x = case.characters[0]
    obs, sub = apply_action(pad, f"place {x} a1")
    assert sub is None and "placed" in obs.lower()
    # `check` must never mention a clue or reveal the solution
    obs, _ = apply_action(pad, "check")
    assert "clue" not in obs.lower()
    for other in case.characters[1:]:
        assert th.name(other).split()[0] not in obs or "holds" in obs.lower()


def test_unknown_action_is_reported_not_crashed(case):
    pad = Scratchpad(case, Theme.load("manor"))
    obs, sub = apply_action(pad, "teleport everyone")
    assert sub is None and obs.startswith("Unknown action")


def test_place_and_unplace_accept_multiword_names(case):
    th = Theme.load("manor")
    pad = Scratchpad(case, th)
    x = case.characters[0]
    name = th.name(x)
    obs, sub = apply_action(pad, f"place {name} a1")
    assert sub is None and x in pad.placed and "placed" in obs.lower()
    obs, sub = apply_action(pad, f"unplace {name}")
    assert sub is None and x not in pad.placed and "no longer" in obs.lower()


def test_solve_ends_the_case_and_answer_is_still_accepted(case):
    """`solve` is the current verb; `answer` stays valid so an agent written against the older
    protocol keeps working. Either way the arrangement is what gets scored."""
    pad = Scratchpad(case, Theme.load("manor"))
    for verb in ("solve", "answer"):
        _, sub = apply_action(pad, f"{verb} Amelia Vance")
        assert sub == "Amelia Vance"


# =============================================================================================
# Answer parsing. These strings are verbatim from a benchmark run in which the previous parser
# scored a CORRECT model as wrong: it scanned the cast in order and took the first name appearing
# anywhere, so any answer that explained itself was attributed to whoever sorted earliest.
# A scoring bug that silently penalises the model is the worst kind, so it gets its own tests.
# =============================================================================================
@pytest.fixture(scope="module")
def fixt():
    a = make_case(variant="classic", size=6, band="medium", seed=5, attempts=25)
    assert a.case is not None
    return a.case, Theme.load("manor")


def test_verdict_wins_over_names_mentioned_later(fixt):
    """The regression. Charlotte is the verdict; Amelia and Dean appear in the explanation."""
    case, theme = fixt
    ans = (
        "Charlotte Reed is the murderer. She was alone with Vaughn in the Study "
        "(Vaughn e2, Charlotte f5; Bruce c3, Enid a4 in Kitchen; Amelia b6 in Library; "
        "Dean d1 in Conservatory)."
    )
    assert parse_person(case, theme, ans) == "C"


def test_murderer_is_x_phrasing(fixt):
    case, theme = fixt
    assert (
        parse_person(
            case, theme, "The murderer is Dean Whitlock — he was alone with Vaughn."
        )
        == "D"
    )
    assert parse_person(case, theme, "Amelia Vance is the murderer.") == "A"
    assert parse_person(case, theme, "murderer: Bruce Ashcombe") == "B"


def test_first_name_and_bare_symbol_resolve(fixt):
    case, theme = fixt
    assert parse_person(case, theme, "Charlotte is the killer") == "C"
    assert parse_person(case, theme, "ANSWER: C") == "C"


def test_the_victim_does_not_win_by_appearing_first(fixt):
    """Explanations open with the victim constantly; that must not become the verdict."""
    case, theme = fixt
    ans = "Vaughn Ashcombe was found in the Study. Charlotte Reed is the one who was alone with him."
    assert parse_person(case, theme, ans) == "C"


def test_naming_the_victim_is_a_wrong_answer_not_a_missing_one(fixt):
    """If the model really does answer the victim, that is wrong — but it must still parse, or the
    episode looks like a formatting failure instead of a reasoning failure."""
    case, theme = fixt
    assert parse_person(case, theme, "Vaughn Ashcombe") == case.victim


def test_no_name_at_all_parses_to_none(fixt):
    case, theme = fixt
    assert parse_person(case, theme, "I could not work it out.") is None


def test_word_boundaries_are_respected(fixt):
    case, theme = fixt
    assert parse_person(case, theme, "Enidine solvent was spilled") is None


def test_direct_mode_placement_block_is_absorbed(fixt):
    """`placed` must mean the same thing in both modes, so one-shot replies get parsed too."""
    case, theme = fixt
    pad = Scratchpad(case, theme)
    lines = "\n".join(
        f"{theme.name(x)} {chr(ord('a') + case.scene.col(k))}{case.scene.row(k) + 1}"
        for x, k in case.solution.items()
    )
    n = absorb_placement(
        pad, "Here is my grid.\nPLACEMENT:\n" + lines + "\nANSWER: someone"
    )
    assert n == len(case.characters)
    assert pad.placed == dict(case.solution)


def test_absorb_ignores_prose_without_erroring(fixt):
    case, theme = fixt
    pad = Scratchpad(case, theme)
    assert (
        absorb_placement(pad, "I think the study matters a lot. ANSWER: Amelia Vance")
        == 0
    )


def test_a_lone_letter_inside_prose_never_wins(fixt):
    """The second regression. A one-character symbol matched the `e` in "the" right next to
    "murderer", stealing the verdict from Dean. Bare symbols now count only as a whole answer.
    """
    case, theme = fixt
    ans = (
        "Dean Whitlock — he stood at e2 in the Kitchen, alone with Vaughn Ashcombe (at f1), "
        "making him the murderer."
    )
    assert parse_person(case, theme, ans) == "D"


def test_a_labelled_bare_symbol_resolves(fixt):
    case, theme = fixt
    assert parse_person(case, theme, "ANSWER: C") == "C"
    assert parse_person(case, theme, "murderer: B") == "B"
    assert parse_person(case, theme, "answer: Charlotte") == "C"


# =============================================================================================
# The Python tool. The solver is handed prose and a grid, never a formulation, so working out that
# this IS a constraint problem and searching it is the thing measured — which needs somewhere to
# run code. What must NOT be reachable is the answer.
# =============================================================================================
from murdoku_lab.evaluation.legacy_python import run_python, screen


def test_computation_works():
    r = run_python(
        "import itertools\nprint(sum(1 for _ in itertools.permutations(range(6))))"
    )
    assert r.ok and r.stdout.strip() == "720"


def test_the_answer_key_is_out_of_reach():
    """`data/cases/*.jsonl` contains solutions and our solver can compute them, so neither the
    filesystem nor the repository may be reachable from model-written code."""
    for hostile in (
        "open('/etc/passwd').read()",
        "import os; print(os.listdir('.'))",
        "import murdoku_lab.core.instance",
        "from murdoku_lab.solver.exact import count_solutions",
        "import pathlib; print(pathlib.Path('.').glob('*'))",
        "__import__('os').system('ls')",
    ):
        r = run_python(hostile)
        assert r.refused, f"not refused: {hostile!r}"
        assert not r.stdout


def test_a_timeout_is_reported_not_hung():
    r = run_python("while True: pass", timeout_s=2)
    assert r.timed_out and "TIMEOUT" in r.observation()


def test_runs_do_not_share_state():
    """Each block stands alone, which the protocol promises the model."""
    run_python("x = 1234")
    r = run_python("print(x)")
    assert not r.ok and "NameError" in r.stderr


def test_screen_allows_ordinary_solver_imports():
    assert screen("import itertools, math\nfrom collections import defaultdict") is None


def test_code_block_extraction():
    from murdoku_lab.environment.answer_text import extract_code

    text = "Let me search.\nACTION: python\n```python\nprint(1+1)\n```\nDone."
    assert extract_code(text).strip() == "print(1+1)"
    assert extract_code("ACTION: python\nno block here") is None


def test_each_python_action_uses_its_own_code_block(fixt):
    from murdoku_lab.environment.answer_text import extract_actions
    from murdoku_lab.evaluation.text_actions import run_agentic

    case, theme = fixt

    class TwoBlocks:
        name = "two-blocks"

        def act(self, prompt, history):
            return (
                "ACTION: python\n```python\nprint('first')\n```\n"
                "ACTION: python\n```python\nprint('second')\n```"
            )

    res = run_agentic(case, TwoBlocks(), theme, max_turns=1)
    assert [a.raw for a in extract_actions(TwoBlocks().act("", []))] == [
        "python",
        "python",
    ]
    assert res.python_calls == 2
    assert [o.strip() for o in res.transcript[0]["observations"]] == ["first", "second"]


def test_action_and_answer_text_inside_code_are_not_submissions(fixt):
    from murdoku_lab.environment.answer_text import (
        absorb_placement,
        extract_verdict,
        extract_actions,
    )

    case, theme = fixt
    text = (
        "ACTION: python\n```python\n"
        "payload = '''\nACTION: solve\nMURDERER: Amelia Vance\n'''\n"
        "print(payload)\n```\nACTION: board"
    )
    assert [a.raw for a in extract_actions(text)] == ["python", "board"]
    assert extract_verdict(text) is None

    pad = Scratchpad(case, theme)
    assert absorb_placement(pad, "```python\nAmelia Vance a1\n```") == 0
    assert not pad.placed


def test_the_verdict_line_is_read_from_the_message(fixt):
    """The protocol asks for `MURDERER: <name>` on its own line, which is where models put it.
    A real qwen3-max episode placed all six people correctly and named the right suspect, and was
    scored as a wrong answer because only `solve`'s arguments were being read."""
    from murdoku_lab.environment.answer_text import extract_verdict

    body = (
        "...all clues satisfied.\n\nACTION: solve\nKeroppi a1\nHello Kitty e2\n"
        "MURDERER: Hello Kitty\n"
    )
    assert extract_verdict(body) == "Hello Kitty"
    assert extract_verdict("ANSWER: Amelia Vance") == "Amelia Vance"
    assert extract_verdict("no verdict here") is None


def test_a_full_correct_submission_scores_on_both_axes(fixt):
    """End-to-end on the scoring path the benchmark reports: grid exact AND verdict right."""
    from murdoku_lab.environment.scoring import score_episode

    case, theme = fixt
    pad = Scratchpad(case, theme)
    pad.placed = dict(case.solution)
    sc = score_episode(case, theme, pad, theme.name(case.murderer))
    assert sc["solved"] and sc["placement_exact"]
    assert sc["answer_correct"] and sc["verdict_matches_own_placement"]
    assert sc["murderer_implied_by_placement"] == case.murderer
    assert sc["clues_all_satisfied"]
    assert sc["clues_satisfied"] == sc["clues_total"] == len(case.clues)


def test_a_correct_grid_with_the_wrong_murderer_is_not_solved(fixt):
    from murdoku_lab.environment.scoring import classify_outcome, score_episode

    case, theme = fixt
    pad = Scratchpad(case, theme)
    pad.placed = dict(case.solution)
    wrong = next(x for x in case.suspects if x != case.murderer)
    sc = score_episode(case, theme, pad, theme.name(wrong))
    assert sc["placement_exact"] and not sc["answer_correct"]
    assert not sc["solved"]
    assert classify_outcome(sc, None) == "correct_grid_wrong_verdict"


def test_a_complete_wrong_grid_has_a_specific_outcome(fixt):
    from murdoku_lab.environment.scoring import classify_outcome, score_episode

    case, theme = fixt
    pad = Scratchpad(case, theme)
    cells = list(case.solution.values())
    pad.placed = dict(zip(case.characters, cells[1:] + cells[:1]))
    sc = score_episode(case, theme, pad, None)
    assert sc["placement_complete"] and not sc["placement_exact"]
    assert classify_outcome(sc, None) in {
        "base_rule_violation",
        "clue_violation",
        "wrong_complete_placement",
    }


def test_episode_deadline_becomes_a_persistable_runtime_outcome(fixt):
    import time
    from murdoku_lab.evaluation.text_actions import run_agentic
    from murdoku_lab.evaluation.run import _run_with_deadline

    case, theme = fixt

    class Slow:
        name = "slow"

        def act(self, prompt, history):
            time.sleep(1)
            return "ACTION: solve"

    result = _run_with_deadline(0.05, run_agentic, case, Slow(), theme, max_turns=1)
    assert result.outcome == "runtime_error"
    assert "hard timeout" in result.error
