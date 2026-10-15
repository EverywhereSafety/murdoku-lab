"""Build the theme showcase: one 6×6, one 7×7 and one 8×8 case for every setting pack.

    python scripts/build_showcase.py                 # generate (cached per size) and dress
    python scripts/build_showcase.py --regenerate --workers 8

Cases come from the constraint-first farm with the player rhythm policy and the cozy scene spec
(denser rooms). Case i of every size is dressed in setting i, so each setting gets one case per
size. A setting's cases get different titles, and none of the titles the locked daily cases use. The result, `cases.jsonl`, holds `murdoku_case` + `murdoku_theme` records that the Lab and
the gallery read:

    python -m murdoku_lab.visual.server --records outputs/showcase/cases.jsonl
    python scripts/art_gallery.py --showcase outputs/showcase/cases.jsonl
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from murdoku_lab.core.instance import Case
from murdoku_lab.setter import settings

ROOT = Path(__file__).resolve().parents[1]
SLOTS = ((6, "easy"), (7, "medium"), (8, "medium"))
SEED = 31


def generate(path, size, band, n, workers):
    command = [
        sys.executable,
        "-m",
        "murdoku_lab.setter.farm",
        "--strategy",
        "constraint-first",
        "--variant",
        "classic",
        "--size",
        str(size),
        "--bands",
        band,
        "--n",
        str(n),
        "--shots",
        "8",
        "--workers",
        str(workers),
        "--seed",
        str(SEED + size),
        "--rhythm-policy",
        str(ROOT / "config" / "rhythm" / "player.json"),
        "--scene-spec",
        str(ROOT / "config" / "scene_specs" / "cozy.json"),
        "--out",
        str(path),
    ]
    with open(path.with_suffix(".log"), "w") as log:
        subprocess.run(
            command, check=True, stdout=log, stderr=subprocess.STDOUT, cwd=ROOT
        )


def daily_titles():
    """Titles of the locked daily cases, per setting: the showcase leaves them to the daily."""
    used = {}
    for path in sorted((ROOT / "content" / "daily").glob("*/days/*.json")):
        record = json.loads(path.read_text())
        used.setdefault(record["setting"], set()).add(record["murdoku_theme"]["title"])
    return used


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(ROOT / "outputs" / "showcase"))
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--regenerate", action="store_true")
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    ids = settings.available()
    records = []
    daily = daily_titles()
    titles = {setting_id: set(daily.get(setting_id, ())) for setting_id in ids}
    for size, band in SLOTS:
        path = out / f"s{size}-{band}.jsonl"
        if args.regenerate or not path.exists():
            print(f"generating {len(ids)} {size}×{size} {band} cases …", flush=True)
            generate(path, size, band, len(ids), args.workers)
        rows = [
            json.loads(line) for line in path.read_text().splitlines() if line.strip()
        ]
        cases = [Case.from_json(row.get("murdoku_case", row)) for row in rows]
        if not cases:
            raise SystemExit(f"{path} has no cases")
        if len(cases) < len(ids):
            print(
                f"warning: only {len(cases)} {size}×{size} cases; some settings share one"
            )
        for i, setting_id in enumerate(ids):
            case = cases[i % len(cases)]
            # A setting's cases should not share a title; try a few salts before giving in.
            for attempt in range(40):
                theme = settings.dress(
                    case, setting_id, salt=str(attempt) if attempt else ""
                )
                if theme.title not in titles[setting_id]:
                    break
            titles[setting_id].add(theme.title)
            records.append(
                {
                    "visual_case_id": f"{setting_id}-{size}x{size}",
                    "murdoku_case": case.to_json(),
                    "murdoku_theme": theme.to_json(),
                }
            )
    records.sort(key=lambda r: r["visual_case_id"])
    target = out / "cases.jsonl"
    target.write_text("".join(json.dumps(r) + "\n" for r in records))
    print(f"wrote {target} with {len(records)} cases")


if __name__ == "__main__":
    main()
