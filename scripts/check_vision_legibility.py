"""Check that casebook vision exports stay legible, setting by setting.

    python scripts/check_vision_legibility.py
    python scripts/check_vision_legibility.py --records outputs/showcase/cases.jsonl

Every dressed case goes through `legibility.check` (key coverage, plaques, contrast, floor ΔE00,
coordinate size at 1568 and 1024px wide) in day and night. Every setting's twenty object
drawings are rasterised side by side and compared: each one's nearest look-alike must stay
far enough away that a reader cannot confuse the two. Writes report.md and report.json and
exits 1 when anything fails.
"""

import argparse
import json
from pathlib import Path

from murdoku_lab.core.instance import Case
from murdoku_lab.core.theme import Theme
from murdoku_lab.environment.state import Scratchpad
from murdoku_lab.setter import settings
from murdoku_lab.visual.art import legibility
from murdoku_lab.visual.demos import glasshouse, lily_pond
from murdoku_lab.visual.projection import public_observation
from murdoku_lab.visual.raster import bundled_profile, png_from_svg

ROOT = Path(__file__).resolve().parents[1]
# RMS distance between 16×16 colour signatures; below this two objects read as one.
MIN_GLYPH_DISTANCE = 0.06


def setting_items(setting_id):
    skins = settings.load(setting_id)["visual"].get("skins", {})
    return [(kind, skins.get(kind)) for kind in settings.CLASSIC_KINDS]


def glyph_report(setting_id):
    items = setting_items(setting_id)
    png = png_from_svg(legibility.glyph_sheet(items), profile=bundled_profile())
    nouns = settings.load(setting_id)["objects"]
    rows = []
    for i, j, distance in legibility.glyph_distances(items, png):
        rows.append(
            {
                "object": nouns[items[i][0]],
                "nearest": nouns[items[j][0]],
                "distance": round(distance, 4),
                "ok": distance >= MIN_GLYPH_DISTANCE,
            }
        )
    return sorted(rows, key=lambda r: r["distance"])


def cases(records):
    if records:
        for line in Path(records).read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                yield row["visual_case_id"], Case.from_json(
                    row["murdoku_case"]
                ), Theme.from_json(row["murdoku_theme"])
        return
    for entry in (glasshouse(), lily_pond()):
        for setting_id in settings.available():
            yield f"{entry.slug}-{setting_id}", entry.case, settings.dress(
                entry.case, setting_id
            )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", help="dressed records (scripts/build_showcase.py)")
    parser.add_argument("--out", default=str(ROOT / "outputs" / "legibility"))
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    board_rows, failures = [], 0
    for slug, case, theme in cases(args.records):
        obs = public_observation(Scratchpad(case, theme))
        for mode in ("day", "night"):
            found = legibility.check(obs, theme=mode)
            failures += len(found["problems"])
            board_rows.append({"case": slug, "theme": mode, **found})

    glyphs = {sid: glyph_report(sid) for sid in settings.available()}
    failures += sum(not row["ok"] for rows in glyphs.values() for row in rows)

    report = {
        "boards": board_rows,
        "glyphs": glyphs,
        "min_glyph_distance": MIN_GLYPH_DISTANCE,
    }
    (out / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    )
    lines = ["# Vision legibility", ""]
    lines.append(f"{len(board_rows)} board checks, {failures} problem(s).")
    lines += [
        "",
        "## Boards",
        "",
        "| case | theme | axis contrast | min floor ΔE00 | axis px @1024 | problems |",
        "|---|---|---|---|---|---|",
    ]
    for row in board_rows:
        m = row["metrics"]
        lines.append(
            f"| {row['case']} | {row['theme']} | {m['axis_contrast']} | {m['min_floor_delta_e']} | "
            f"{m['axis_px_at_1024']} | {'; '.join(row['problems']) or 'none'} |"
        )
    lines += ["", "## Closest look-alikes per setting", ""]
    for setting_id, rows in glyphs.items():
        worst = rows[:3]
        lines.append(
            f"- **{setting_id}**: "
            + ", ".join(
                f"{r['object']} ≈ {r['nearest']} ({r['distance']})" for r in worst
            )
        )
    (out / "report.md").write_text("\n".join(lines) + "\n")
    print(f"wrote {out / 'report.md'}: {failures} problem(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
