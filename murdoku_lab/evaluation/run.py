"""CLI: generate (or load) a case set, run agents over it, write per-episode JSONL + a summary.

python -m murdoku_lab.evaluation.run --agents oracle,chance --bands easy,medium,hard --per-band 3
python -m murdoku_lab.evaluation.run --agents llm --model claude-opus-4-8 --modes direct,agentic
"""

from __future__ import annotations

import argparse
import json
import signal
import sys
from collections import defaultdict
from pathlib import Path

from murdoku_lab.core.instance import Case
from murdoku_lab.core.theme import Theme, canonical_theme
from murdoku_lab.evaluation.agents import build_agent
from murdoku_lab.evaluation.text_actions import RUNNERS
from murdoku_lab.setter.pipeline import SetterStats, gate, make_case

from murdoku_lab.paths import PROJECT_ROOT

ROOT = PROJECT_ROOT


class EpisodeDeadline(RuntimeError):
    pass


def _run_with_deadline(seconds: float, fn, *args, **kwargs):
    """Interrupt a blocking provider call so the harness can persist a failure row."""
    if seconds <= 0 or not hasattr(signal, "SIGALRM"):
        return fn(*args, **kwargs)
    previous = signal.getsignal(signal.SIGALRM)

    def expired(_signum, _frame):
        raise EpisodeDeadline(f"episode exceeded {seconds:g}s hard timeout")

    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        return fn(*args, **kwargs)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def _theme(case: Case, name: str) -> Theme:
    if name == "canonical":
        return canonical_theme(case)
    if name == "official":
        labels = case.meta.get("official_area_labels") or {}
        return Theme(
            theme_id="official",
            title=case.meta.get("official_title") or "Murdoku",
            names={x: x for x in case.characters},
            areas=tuple(
                labels.get(str(i), labels.get(i, f"Area {i + 1}"))
                for i in range(case.scene.n_areas)
            ),
        )
    return Theme.load(name)


def build_set(bands, per_band, variant, size, seed0, verify) -> tuple[list[Case], dict]:
    cases, stats = [], SetterStats()
    for band in bands:
        made = 0
        for i in range(per_band * 12):
            if made >= per_band:
                break
            a = make_case(
                variant=variant,
                size=size,
                band=band,
                seed=seed0 + i * 977,
                attempts=20,
                time_limit_s=5.0,
                stats=stats,
            )
            if not a.ok or a.case is None:
                continue
            if verify:
                g = gate(a.case, expect_band=band)
                if not g.ok:
                    stats.reject("gate_" + ",".join(g.failed))
                    continue
            cases.append(a.case)
            made += 1
    return cases, stats.to_json()


def summarize(rows: list[dict]) -> str:
    by = defaultdict(list)
    for r in rows:
        by[(r["agent"], r["mode"], r["band"])].append(r)
    out = [
        f"{'agent':<22} {'mode':<8} {'band':<7} {'n':>3} {'success':>7} "
        f"{'answer':>7} {'placed':>7} {'exact':>6} {'turns':>6} {'py':>4} "
        f"{'retry':>5} {'wall':>7}"
    ]
    for (agent, mode, band), rs in sorted(
        by.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][2] or "")
    ):
        n = len(rs)
        success = sum(r["score"]["solved"] for r in rs) / n
        acc = sum(r["score"]["answer_correct"] for r in rs) / n
        pl = sum(r["score"]["placement_accuracy"] for r in rs) / n
        ex = sum(r["score"]["placement_exact"] for r in rs) / n
        tn = sum(r["turns"] for r in rs) / n
        py = sum(r.get("python_calls", 0) for r in rs) / n
        retries = sum((r.get("usage") or {}).get("retries", 0) for r in rs)
        wall = sum(r.get("wall_s", 0) for r in rs) / n
        out.append(
            f"{agent:<22} {mode:<8} {str(band):<7} {n:>3} {success:>7.2f} "
            f"{acc:>7.2f} {pl:>7.2f} {ex:>6.2f} {tn:>6.1f} {py:>4.1f} "
            f"{retries:>5} {wall:>7.1f}"
        )
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--agents", default="oracle,chance")
    ap.add_argument("--modes", default="agentic")
    ap.add_argument("--bands", default="easy,medium,hard")
    ap.add_argument("--per-band", type=int, default=2)
    ap.add_argument("--variant", default="classic")
    ap.add_argument("--size", type=int, default=6)
    ap.add_argument("--seed", type=int, default=1000)
    ap.add_argument(
        "--theme",
        default="manor",
        help="bundled id, 'canonical', or 'official' for imported cases",
    )
    ap.add_argument(
        "--view",
        choices=("compact", "classic"),
        default="compact",
        help="solver-facing scene representation",
    )
    ap.add_argument("--model", default=None)
    ap.add_argument("--max-turns", type=int, default=8)
    ap.add_argument("--max-tokens-per-turn", type=int, default=24576)
    ap.add_argument("--max-total-completion-tokens", type=int, default=49152)
    ap.add_argument(
        "--episode-timeout",
        type=float,
        default=1200.0,
        help="hard wall-clock budget per case; 0 disables",
    )
    ap.add_argument(
        "--no-check", action="store_true", help="disable the `check` assist"
    )
    ap.add_argument(
        "--no-python",
        action="store_true",
        help="disable the `python` action — the control arm for 'does code help?'",
    )
    ap.add_argument(
        "--cases", default=None, help="load a case jsonl instead of generating"
    )
    ap.add_argument(
        "--case-json",
        default=None,
        help="load a JSON *list* of case records (e.g. a hand-picked expert set)",
    )
    ap.add_argument(
        "--case-index",
        type=int,
        default=None,
        help="after loading --cases/--case-json, run only this zero-based case",
    )
    ap.add_argument("--out", default=None)
    ap.add_argument(
        "--resume",
        action="store_true",
        help="append missing episodes to an existing output file",
    )
    ap.add_argument("--verify", action="store_true", default=True)
    a = ap.parse_args(argv)

    bands = [b for b in a.bands.split(",") if b]
    if a.case_json:
        loaded = json.loads(Path(a.case_json).read_text())
        cases = [
            Case.from_json(r)
            for r in (loaded if isinstance(loaded, list) else [loaded])
        ]
        gen_stats = {"loaded": len(cases)}
    elif a.cases:
        cases = [
            Case.from_json(json.loads(l))
            for l in Path(a.cases).read_text().splitlines()
            if l
        ]
        gen_stats = {"loaded": len(cases)}
    else:
        cases, gen_stats = build_set(
            bands, a.per_band, a.variant, a.size, a.seed, a.verify
        )
    if a.case_index is not None:
        if not (0 <= a.case_index < len(cases)):
            raise SystemExit(f"--case-index {a.case_index} outside 0..{len(cases) - 1}")
        cases = [cases[a.case_index]]
        gen_stats = {**gen_stats, "selected_index": a.case_index}
    print(
        f"case set: {len(cases)} case(s)  | setter: {json.dumps(gen_stats)}",
        file=sys.stderr,
    )
    if not cases:
        print("no cases generated", file=sys.stderr)
        return 1

    out = Path(a.out) if a.out else ROOT / "results" / "bench_latest.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    if a.resume and out.exists():
        rows = [json.loads(line) for line in out.read_text().splitlines() if line]
    done = {
        (
            r["case_id"],
            r["mode"],
            r["agent"],
            r.get("theme_id"),
            r.get("scene_format", "classic"),
        )
        for r in rows
    }
    if not a.resume:
        out.write_text("")
    for case in cases:
        theme = _theme(case, a.theme)
        for mode in a.modes.split(","):
            for kind in a.agents.split(","):
                agent = build_agent(
                    kind,
                    case,
                    theme,
                    seed=a.seed,
                    model=a.model,
                    max_tokens=a.max_tokens_per_turn,
                    max_total_completion_tokens=a.max_total_completion_tokens,
                )
                key = (case.content_hash(), mode, agent.name, theme.theme_id, a.view)
                if key in done:
                    continue
                kw = {"scene_format": a.view}
                if mode != "direct":
                    kw.update(
                        {
                            "max_turns": a.max_turns,
                            "allow_check": not a.no_check,
                            "allow_python": not a.no_python,
                        }
                    )
                res = _run_with_deadline(
                    a.episode_timeout, RUNNERS[mode], case, agent, theme, **kw
                )
                row = res.to_json()
                row["source"] = case.meta.get("source", "local_generated")
                row["source_id"] = case.meta.get("official_id", case.content_hash())
                row["size"] = f"{case.scene.W}x{case.scene.H}"
                row["difficulty"] = {
                    "target_band": case.target_band,
                    "official": case.meta.get("official_difficulty"),
                    "certificate": (
                        {
                            k: case.certificate.get(k)
                            for k in (
                                "depth",
                                "advanced",
                                "tier_max",
                                "max_width",
                                "cost",
                            )
                        }
                        if case.certificate
                        else None
                    ),
                }
                # Record how the case set was built. Without this a finished jsonl cannot be
                # re-scored or reproduced: the setter is deterministic, but only given these.
                row["run"] = {
                    "no_python": bool(a.no_python),
                    "variant": a.variant,
                    "size": a.size,
                    "seed": a.seed,
                    "per_band": a.per_band,
                    "bands": bands,
                    "model": a.model,
                    "max_turns": a.max_turns,
                    "no_check": bool(a.no_check),
                    "max_tokens_per_turn": a.max_tokens_per_turn,
                    "max_total_completion_tokens": a.max_total_completion_tokens,
                    "episode_timeout": a.episode_timeout,
                    "verify": bool(a.verify),
                    "cases_file": a.cases,
                    "scene_format": a.view,
                }
                rows.append(row)
                with out.open("a") as f:
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
                done.add(key)
                (out.with_suffix(".summary.txt")).write_text(summarize(rows) + "\n")
                sc = res.score
                print(
                    f"  {case.target_band:<7} {mode:<8} {res.agent:<20} "
                    f"answer={'OK ' if sc['answer_correct'] else 'X  '} "
                    f"placed={sc['placement_accuracy']:.2f} turns={res.turns} "
                    f"{res.error or ''}",
                    file=sys.stderr,
                )

    table = summarize(rows)
    (out.with_suffix(".summary.txt")).write_text(table + "\n")
    print("\n" + table)
    print(f"\nwrote {out}  and  {out.with_suffix('.summary.txt')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
