"""Export gated Case/RL records into paired text and image queries.

Usage: python -m murdoku_lab.setter.export_queries --input cases.jsonl --out query_bundle
Private *.rl.jsonl retain the existing environment schema; public/ contains only
model-facing fields. PNG paths are relative to the bundle root.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from murdoku_lab.core.instance import Case
from murdoku_lab.core.theme import Theme
from murdoku_lab.core.name_library import preset_theme
from murdoku_lab.environment.queries import make_record, public_record
from murdoku_lab.setter.pipeline import gate
from murdoku_lab.solver.difficulty import respects_caps, style_ok


def load_records(path):
    if path.suffix == ".jsonl":
        return [
            json.loads(line) for line in path.read_text().splitlines() if line.strip()
        ]
    value = json.loads(path.read_text())
    return value if isinstance(value, list) else [value]


def export_case(
    case, theme, destination, *, views=("text", "vision"), artwork_style="art"
):
    """Pure view export for a case already admitted by the caller's gate."""
    result = {}
    if "text" in views:
        result["text"] = make_record(case, theme, view="text")
    if "vision" in views:
        from murdoku_lab.environment.state import Scratchpad
        from murdoku_lab.visual.art import board_svg
        from murdoku_lab.visual.projection import public_observation
        from murdoku_lab.visual.raster import png_from_svg

        data = png_from_svg(
            board_svg(public_observation(Scratchpad(case, theme)), style=artwork_style)
        )
        suffix = "" if artwork_style == "art" else "-" + artwork_style
        relative = f"images/{case.content_hash()}{suffix}.png"
        path = destination / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        result["vision"] = make_record(
            case, theme, view="vision", image_path=relative, image_bytes=data
        )
        result["vision"]["artwork_style"] = artwork_style
    return result


def write_bundle(
    records,
    destination,
    *,
    views=("text", "vision"),
    time_limit_s=15,
    artwork_style="art",
):
    if not views or any(view not in ("text", "vision") for view in views):
        raise ValueError("views must contain text and/or vision")
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    (destination / "public").mkdir()
    private = {view: [] for view in views}
    results, seen = [], set()
    for source in records:
        case = Case.from_json(source.get("murdoku_case", source))
        theme = (
            Theme.from_json(source["murdoku_theme"])
            if source.get("murdoku_theme")
            else preset_theme(case)
        )
        identity = case.content_hash()
        if identity in seen:
            continue
        seen.add(identity)
        report = gate(
            case,
            expect_band=case.target_band,
            exact_count=False,
            time_limit_s=time_limit_s,
        )
        actual_band = report.detail.get("band")
        report.checks["caps_respected"] = bool(actual_band) and respects_caps(
            case, actual_band
        )
        report.checks["style_floor"] = bool(actual_band) and style_ok(
            case.atoms, actual_band, len(case.characters)
        )
        admitted = report.ok and all(report.checks.values())
        admission = {
            "case_id": identity,
            "accepted": admitted,
            "band": actual_band,
            "gate_checks": report.checks,
        }
        if admitted:
            rendered = export_case(
                case, theme, destination, views=views, artwork_style=artwork_style
            )
            for view, record in rendered.items():
                original_uid = source.get("prompt_uid", identity)
                if source.get("murdoku_observation") == "vision":
                    original_uid = identity
                record["prompt_uid"] = (
                    original_uid if view == "text" else original_uid + "-vision"
                )
                for field in ("split", "agent_info", "allow_check", "murdoku_reward"):
                    if field in source:
                        record[field] = source[field]
                record["query_validation"] = {
                    "gate_passed": True,
                    "band": actual_band,
                    "gate_checks": report.checks,
                }
                private[view].append(record)
        results.append(admission)
    files = {}
    for view, rows in private.items():
        path = destination / f"{view}.rl.jsonl"
        path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
        public = destination / "public" / f"{view}.jsonl"
        public.write_text(
            "".join(
                json.dumps(public_record(r), ensure_ascii=False) + "\n" for r in rows
            )
        )
        files[view] = {
            "records": path.name,
            "public_records": str(public.relative_to(destination)),
            "count": len(rows),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    manifest = {
        "schema": "murdoku.query_bundle/1",
        "views": files,
        "cases": len(seen),
        "accepted_cases": sum(r["accepted"] for r in results),
        "admission": results,
        "image_references": "relative to bundle root; resolve with murdoku_lab.environment.queries.model_inputs",
        "legacy_text_record_schema_preserved": True,
        "model_calls": 0,
        "private_files": "*.rl.jsonl contain environment cases and answers; send only model_inputs to the model",
    }
    (destination / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    )
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--views", default="text,vision")
    parser.add_argument(
        "--artwork-style", choices=("art", "diagram", "fluent"), default="art"
    )
    parser.add_argument("--time-limit", type=float, default=15)
    args = parser.parse_args()
    views = tuple(dict.fromkeys(args.views.split(",")))
    if not views or any(v not in ("text", "vision") for v in views):
        parser.error("--views must contain text and/or vision")
    manifest = write_bundle(
        load_records(args.input),
        args.out,
        views=views,
        time_limit_s=args.time_limit,
        artwork_style=args.artwork_style,
    )
    print(
        json.dumps(
            {"accepted_cases": manifest["accepted_cases"], "views": manifest["views"]},
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
