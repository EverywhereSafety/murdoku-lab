"""CLI: generate a verified case corpus.

    python -m murdoku_lab.setter.generate --band medium --n 20 --size 7 --out data/cases/medium_n7.jsonl
    python -m murdoku_lab.setter.generate --bands easy,medium,hard --n 10 --theme manor --render 1

Every emitted record has passed `gate()`: proved-unique solution, pure-logic solvable, no useless
clue, band as requested, caps and style floors respected. The setter's reject histogram and the hit
rate are written alongside, because a difficulty dial you cannot miss with is not being measured.

`--split` additionally writes the pair of files a solver-facing corpus needs (`murdoku_lab/setter/emit.py`):

    <id>.puzzle.json   prose, map, cast, clues   <- all a solver is given
    <id>.key.json      answer + the mathematical warrant

The mathematics justifies the puzzle; the prose *is* the puzzle. Keeping them in one record, as
`to_json` does, is right for our own regression corpus and wrong for anything handed to a solver,
because the answer sits in the same file.

`--verify-prose` goes further and round-trips each statement (`murdoku_lab/evaluation/roundtrip.py`): the prose alone is
translated back to constraints and must admit exactly the answer key. That proves the English states
the same puzzle as the atoms rather than merely being rendered from them. It needs an API key, so it
is opt-in — with it off, `prose_roundtrip.checked` is recorded as false rather than assumed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from murdoku_lab.core.theme import Theme
from murdoku_lab.core.name_library import preset_theme
from murdoku_lab.core.render import render_case
from murdoku_lab.setter.pipeline import SetterStats, gate, make_case

from murdoku_lab.paths import PROJECT_ROOT

ROOT = PROJECT_ROOT


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--bands", "--band", dest="bands", default="medium")
    ap.add_argument("--n", type=int, default=5, help="cases per band")
    ap.add_argument("--size", type=int, default=6)
    ap.add_argument("--variant", default="classic")
    ap.add_argument("--n-areas", type=int, default=None)
    ap.add_argument(
        "--scene-spec",
        type=Path,
        default=None,
        help="public scene_spec/1 JSON for area count and standable anchors per area",
    )
    ap.add_argument(
        "--query-dir",
        type=Path,
        default=None,
        help="also export paired text/vision queries and PNGs into a new directory",
    )
    ap.add_argument(
        "--views", default="text,vision", help="query views: text, vision, or both"
    )
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--attempts", type=int, default=25)
    ap.add_argument("--time-limit", type=float, default=5.0)
    ap.add_argument("--theme", default=None, help="use a bundled theme by id")
    ap.add_argument(
        "--llm-theme",
        default=None,
        metavar="STYLE",
        help="author a FRESH theme per case with the model, in this style "
        "(e.g. 'a 1970s roller disco'). Needs an API key; falls back to a bundled "
        "theme if the call fails, and the record says which was used.",
    )
    ap.add_argument(
        "--render", type=int, default=0, help="print the first N cases as text"
    )
    ap.add_argument(
        "--no-gate", action="store_true", help="skip re-verification (not advised)"
    )
    ap.add_argument(
        "--split",
        default=None,
        help="directory for solver-facing <id>.puzzle.json + <id>.key.json pairs",
    )
    ap.add_argument(
        "--verify-prose",
        action="store_true",
        help="round-trip each statement through a model; needs an API key",
    )
    ap.add_argument("--prose-model", default="kimi-k3")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    query_views = tuple(dict.fromkeys(a.views.split(",")))
    if not query_views or any(v not in ("text", "vision") for v in query_views):
        ap.error("--views must contain text and/or vision")
    if a.query_dir and a.query_dir.exists():
        ap.error("--query-dir must name a new directory")
    from murdoku_lab.setter.scene_spec import normalize_spec

    spec = normalize_spec(
        json.loads(a.scene_spec.read_text()) if a.scene_spec else None,
        size=a.size,
        n_areas=a.n_areas,
    )

    bands = [b for b in a.bands.split(",") if b]
    stats = SetterStats()
    stats.requested = a.n * len(bands)
    records, rendered = [], 0
    query_sources = []

    for band in bands:
        made = 0
        for i in range(a.n * 15):
            if made >= a.n:
                break
            att = make_case(
                variant=a.variant,
                size=a.size,
                band=band,
                seed=a.seed + i * 7919,
                attempts=a.attempts,
                time_limit_s=a.time_limit,
                stats=stats,
                n_areas=a.n_areas,
                scene_spec=spec,
            )
            if not att.ok or att.case is None:
                continue
            case = att.case
            if not a.no_gate:
                g = gate(case, expect_band=band)
                if not g.ok:
                    stats.reject("gate_" + "+".join(g.failed))
                    continue
            # Resolve a fresh LLM theme, a bundled theme, or preset display names.
            th = preset_theme(case)
            if a.llm_theme:
                from murdoku_lab.setter.llm_setter import theme_for

                tr = theme_for(case, style=a.llm_theme, seed=a.seed + i)
                th = tr.theme
                print(
                    f"  {band:<7} theme[{tr.source}] {th.theme_id}: {th.title}",
                    file=sys.stderr,
                )
            elif a.theme:
                th = Theme.load(a.theme)
            if th is not None:
                th.validate(case)
                from dataclasses import replace

                case = replace(case, theme_id=th.theme_id)
            records.append(case.to_json())
            made += 1

            if a.split:
                from murdoku_lab.setter.emit import emit as emit_pair

                rt = {"checked": False}
                if a.verify_prose:
                    from murdoku_lab.evaluation.roundtrip import check_case
                    from dataclasses import asdict as _asdict

                    r = check_case(case, th, a.prose_model, 2, a.time_limit * 4)
                    # "the check found a problem" and "the check could not run" are different things.
                    # Dropping a case because an API call returned no JSON would quietly destroy yield
                    # and would be evidence of nothing. Only a substantive verdict rejects.
                    substantive = {"weaker", "stronger", "different"}
                    rt = {
                        "checked": r.verdict in (substantive | {"faithful"}),
                        **_asdict(r),
                    }
                    if r.verdict in substantive:
                        stats.reject(f"prose_{r.verdict}")
                        records.pop()
                        made -= 1
                        print(
                            f"  {band:<7} prose NOT faithful ({r.verdict}: {r.detail[:60]}) "
                            f"— case dropped",
                            file=sys.stderr,
                        )
                        continue
                    if r.verdict != "faithful":
                        stats.reject(f"prose_check_failed_{r.verdict}")
                        print(
                            f"  {band:<7} prose check could not run ({r.verdict}) "
                            f"— case KEPT, warrant says unchecked",
                            file=sys.stderr,
                        )
                pair = emit_pair(case, th, roundtrip=rt)
                pp, kk = pair.write(a.split)
                print(f"  {band:<7} -> {pp.name} + {kk.name}", file=sys.stderr)
            if a.query_dir:
                query_sources.append(
                    {"murdoku_case": case.to_json(), "murdoku_theme": (th).to_json()}
                )
            if rendered < a.render:
                print(render_case(case, th))
                print(
                    f"[answer: {case.answer_key}]  band={band}  "
                    f"clues={len(case.clues)}  atoms={len(case.atoms)}\n" + "-" * 78
                )
                rendered += 1
            print(
                f"  {band:<7} #{made:<3} id={case.content_hash()} clues={len(case.clues):>2} "
                f"atoms={len(case.atoms):>2} adv={case.certificate['advanced']:>2} "
                f"depth={case.certificate['depth']:>2}",
                file=sys.stderr,
            )

    out = (
        Path(a.out)
        if a.out
        else ROOT / "data" / "cases" / f"{a.variant}_n{a.size}.jsonl"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records))
    meta = out.with_suffix(".setter_stats.json")
    meta.write_text(json.dumps(stats.to_json(), indent=2) + "\n")
    print(f"\nemitted {len(records)} case(s) -> {out}")
    print(f"setter stats -> {meta}: {json.dumps(stats.to_json())}")
    if a.query_dir:
        from murdoku_lab.setter.export_queries import write_bundle

        exported = write_bundle(query_sources, a.query_dir, views=query_views)
        print(
            f"paired query bundle -> {a.query_dir}: {exported['accepted_cases']} cases"
        )
        if not exported["accepted_cases"]:
            return 1
    return 0 if records else 1


if __name__ == "__main__":
    raise SystemExit(main())
