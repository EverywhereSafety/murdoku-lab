"""Publish the difficulty dial's accuracy: per-band achieved distribution AND hit rate.

    python -m murdoku_lab.evaluation.calibrate --bands easy,medium,hard,expert --n 8 --sizes 6,7

A band that cannot be hit reliably is reported as such. This script is the honesty mechanism:
it is what distinguishes "controlled difficulty" from "requested difficulty".
"""

from __future__ import annotations

import argparse
import json
import statistics as stat
from collections import Counter, defaultdict
from pathlib import Path

from murdoku_lab.setter.pipeline import SetterStats, gate, make_case

from murdoku_lab.paths import PROJECT_ROOT

ROOT = PROJECT_ROOT


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--bands", default="easy,medium,hard,expert")
    ap.add_argument("--sizes", default="6,7")
    ap.add_argument("--n", type=int, default=6, help="requests per (band, size)")
    ap.add_argument("--variant", default="classic")
    ap.add_argument("--attempts", type=int, default=25)
    ap.add_argument("--time-limit", type=float, default=5.0)
    ap.add_argument("--seed", type=int, default=500)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)

    rows = []
    for size in [int(s) for s in a.sizes.split(",")]:
        for band in a.bands.split(","):
            st = SetterStats()
            got, feats = 0, defaultdict(list)
            landed = Counter()
            for i in range(a.n):
                att = make_case(
                    variant=a.variant,
                    size=size,
                    band=band,
                    seed=a.seed + i * 6151,
                    attempts=a.attempts,
                    time_limit_s=a.time_limit,
                    stats=st,
                )
                landed[str(att.band)] += 1
                if att.ok and att.case is not None:
                    got += 1
                    c = att.case.certificate
                    for k in ("advanced", "depth", "tier_max", "max_width", "cost"):
                        feats[k].append(c[k])
                    feats["clues"].append(len(att.case.clues))
                    feats["atoms"].append(len(att.case.atoms))
            row = {
                "size": size,
                "band": band,
                "requested": a.n,
                "hit": got,
                "hit_rate": round(got / a.n, 3),
                "landed_in": dict(landed),
                "median": {
                    k: (round(stat.median(v), 2) if v else None)
                    for k, v in feats.items()
                },
                "setter": st.to_json(),
            }
            rows.append(row)
            m = row["median"]
            print(
                f"n={size} {band:<7} hit {got}/{a.n} ({row['hit_rate']:.2f})  "
                f"adv~{m.get('advanced')} depth~{m.get('depth')} clues~{m.get('clues')} "
                f"atoms~{m.get('atoms')}  landed={dict(landed)}"
            )

    out = Path(a.out) if a.out else ROOT / "results" / "difficulty_calibration.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows, indent=2) + "\n")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
