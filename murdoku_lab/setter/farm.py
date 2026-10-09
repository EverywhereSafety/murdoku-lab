"""Run many independent generation attempts across processes, and keep the ones that land.

Where the parallelism actually is, and where it is not:

  * An ATTEMPT is independent of every other attempt — different seed, different board, different clue
    choices. Perfectly parallel, and the right place to spend cores when the failures are
    luck-of-the-draw (`caps_violated`, `band_miss_*`, `not solvable by pure logic`).
  * A CARVE is a sequential chain: each drop is decided against the set the previous drop left. Cores
    do not shorten one carve.
  * Constraint-first scores candidate clues against already-enumerated witness solutions in memory.
    It therefore also benefits most from parallelising independent attempts, not nested workers.

So this module fans out attempts and leaves each attempt single-threaded. That keeps one level of
parallelism (nested pools deadlock or oversubscribe) and means the same code runs unchanged on a box
with 8 cores or a cluster with 800 — only `--workers` changes.

    python3 -m murdoku_lab.setter.farm --variant classic --size 6 --bands easy,medium,hard,expert --n 4 --workers 8
    python3 -m murdoku_lab.setter.farm --strategy constraint-first --variant course --size 16 --n 2 --workers 8
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from pathlib import Path

from murdoku_lab.paths import PROJECT_ROOT

ROOT = PROJECT_ROOT


@dataclass
class Landed:
    band: str | None = None
    variant: str = ""
    size: int = 0
    seed: int = 0
    strategy: str = ""
    ok: bool = False
    reason: str = ""
    n_clues: int = 0
    n_atoms: int = 0
    advanced: int | None = None
    depth: int | None = None
    wall_s: float = 0.0
    solves: int | None = None
    record: dict | None = field(default=None, repr=False)


def _attempt(payload) -> dict:
    """One independent attempt, single-threaded. Runs in a worker process."""
    (
        strategy,
        variant,
        size,
        band,
        seed,
        time_limit,
        attempts,
        beam,
        max_clues,
        cap,
        *extra,
    ) = payload
    n_areas = extra[0] if extra else None
    scene_spec = extra[1] if len(extra) > 1 else None
    t0 = time.time()
    out = Landed(band=band, variant=variant, size=size, seed=seed, strategy=strategy)
    try:
        if strategy == "constraint-first":
            from murdoku_lab.setter.constraint_first import generate

            r = generate(
                variant=variant,
                size=size,
                band=band,
                seed=seed,
                workers=1,
                beam=beam,
                max_clues=max_clues,
                cap=cap,
                attempts=attempts,
                time_limit_s=time_limit,
                n_areas=n_areas,
                scene_spec=scene_spec,
            )
            out.reason = r.reason
            out.solves = r.solves
            if r.case is not None and not r.reason:
                from murdoku_lab.setter.pipeline import gate

                g = gate(
                    r.case,
                    expect_band=band,
                    time_limit_s=time_limit * 3,
                    exact_count=False,
                )
                if g.ok:
                    out.ok = True
                    out.n_clues, out.n_atoms = r.n_clues, r.n_atoms
                    out.advanced = r.certificate.advanced if r.certificate else None
                    out.depth = r.certificate.depth if r.certificate else None
                    out.record = r.case.to_json()
                else:
                    out.reason = "gate_" + "+".join(g.failed)
        else:
            from murdoku_lab.setter.pipeline import gate, make_case

            a = make_case(
                variant=variant,
                size=size,
                band=band,
                seed=seed,
                attempts=attempts,
                time_limit_s=time_limit,
                n_areas=n_areas,
                scene_spec=scene_spec,
            )
            out.reason = a.reason
            if a.ok and a.case is not None:
                g = gate(a.case, expect_band=band, time_limit_s=time_limit * 4)
                if g.ok:
                    out.ok = True
                    out.n_clues, out.n_atoms = len(a.case.clues), len(a.case.atoms)
                    c = a.certificate
                    out.advanced = c.advanced if c else None
                    out.depth = c.depth if c else None
                    out.record = a.case.to_json()
                else:
                    out.reason = "gate_" + "+".join(g.failed)
    except Exception as e:  # noqa: BLE001
        out.reason = f"{type(e).__name__}: {e}"
    out.wall_s = round(time.time() - t0, 1)
    return asdict(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__.splitlines()[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--strategy",
        choices=["placement-first", "constraint-first"],
        default="placement-first",
    )
    ap.add_argument("--variant", default="classic")
    ap.add_argument("--n-areas", type=int, default=None)
    ap.add_argument(
        "--scene-spec",
        type=Path,
        default=None,
        help="public scene_spec/1 JSON for area count and standable anchors per area",
    )
    ap.add_argument("--size", type=int, default=6)
    ap.add_argument("--bands", default="medium")
    ap.add_argument("--n", type=int, default=4, help="how many cases wanted PER BAND")
    ap.add_argument(
        "--shots",
        type=int,
        default=6,
        help="attempts fanned out per wanted case; raise it to trade cores for yield",
    )
    ap.add_argument("--attempts", type=int, default=6, help="inner retries per attempt")
    ap.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 1))
    ap.add_argument("--time-limit", type=float, default=10.0)
    ap.add_argument(
        "--beam",
        type=int,
        default=64,
        help="constraint-first candidates compared per clue",
    )
    ap.add_argument("--max-clues", type=int, default=60)
    ap.add_argument(
        "--solution-cap",
        type=int,
        default=50,
        help="witness placements retained per exact solve",
    )
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    from murdoku_lab.setter.scene_spec import normalize_spec

    spec = normalize_spec(
        json.loads(a.scene_spec.read_text()) if a.scene_spec else None,
        size=a.size,
        n_areas=a.n_areas,
    )

    bands = [b for b in a.bands.split(",") if b]
    rng = random.Random(a.seed)
    jobs = [
        (
            a.strategy,
            a.variant,
            a.size,
            b,
            rng.randrange(10**8),
            a.time_limit,
            a.attempts,
            a.beam,
            a.max_clues,
            a.solution_cap,
            a.n_areas,
            spec,
        )
        for b in bands
        for _ in range(a.n * a.shots)
    ]
    print(
        f"{len(jobs)} attempt(s) over {a.workers} worker(s): {a.strategy}, {a.variant} "
        f"{a.size}x{a.size}, bands {bands}, want {a.n}/band",
        flush=True,
    )

    want = {b: a.n for b in bands}
    got: dict[str, list[dict]] = {b: [] for b in bands}
    rejects: Counter = Counter()
    t0 = time.time()
    done = 0
    accepted_jobs = 0
    total_attempt_s = 0.0
    outp = ROOT / a.out if a.out else None
    statsp = outp.with_suffix(".farm_stats.json") if outp else None
    if outp:
        outp.parent.mkdir(parents=True, exist_ok=True)
        outp.write_text("")

    def checkpoint() -> None:
        if outp is None or statsp is None:
            return
        landed_now = sum(len(v) for v in got.values())
        records = [
            x
            for b in bands
            for x in sorted(got[b], key=lambda z: z["seed"])
            if x["record"]
        ]
        outp.write_text(
            "".join(json.dumps(x["record"], ensure_ascii=False) + "\n" for x in records)
        )
        statsp.write_text(
            json.dumps(
                {
                    "strategy": a.strategy,
                    "variant": a.variant,
                    "size": a.size,
                    "n_areas": a.n_areas,
                    "scene_spec": spec,
                    "bands": bands,
                    "requested_per_band": a.n,
                    "shots": a.shots,
                    "finished_jobs": done,
                    "accepted_jobs": accepted_jobs,
                    "written_cases": landed_now,
                    "wall_s": round(time.time() - t0, 3),
                    "acceptance_rate": round(accepted_jobs / max(1, done), 6),
                    "landed_wall_s": (
                        round((time.time() - t0) / landed_now, 3)
                        if landed_now
                        else None
                    ),
                    "attempt_process_s": round(total_attempt_s, 3),
                    "process_s_per_accepted": (
                        round(total_attempt_s / accepted_jobs, 3)
                        if accepted_jobs
                        else None
                    ),
                    "rejects": dict(rejects),
                    "constraint_first": {
                        "beam": a.beam,
                        "max_clues": a.max_clues,
                        "solution_cap": a.solution_cap,
                    },
                },
                indent=2,
            )
            + "\n"
        )

    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(_attempt, j): j for j in jobs}
        for fut in as_completed(futs):
            r = fut.result()
            done += 1
            total_attempt_s += float(r["wall_s"])
            b = r["band"]
            if r["ok"]:
                accepted_jobs += 1
                if len(got[b]) < want[b]:
                    got[b].append(r)
                    print(
                        f"  [{done}/{len(jobs)}] {b:7} LANDED clues={r['n_clues']:2} "
                        f"atoms={r['n_atoms']:2} adv={r['advanced']} depth={r['depth']} "
                        f"{r['wall_s']}s",
                        flush=True,
                    )
            elif not r["ok"]:
                rejects[r["reason"][:48] or "?"] += 1
            checkpoint()

    wall = time.time() - t0
    print(f"\n=== {wall:.0f}s wall, {done} attempt(s) finished ===")
    for b in bands:
        print(
            f"  {b:7} {len(got[b])}/{want[b]}"
            + (
                f"  中位 clues={sorted(x['n_clues'] for x in got[b])[len(got[b]) // 2]}"
                f" atoms={sorted(x['n_atoms'] for x in got[b])[len(got[b]) // 2]}"
                if got[b]
                else ""
            )
        )
    if rejects:
        print("\n  拒绝原因:")
        for why, n in rejects.most_common(8):
            print(f"    x{n:3}  {why}")
    landed = sum(len(v) for v in got.values())
    print(
        f"\n  {landed} written case(s), {accepted_jobs}/{done} accepted jobs; "
        f"{wall / max(1, landed):.0f}s per written case at {a.workers} workers"
    )

    if outp:
        checkpoint()
        print(f"  wrote {outp}")
        print(f"  stats {statsp}")
    return 0 if landed else 1


if __name__ == "__main__":
    raise SystemExit(main())
