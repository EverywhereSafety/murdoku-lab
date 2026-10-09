"""Placement and verdict scoring shared by player and model environments."""

from __future__ import annotations

import re
from murdoku_lab.core.instance import Case
from murdoku_lab.core.theme import Theme
from murdoku_lab.environment.state import Scratchpad
from murdoku_lab.core.render import cell_label, parse_cell

_VERDICT = r"(?:murderer|killer|culprit|guilty(?:\s+one)?)"


def parse_person(case: Case, theme: Theme, answer: str) -> str | None:
    """Resolve a verdict by symbol, full name, explicit verdict phrase or first mention.

    Whole-name matches take priority. Prose uses word boundaries and prefers
    explicit verdict phrases, then the earliest non-victim name.
    """
    low = answer.strip().lower()
    # A bare symbol is only recognised as the WHOLE answer, so a leading label has to come off
    # first or "ANSWER: C" resolves to nothing. The runners usually strip this, but not always.
    bare = re.sub(
        r"^(?:the\s+)?(?:answer|verdict|murderer|killer|culprit)\s*[:\-—]\s*",
        "",
        low.rstrip(".,!?;:").strip(),
    ).strip()

    forms: list[tuple[str, str]] = []  # (needle, symbol)
    for x in case.characters:
        full = theme.name(x).lower()
        forms.append((full, x))
        first = full.split()[0]
        if first != full:
            forms.append((first, x))
        if x.lower() != full:
            forms.append((x.lower(), x))
    forms.sort(key=lambda t: -len(t[0]))
    prose = [(n, x) for n, x in forms if len(n) >= 2]

    # 1. the entire answer is a name or a bare symbol
    for needle, x in forms:
        if bare == needle:
            return x

    # 2. explicit verdict, boundary-matched
    for needle, x in prose:
        if x == case.victim:
            continue
        nb = _bounded(needle)
        pat = (
            rf"{nb}\W{{0,4}}(?:is|was|,|-|—|:)?\W{{0,6}}(?:the\s+)?{_VERDICT}"
            rf"|{_VERDICT}\W{{0,6}}(?:is|was)?\W{{0,6}}(?:[:\-—]\s*)?{nb}"
        )
        if re.search(pat, low):
            return x

    # 3./4. earliest mention, non-victim first
    for skip_victim in (True, False):
        hits = []
        for needle, x in prose:
            if skip_victim and x == case.victim:
                continue
            i = _word_find(low, needle)
            if i >= 0:
                hits.append((i, -len(needle), x))
        if hits:
            return sorted(hits)[0][2]
    return None


def _bounded(needle: str) -> str:
    """`needle` as a regex that will not match inside a longer word."""
    return rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])"


def _word_find(hay: str, needle: str) -> int:
    """Index of `needle` in `hay` on word boundaries, or -1. Boundaries matter: without them
    "Enid" matches inside "Enidine" and a first name matches inside an unrelated word.
    """
    m = re.search(_bounded(needle), hay)
    return m.start() if m else -1


def score_episode(
    case: Case, theme: Theme, pad: Scratchpad, answer: str | None
) -> dict:
    key = case.vdef.answer
    correct = False
    parsed: str | None = None

    if answer:
        if key == "murderer":
            parsed = got = parse_person(case, theme, answer)
            correct = got is not None and got == case.murderer
        elif key == "victim_cell":
            k = parse_cell(case, answer.split()[-1]) if answer.split() else None
            parsed = None if k is None else cell_label(case, k)
            correct = k is not None and k == case.solution[case.victim]

    sol = dict(case.solution)
    n = len(case.characters)
    cells_right = sum(1 for x, k in pad.placed.items() if sol.get(x) == k)
    complete = len(pad.placed) == n
    exact = complete and cells_right == n
    clues_satisfied = None
    if complete:
        clues_satisfied = sum(
            1 for clue in case.clues if clue.holds(case.scene, pad.placed, case.tags)
        )

    # The murderer implied by the arrangement the model actually submitted. This separates "worked
    # out the grid but misapplied the alone-with rule" from "never found the grid" — two very
    # different failures that a single identity score cannot tell apart.
    implied = murderer_rule(case, pad.placed) if complete else None

    task_solved = bool(exact and correct)
    return {
        # --- primary: the whole arrangement
        # A task is solved only when BOTH the full placement and requested verdict are correct.
        "solved": task_solved,
        "placement_exact": bool(exact),
        "placement_complete": bool(complete),
        "placement_cells_correct": cells_right,
        "placement_cells_claimed": len(pad.placed),
        "placement_accuracy": round(cells_right / n, 4),
        "clues_satisfied": clues_satisfied,
        "clues_total": len(case.clues),
        "clues_all_satisfied": bool(complete and clues_satisfied == len(case.clues)),
        # --- secondary: the named verdict, which is 1-of-few and guessable on its own
        "answer_raw": answer,
        "answer_parsed": parsed,
        "answer_correct": bool(correct),
        "murderer_implied_by_placement": implied,
        "verdict_matches_own_placement": bool(
            implied is not None and parsed == implied
        ),
        "base_rule_violations": len(pad.violations()),
    }


def classify_outcome(score: dict, error: str | None) -> str:
    """Return one mutually exclusive label for fast failure accounting."""
    if error:
        return "runtime_error"
    if score["solved"]:
        return "solved"
    if score["placement_exact"]:
        return "correct_grid_wrong_verdict"
    if not score["placement_complete"]:
        return "incomplete_placement"
    if score["base_rule_violations"]:
        return "base_rule_violation"
    if not score["clues_all_satisfied"]:
        return "clue_violation"
    if score["answer_correct"]:
        return "correct_verdict_wrong_grid"
    return "wrong_complete_placement"


def murderer_rule(case: Case, placement: dict) -> str | None:
    """Apply the case's own answer rule to a *claimed* placement. Uses the variant's rule so this
    stays correct for variants where the answer is not a suspect at all."""
    from murdoku_lab.core.instance import MURDERER_RULES

    try:
        return MURDERER_RULES[case.vdef.murderer_rule](
            case.scene, placement, case.victim
        )
    except Exception:  # noqa: BLE001
        return None
