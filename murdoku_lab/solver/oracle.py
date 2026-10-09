"""One deterministic, auditable front door for solver ground truth.

The exact answer, the human deduction certificate, and the optimal-path analysis answer different
questions.  Keeping them in one result makes their evidence and limitations explicit without
pretending that a CP-SAT solution is a human explanation or that a bounded A* result is globally
optimal over every conceivable deduction.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from murdoku_lab.core.instance import Case
from .exact import enumerate_cp, enumerate_dfs
from .logic import Certificate, certify
from .optimal import OptimalResult, optimal_chain


@dataclass
class OracleResult:
    status: str  # unique | multiple | unsat | timeout | disagreement
    solution: dict[str, int] | None
    cp_count: int
    cp_timed_out: bool
    dfs_count: int | None
    engines_agree: bool | None
    human: Certificate | None
    optimal: OptimalResult | None

    @property
    def unique(self) -> bool:
        return self.status == "unique"

    def to_json(self) -> dict:
        return {
            "status": self.status,
            "unique": self.unique,
            "solution": self.solution,
            "exact": {
                "cp_count_capped_at": self.cp_count,
                "cp_timed_out": self.cp_timed_out,
                "dfs_count_capped_at": self.dfs_count,
                "engines_agree": self.engines_agree,
                "deterministic_settings": {"num_workers": 1, "random_seed": 0},
            },
            "human": self.human.to_json() if self.human else None,
            "optimal": self.optimal.to_json() if self.optimal else None,
        }


def solve(
    case: Case,
    *,
    cross_check: bool | None = None,
    include_optimal: bool = False,
    time_limit_s: float = 20.0,
    max_optimal_nodes: int = 20000,
) -> OracleResult:
    """Solve and classify a case without trusting its recorded solution.

    `cross_check=None` enables the independent DFS on boards up to 9 characters, where it is a
    practical per-case guard. Larger cases rely on CP-SAT plus the corpus-level encoder-agreement
    tests; callers may explicitly request DFS when they are willing to pay for it.
    """
    cp = enumerate_cp(case, cap=2, time_limit_s=time_limit_s)
    if cp.timed_out:
        return OracleResult("timeout", None, cp.count, True, None, None, None, None)

    use_dfs = len(case.characters) <= 9 if cross_check is None else cross_check
    dfs = enumerate_dfs(case, cap=2) if use_dfs else None
    agree = None
    if dfs is not None:
        # At cap=2 the two engines need only agree on the classification. Their first two solutions
        # need not be the same two when a puzzle has many solutions; for a unique case the placement
        # itself must match exactly.
        agree = dfs.count == cp.count and (
            cp.count >= 2
            or {tuple(sorted(x.items())) for x in dfs.solutions}
            == {tuple(sorted(x.items())) for x in cp.solutions}
        )
    if agree is False:
        return OracleResult(
            "disagreement", None, cp.count, False, dfs.count, False, None, None
        )
    if cp.count == 0:
        return OracleResult(
            "unsat", None, 0, False, dfs.count if dfs else None, agree, None, None
        )
    if cp.count > 1:
        return OracleResult(
            "multiple",
            None,
            cp.count,
            False,
            dfs.count if dfs else None,
            agree,
            None,
            None,
        )

    solution = dict(sorted(cp.solutions[0].items()))
    human = certify(case)
    optimal = (
        optimal_chain(case, max_nodes=max_optimal_nodes) if include_optimal else None
    )
    return OracleResult(
        "unique", solution, 1, False, dfs.count if dfs else None, agree, human, optimal
    )


def _load_case(path: Path, index: int) -> Case:
    text = path.read_text()
    try:
        value = json.loads(text)
        rows = value if isinstance(value, list) else [value]
    except json.JSONDecodeError:
        rows = [json.loads(line) for line in text.splitlines() if line.strip()]
    if not (0 <= index < len(rows)):
        raise SystemExit(f"--case-index {index} outside 0..{len(rows) - 1}")
    return Case.from_json(rows[index])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("case_file", type=Path)
    ap.add_argument("--case-index", type=int, default=0)
    ap.add_argument("--cross-check", choices=("auto", "yes", "no"), default="auto")
    ap.add_argument("--optimal", action="store_true")
    ap.add_argument("--time-limit", type=float, default=20.0)
    ap.add_argument("--max-optimal-nodes", type=int, default=20000)
    a = ap.parse_args(argv)
    cross = {"auto": None, "yes": True, "no": False}[a.cross_check]
    result = solve(
        _load_case(a.case_file, a.case_index),
        cross_check=cross,
        include_optimal=a.optimal,
        time_limit_s=a.time_limit,
        max_optimal_nodes=a.max_optimal_nodes,
    )
    print(json.dumps(result.to_json(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.unique else 1


if __name__ == "__main__":
    raise SystemExit(main())
