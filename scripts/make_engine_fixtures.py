"""Record the Python session's behaviour for the player's JavaScript engine to replay.

    python scripts/make_engine_fixtures.py

For each classic demo case, random action sequences — valid ones, malformed ones, and moves
the session accepts but flags later, such as two people on one square — run through
VisualSession.act. After every action the fixture stores whether it was accepted and the
resulting placements, marks, exclusions, reviewed clues and undo/redo availability.
tests/engine/engine.test.mjs replays them against web/src/play/engine.

Also writes tests/fixtures/seal_vectors.json, which pins murdoku.seal/1 for both languages.
"""

import json
import random
from pathlib import Path

from murdoku_lab.core.render import cell_label, parse_cell
from murdoku_lab.environment.scoring import classify_outcome, score_episode
from murdoku_lab.environment.state import Scratchpad
from murdoku_lab.environment.validation import SessionError
from murdoku_lab.visual.demos import glasshouse, lily_pond
from murdoku_lab.visual.seal import seal
from murdoku_lab.visual.session import VisualSession

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tests" / "fixtures" / "engine"
STEPS = 260


def _state(observation):
    return {
        "placements": observation["placements"],
        "marks": observation["marks"],
        "exclusions": observation["exclusions"],
        "reviewed": sorted(c["id"] for c in observation["clues"] if c["reviewed"]),
        "can_undo": observation["can_undo"],
        "can_redo": observation["can_redo"],
    }


def _random_action(rng, people, cells, clues):
    person = rng.choice(people + ["Z"]) if rng.random() < 0.95 else "nobody"
    cell = (
        rng.choice(cells)
        if rng.random() < 0.93
        else rng.choice(["z9", "a0", "a99", "", "?"])
    )
    kind = rng.choices(
        [
            "place",
            "unplace",
            "mark",
            "unmark",
            "exclude",
            "unexclude",
            "review_clue",
            "undo",
            "redo",
        ],
        weights=[30, 8, 14, 8, 8, 5, 6, 11, 6],
    )[0]
    if kind in ("place", "exclude", "unexclude"):
        return {"action": kind, "person": person, "cell": cell}
    if kind == "unplace":
        return {"action": kind, "person": person}
    if kind in ("mark", "unmark"):
        many = " ".join(rng.sample(cells, k=rng.choice((1, 1, 2, 3))))
        return {
            "action": kind,
            "person": person,
            "cell": many if rng.random() < 0.9 else cell,
        }
    if kind == "review_clue":
        clue = rng.choice(clues + ["clue-99"])
        return {"action": kind, "clue_id": clue, "reviewed": rng.random() < 0.7}
    return {"action": kind}


def record(entry, seed):
    rng = random.Random(seed)
    session = VisualSession(entry)
    first = session.observe()
    people = [p["id"] for p in first["people"]]
    cells = [c["cell"] for c in first["scene"]["cells"]]
    clues = [c["id"] for c in first["clues"]]
    steps = []
    for _ in range(STEPS):
        action = _random_action(rng, people, cells, clues)
        try:
            state = _state(session.act(action, source="human")["observation"])
            steps.append({"action": action, "ok": True, "state": state})
        except SessionError:
            steps.append({"action": action, "ok": False})
    return {
        "case": entry.slug,
        "width": first["scene"]["width"],
        "height": first["scene"]["height"],
        "people": [
            {"id": p["id"], "name": p["name"], "victim": p["victim"]}
            for p in first["people"]
        ],
        "cells": [
            {k: c[k] for k in ("cell", "row", "col", "area", "standable")}
            for c in first["scene"]["cells"]
        ],
        "clues": clues,
        "goal_type": first["goal_type"],
        "initial": _state(first),
        "steps": steps,
        "verdicts": verdicts(entry, rng),
    }


# The player merges the two clue-level failures: it cannot evaluate clues in the browser.
OUTCOMES = {
    "clue_violation": "wrong_arrangement",
    "wrong_complete_placement": "wrong_arrangement",
}


def verdicts(entry, rng):
    case, theme = entry.case, entry.theme
    solution = {p: cell_label(case, k) for p, k in case.solution.items()}
    goal = case.vdef.answer
    right = case.murderer if goal == "murderer" else solution[case.victim]
    people = list(case.characters)
    scenarios = [(dict(solution), right)]
    wrong = next(p for p in people if p not in (right, case.victim))
    scenarios.append((dict(solution), wrong if goal == "murderer" else "a1"))
    partial = dict(solution)
    partial.pop(people[0])
    scenarios.append((partial, right))
    for _ in range(6):
        shuffled = dict(solution)
        a, b = rng.sample(people, 2)
        shuffled[a], shuffled[b] = shuffled[b], shuffled[a]
        if rng.random() < 0.4:
            shuffled[a] = solution[people[-1]]
        scenarios.append((shuffled, right if rng.random() < 0.5 else wrong))
    out = []
    for placed, answer in scenarios:
        pad = Scratchpad(case, theme)
        pad.placed = {p: parse_cell(case, c) for p, c in placed.items()}
        score = score_episode(case, theme, pad, answer)
        outcome = classify_outcome(score, None)
        out.append(
            {
                "placed": placed,
                "answer": answer,
                "solved": score["solved"],
                "outcome": OUTCOMES.get(outcome, outcome),
                "cells_correct": score["placement_cells_correct"],
                "implied": score["murderer_implied_by_placement"],
            }
        )
    return {"solution": solution, "right": right, "scenarios": out}


def seal_vectors():
    values = [
        ("glasshouse", "", {"murderer": "A", "solution": {"A": "b1", "V": "c3"}}),
        (
            "n-142-ab12cd",
            "2026-10-15",
            {"epilogue": "Café au lait — “quoted”", "hints": [1, 2]},
        ),
        ("liner-7x7", "", {"empty": {}, "list": [], "flag": True, "none": None}),
    ]
    return [
        {
            "id": case_id,
            "salt": salt,
            "value": value,
            "sealed": seal(value, case_id, salt),
        }
        for case_id, salt, value in values
    ]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for seed, entry in enumerate(
        (glasshouse(), lily_pond(), glasshouse(open_case=True))
    ):
        (OUT / f"{entry.slug}.json").write_text(
            json.dumps(record(entry, 1000 + seed)) + "\n"
        )
    (ROOT / "tests" / "fixtures" / "seal_vectors.json").write_text(
        json.dumps(seal_vectors(), ensure_ascii=False, indent=1) + "\n"
    )
    print(f"wrote engine fixtures to {OUT}")


if __name__ == "__main__":
    main()
