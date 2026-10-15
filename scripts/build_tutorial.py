"""Pick the training case: an easy 6×6 whose first deduction is a single obvious square.

    python scripts/build_tutorial.py

Generates a few easy candidates with the constraint-first farm (player rhythm policy, cozy
scene spec), keeps those whose first person in deduction order has exactly one square allowed
by their own statement, and takes the cheapest certificate. Writes
content/tutorial/tutorial.json (`murdoku_case` + `murdoku_theme`, dressed in the manor), which
play_export ships as the `tutorial` case.
"""

import json
import subprocess
import sys
from pathlib import Path

from murdoku_lab.core.instance import Case
from murdoku_lab.setter import settings
from murdoku_lab.solver.exact import candidate_masks
from murdoku_lab.solver.logic import certify

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "content" / "tutorial" / "tutorial.json"


def open_steps(case, order):
    """Steps of the coached walk where more than one square is still open for the next person
    after their own statements and the rows and columns already taken. The coach shines when
    every step comes down to a single square."""
    scene = case.scene
    allowed = candidate_masks(case)
    taken_rows, taken_cols, wide = set(), set(), 0
    for person in order:
        k = case.solution[person]
        left = [
            m
            for m in allowed[person]
            if scene.row(m) not in taken_rows and scene.col(m) not in taken_cols
        ]
        wide += len(left) > 1
        taken_rows.add(scene.row(k))
        taken_cols.add(scene.col(k))
    return wide


def main():
    work = ROOT / "outputs" / "tutorial"
    work.mkdir(parents=True, exist_ok=True)
    pool = work / "candidates.jsonl"
    if not pool.exists():
        subprocess.run(
            [
                sys.executable,
                "-m",
                "murdoku_lab.setter.farm",
                "--strategy",
                "constraint-first",
                "--variant",
                "classic",
                "--size",
                "6",
                "--bands",
                "easy",
                "--n",
                "40",
                "--shots",
                "6",
                "--workers",
                "6",
                "--seed",
                "4242",
                "--rhythm-policy",
                str(ROOT / "config" / "rhythm" / "player.json"),
                "--scene-spec",
                str(ROOT / "config" / "scene_specs" / "cozy.json"),
                "--out",
                str(pool),
            ],
            check=True,
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
        )
    best = None
    for line in pool.read_text().splitlines():
        if not line.strip():
            continue
        case = Case.from_json(json.loads(line))
        cert = certify(case)
        first = cert.place_order[0]
        if len(candidate_masks(case)[first]) != 1:
            continue
        key = (open_steps(case, cert.place_order), cert.cost, cert.depth)
        if best is None or key < best[0]:
            best = (key, case)
    if best is None:
        raise SystemExit("no candidate starts with a single-square deduction")
    case = best[1]
    theme = settings.dress(case, "manor", salt="tutorial")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "visual_case_id": "tutorial",
                "murdoku_case": case.to_json(),
                "murdoku_theme": theme.to_json(),
            },
            indent=1,
        )
        + "\n"
    )
    print(
        f"wrote {OUT} ({best[0][0]} open step(s), cost {best[0][1]}, {best[0][2]} steps)"
    )


if __name__ == "__main__":
    main()
