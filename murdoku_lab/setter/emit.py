"""Emit a puzzle as two files: what the solver sees, and what grades it.

The architecture this enforces:

    the mathematics is the WARRANT       — uniqueness, guess-freedom, difficulty, the answer key
    the natural language is the ARTEFACT — the only thing a solver is given
    the key is the GRADER               — kept apart, so it cannot leak by accident

`Case.to_json` puts statement, atoms and solution in one record, which is right for our own
regression corpus and wrong for anything handed to a solver: the answer sits in the same file. Convention
("just don't read the solution field") is not a guarantee. Splitting the files is.

    <id>.puzzle.json   {id, statement, cast, goal}          <- pure prose, no atoms, no solution
    <id>.key.json      {id, solution, answer, atoms, certificate, band, warrant}

`load_puzzle` returns only the prose; there is no code path from a puzzle file to its key. The two are
tied together by `id`, which is the content hash of the DE-THEMED case, so a key cannot be silently
paired with the wrong puzzle.

The warrant records *why* the puzzle is well-posed — solution count, guess-freedom, the certificate,
and whether the prose was round-trip verified — so a published corpus carries its own justification
rather than asking you to trust the generator.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from murdoku_lab.core.instance import Case
from murdoku_lab.core.theme import Theme, canonical_theme
from murdoku_lab.core.render import render_case
from murdoku_lab.solver.difficulty import classify
from murdoku_lab.solver.logic import certify


@dataclass
class Emitted:
    puzzle: dict  # what a solver may see
    key: dict  # what grades it
    warrant: dict = field(default_factory=dict)

    def write(
        self, directory: str | Path, stem: str | None = None
    ) -> tuple[Path, Path]:
        d = Path(directory)
        d.mkdir(parents=True, exist_ok=True)
        stem = stem or self.puzzle["id"]
        p = d / f"{stem}.puzzle.json"
        k = d / f"{stem}.key.json"
        p.write_text(json.dumps(self.puzzle, ensure_ascii=False, indent=1) + "\n")
        k.write_text(json.dumps(self.key, ensure_ascii=False, indent=1) + "\n")
        return p, k


def emit(
    case: Case, theme: Theme | None = None, *, roundtrip: dict | None = None
) -> Emitted:
    """Split a verified case into a solver-facing puzzle and a separate key.

    `roundtrip` is the result of `murdoku_lab.evaluation.roundtrip.check_case` if it was run — recorded in the warrant so
    a reader can tell whether the prose was *proved* to state the same puzzle or merely rendered.
    """
    theme = theme or canonical_theme(case)
    theme.validate(case)
    cert = certify(case)
    statement = render_case(case, theme)

    puzzle = {
        "schema": "murdoku.puzzle/1",
        "id": case.content_hash(),
        "theme_id": theme.theme_id,
        "title": theme.title,
        "cast": [theme.name(x) for x in case.characters],
        "victim": theme.name(case.victim),
        # The whole puzzle, as prose and an ASCII map. Nothing else is needed to solve it, and
        # nothing here names a placement.
        "statement": statement,
    }
    key = {
        "schema": "murdoku.key/1",
        "id": case.content_hash(),
        "answer": case.vdef.answer,
        "answer_key": case.answer_key,
        # Both spellings: symbols for our own tooling, themed names for grading a prose answer.
        "solution": {x: int(k) for x, k in sorted(case.solution.items())},
        "solution_named": {
            theme.name(x): _cell(case, k) for x, k in sorted(case.solution.items())
        },
        "murderer": case.murderer,
        "murderer_named": theme.name(case.murderer) if case.murderer else None,
        "case": case.to_json(),  # the full mathematical record, for reproduction
    }
    warrant = {
        "band": classify(cert),
        "target_band": case.target_band,
        "guess_free": cert.solved,
        "certificate": {
            k: cert.to_json()[k]
            for k in ("depth", "advanced", "tier_max", "max_width", "cost")
        },
        "explanation_steps": [s.to_json() for s in cert.steps],
        "n_clues": len(case.clues),
        "n_atoms": len(case.atoms),
        "prose_roundtrip": roundtrip or {"checked": False},
    }
    key["warrant"] = warrant
    return Emitted(puzzle=puzzle, key=key, warrant=warrant)


def _cell(case: Case, k: int) -> str:
    from murdoku_lab.core.render import cell_label

    return cell_label(case, k)


def load_puzzle(path: str | Path) -> dict:
    """Read a solver-facing puzzle. There is deliberately no path from here to its key."""
    d = json.loads(Path(path).read_text())
    if d.get("schema") != "murdoku.puzzle/1":
        raise ValueError(f"not a murdoku puzzle file: {d.get('schema')!r}")
    return d


def load_key(path: str | Path) -> dict:
    d = json.loads(Path(path).read_text())
    if d.get("schema") != "murdoku.key/1":
        raise ValueError(f"not a murdoku key file: {d.get('schema')!r}")
    return d


def grade(key: dict, placement: dict[str, str], verdict: str | None = None) -> dict:
    """Grade a solver's answer against a key, taking themed names and cell labels as a player writes
    them. The placement is the deliverable; the named verdict is secondary and guessable on its own.
    """
    want = {k.lower(): v.lower() for k, v in key["solution_named"].items()}
    got = {
        str(k).strip().lower(): str(v).strip().lower()
        for k, v in (placement or {}).items()
    }
    right = sum(1 for k, v in want.items() if got.get(k) == v)
    complete = set(got) >= set(want)
    exact = complete and right == len(want)
    m = key.get("murderer_named")
    verdict_correct = bool(verdict and m and verdict.strip().lower() == m.lower())
    return {
        "solved": bool(exact and verdict_correct),
        "cells_correct": right,
        "cells_total": len(want),
        "placement_accuracy": round(right / max(1, len(want)), 4),
        "placement_complete": bool(complete),
        "verdict_correct": verdict_correct,
    }
