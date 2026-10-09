"""Summarise one or more benchmark JSONL files without re-running model calls."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def load(paths: list[Path]) -> list[dict]:
    rows = []
    for path in paths:
        rows.extend(
            json.loads(line) for line in path.read_text().splitlines() if line.strip()
        )
    return rows


def summary(rows: list[dict]) -> str:
    groups = defaultdict(list)
    for row in rows:
        source = row.get("source", "unknown")
        size = row.get("size", "unknown")
        groups[(source, size, row.get("band"))].append(row)
    head = (
        f"{'source':<18} {'size':<7} {'band':<9} {'n':>3} {'success':>7} "
        f"{'exact':>7} {'murder':>7} {'partial':>7} {'turns':>6} {'python':>6} "
        f"{'wall_s':>8}"
    )
    out = [head]
    for (source, size, band), rs in sorted(
        groups.items(), key=lambda x: tuple(str(v) for v in x[0])
    ):
        n = len(rs)
        mean = lambda key: sum(float(r["score"].get(key, 0) or 0) for r in rs) / n
        out.append(
            f"{source:<18} {size:<7} {str(band):<9} {n:>3} "
            f"{mean('solved'):>7.2f} {mean('placement_exact'):>7.2f} "
            f"{mean('answer_correct'):>7.2f} "
            f"{mean('placement_accuracy'):>7.2f} "
            f"{sum(r.get('turns', 0) for r in rs) / n:>6.1f} "
            f"{sum(r.get('python_calls', 0) for r in rs) / n:>6.1f} "
            f"{sum(r.get('wall_s', 0) for r in rs) / n:>8.1f}"
        )
    out.append("\noutcomes")
    counts = Counter(row.get("outcome", "unknown") for row in rows)
    out.extend(f"  {name:<28} {n}" for name, n in sorted(counts.items()))
    out.append("\n" + failure_diagnostics(rows))
    return "\n".join(out)


def failure_diagnostics(rows: list[dict]) -> str:
    """Compact protocol/tool-use diagnostics derived only from persisted episode fields."""
    turns = [turn for row in rows for turn in row.get("transcript", [])]
    observations = [str(obs) for turn in turns for obs in turn.get("observations", [])]
    completion_tokens = sum(
        int((row.get("usage") or {}).get("completion_tokens", 0) or 0) for row in rows
    )
    n = len(rows)
    values = {
        "episodes_with_no_action_turn": sum(
            any(not turn.get("actions") for turn in row.get("transcript", []))
            for row in rows
        ),
        "no_action_turns": sum(not turn.get("actions") for turn in turns),
        "invalid_actions": sum(int(row.get("invalid_actions", 0) or 0) for row in rows),
        "python_calls": sum(int(row.get("python_calls", 0) or 0) for row in rows),
        "python_refusals": sum(int(row.get("python_refusals", 0) or 0) for row in rows),
        "python_error_observations": sum(
            any(marker in obs for marker in ("STDERR:", "REFUSED:", "TIMEOUT"))
            for obs in observations
        ),
        "python_no_output_observations": sum(
            "(no output" in obs for obs in observations
        ),
        "correct_verdict_without_exact_grid": sum(
            bool(row.get("score", {}).get("answer_correct"))
            and not bool(row.get("score", {}).get("placement_exact"))
            for row in rows
        ),
        "completion_token_budget_exhausted": sum(
            "completion-token budget exhausted" in str(row.get("error") or "")
            for row in rows
        ),
    }
    out = ["failure diagnostics"]
    out.extend(f"  {name:<36} {value}" for name, value in values.items())
    mean_tokens = f"{completion_tokens / n:.1f}" if n else "n/a"
    out.append(f"  {'mean_completion_tokens':<36} {mean_tokens}")
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("paths", nargs="+", type=Path)
    a = ap.parse_args(argv)
    print(summary(load(a.paths)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
