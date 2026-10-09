"""Round-trip verification: prove the natural language means what the mathematics says.

The setter builds a case from atoms and renders it to English. That rendering is templates and hope —
nothing checks that the sentence a player reads constrains the same placements the atom does. An
ambiguous template does not fail loudly; it produces a puzzle whose prose admits a solution the maths
forbids, which is indistinguishable from a hard puzzle until someone gets it "wrong".

So close the loop. We already have both halves:

    atoms --render_clue--> English --a model reads it--> atoms' --compare--> atoms

Comparison is by MEANING, not by spelling, because a paraphrase may legitimately produce different
atoms with the same content:

  * `--mode atom` (default): per predicate. Render one atom, have it read back, and compare the two
    atoms *semantically* — identical candidate masks for a unary predicate, identical truth over
    sampled placements for a pair or global one. This validates the 45 templates directly and says
    which sentence is ambiguous, which is what you can act on.
  * `--mode case`: whole puzzles. Render a generated case, have the prose alone translated back, and
    require the recovered clue set to admit EXACTLY the original solution. This is the end-to-end
    property: the emitted English determines the same puzzle as the maths.

The model never sees the atoms, only the prose — otherwise the check is vacuous.

Deliberately NOT a gate condition by default: the setter must keep working with no API key, and
a network dependency inside `gate()` would break every offline run. Use `--gate` to enforce it for a
corpus you are about to publish, and read the per-template rate the rest of the time.

Usage:
  python3 -m murdoku_lab.evaluation.roundtrip --mode atom [--kinds beside,compass] [--per-kind 2] [--model kimi-k3]
  python3 -m murdoku_lab.evaluation.roundtrip --mode case --n 6 --band medium --size 6
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from pathlib import Path

from murdoku_lab.paths import PROJECT_ROOT

ROOT = PROJECT_ROOT

from murdoku_lab.core.atoms import SPECS, Atom, holds_atom, unary_mask  # noqa: E402
from murdoku_lab.core.board import Scene  # noqa: E402
from murdoku_lab.core.instance import Case, Clue, VARIANTS  # noqa: E402
from murdoku_lab.core.theme import Theme, canonical_theme  # noqa: E402
from murdoku_lab.core.render import render_atom, render_case  # noqa: E402
from murdoku_lab.setter.llm_client import LLMClient  # noqa: E402
from murdoku_lab.solver.exact import count_solutions, enumerate_cp  # noqa: E402

# ---------------------------------------------------------------------------------------- prompts
ATOM_SYSTEM = (
    "You convert a single sentence from a logic puzzle into one formal predicate. You are given the "
    "exact catalogue of predicates and the board's facts. Reply with a single JSON object and "
    "nothing else. If the sentence is ambiguous — if it could mean two different predicates — say so "
    "rather than guessing, because an ambiguous sentence is a bug in the puzzle."
)

ATOM_PROMPT = """BOARD
  grid   : {W} columns x {H} rows. Columns are 1..{W} left to right, rows 1..{H} top to bottom.
  areas  : {n_areas}. id -> name: {area_names}
  props  : {objects}
  terrain: {terrains}
  people : {cast}
  tags   : {tags}

PREDICATE CATALOGUE — use exactly one of these
{catalogue}

CONVENTIONS
  area/areas 0-based ids · row/col 0-based · d a signed offset · dr,dc each -1/0/+1
  par "even"/"odd" · side north/south/east/west · axis "row"/"column"
  "beside" means 4-adjacent AND in the same area.

SENTENCE (about {holder})
  {sentence}

Reply with exactly:
{{"kind": "<predicate>", "args": [...], "ambiguous": false, "note": ""}}
"""


@dataclass
class AtomResult:
    kind: str
    args: list
    sentence: str = ""
    got_kind: str | None = None
    got_args: list = field(default_factory=list)
    verdict: str = "?"  # equivalent | different | ambiguous | unparsed | error
    detail: str = ""


@dataclass
class CaseResult:
    case_id: str
    band: str | None = None
    size: str = ""
    n_clues: int = 0
    verdict: str = "?"  # faithful | weaker | stronger | different | unparsed | error
    n_solutions: int | None = None
    detail: str = ""
    unsupported: list = field(default_factory=list)
    wall_s: float = 0.0


def catalogue_text(kinds: list[str] | None = None) -> str:
    out = []
    for arity in ("unary", "pair", "global"):
        rows = [
            (k, sp)
            for k, sp in sorted(SPECS.items())
            if sp.arity == arity and (kinds is None or k in kinds)
        ]
        if not rows:
            continue
        out.append(f"\n{arity.upper()}:")
        for k, sp in rows:
            out.append(f"  {k}({', '.join(sp.params) or '-'})")
    return "\n".join(out)


# ------------------------------------------------------------------------------- atom equivalence
def atoms_equivalent(
    a: Atom,
    b: Atom,
    scene: Scene,
    cast: list[str],
    tags: dict,
    rng: random.Random,
    samples: int = 300,
) -> tuple[bool, str]:
    """Do two atoms mean the same thing? Compared by behaviour, never by spelling.

    A unary predicate is fully described by the cells it permits, so mask equality is exact. Anything
    else is compared by truth over sampled complete placements — not a proof, but a difference in
    meaning almost always shows up within a few hundred samples, and a false 'equivalent' here is
    caught downstream by the case-level check.
    """
    sa, sb = SPECS.get(a.kind), SPECS.get(b.kind)
    if sb is None:
        return False, f"unknown predicate {b.kind!r}"
    if sa.arity == "unary" and sb.arity == "unary":
        ma, mb = unary_mask(a, scene), unary_mask(b, scene)
        if ma == mb:
            return True, "identical candidate masks"
        only_a, only_b = len(ma - mb), len(mb - ma)
        return (
            False,
            f"masks differ: {only_a} cell(s) only in ours, {only_b} only in theirs",
        )
    if sa.arity != sb.arity:
        return False, f"arity {sa.arity} vs {sb.arity}"

    cells = sorted(scene.open_cells)
    if len(cells) < len(cast):
        return False, "board cannot seat the cast"
    diff = 0
    for _ in range(samples):
        pl = dict(zip(cast, rng.sample(cells, len(cast))))
        try:
            if holds_atom(a, scene, pl, tags) != holds_atom(b, scene, pl, tags):
                diff += 1
        except Exception:  # noqa: BLE001
            return False, "evaluation failed"
    return (diff == 0), (
        "agree on all samples"
        if diff == 0
        else f"disagree on {diff}/{samples} placements"
    )


def sample_atoms(
    scene: Scene,
    cast: list[str],
    tags: dict,
    kinds: list[str],
    per_kind: int,
    rng: random.Random,
) -> list[Atom]:
    """One or more concrete, satisfiable atoms per kind, drawn from the board's own contents."""
    objs = sorted({o for o in scene.obj_of if o})
    ters = sorted(set(scene.terrain_of))
    tag_names = sorted({t for ts in tags.values() for t in ts})
    out: list[Atom] = []
    for kind in kinds:
        sp = SPECS[kind]
        for _ in range(per_kind):
            args = []
            ok = True
            for p in sp.params:
                if p == "area":
                    args.append(rng.randrange(scene.n_areas))
                elif p == "areas":
                    n = min(scene.n_areas, rng.randint(2, 3))
                    args.append(tuple(sorted(rng.sample(range(scene.n_areas), n))))
                elif p == "obj":
                    if not objs:
                        ok = False
                        break
                    args.append(rng.choice(objs))
                elif p == "ter":
                    args.append(rng.choice(ters))
                elif p == "other":
                    args.append(rng.choice(cast[1:]))
                elif p == "row":
                    args.append(rng.randrange(scene.H))
                elif p == "col":
                    args.append(rng.randrange(scene.W))
                elif p == "d":
                    args.append(rng.choice([-2, -1, 1, 2]))
                elif p in ("dr", "dc"):
                    args.append(rng.choice([-1, 0, 1]))
                elif p == "par":
                    args.append(rng.choice(["even", "odd"]))
                elif p == "side":
                    args.append(rng.choice(["north", "south", "east", "west"]))
                elif p == "axis":
                    args.append(rng.choice(["row", "column"]))
                elif p == "tag":
                    if not tag_names:
                        ok = False
                        break
                    args.append(rng.choice(tag_names))
                else:
                    ok = False
                    break
            if not ok:
                continue
            at = Atom(kind, cast[0], tuple(args))
            # Only keep atoms that SOMETHING on this board can satisfy. "A was the only person on a
            # shelf" is unsatisfiable — a shelf blocks the square — and asking a model to translate a
            # sentence that cannot be true tests nothing but its patience.
            m = unary_mask(at, scene) if SPECS[kind].arity == "unary" else None
            if m is not None and not m:
                continue
            out.append(at)
    return out


def check_atom(
    atom: Atom, case: Case, theme: Theme, model: str, rng_seed: int
) -> AtomResult:
    s = case.scene
    res = AtomResult(
        kind=atom.kind, args=[list(a) if isinstance(a, tuple) else a for a in atom.args]
    )
    try:
        res.sentence = render_atom(atom, case, theme)
    except Exception as e:  # noqa: BLE001
        res.verdict, res.detail = "error", f"render failed: {e}"
        return res

    tags = {t for ts in case.tags.values() for t in ts}
    prompt = ATOM_PROMPT.format(
        W=s.W,
        H=s.H,
        n_areas=s.n_areas,
        area_names="; ".join(f"{i}={theme.area(i)!r}" for i in range(s.n_areas)),
        objects=", ".join(sorted({theme.obj(o) for o in s.obj_of if o})) or "(none)",
        terrains=", ".join(sorted({theme.obj(t) for t in set(s.terrain_of)})),
        cast=", ".join(theme.name(x) for x in case.characters),
        tags=", ".join(sorted(tags)) or "(none)",
        catalogue=catalogue_text(),
        holder=theme.name(atom.holder),
        sentence=res.sentence,
    )
    data = None
    last = ""
    for _ in range(
        2
    ):  # one retry: a reply with no JSON is usually a one-off, not a refusal
        try:
            reply = LLMClient(model=model).chat(
                [
                    {"role": "system", "content": ATOM_SYSTEM},
                    {"role": "user", "content": prompt + last},
                ],
                max_tokens=1024,
            )
            data = _extract_json(reply)
            break
        except Exception as e:  # noqa: BLE001
            res.verdict, res.detail = "error", f"{type(e).__name__}: {e}"
            last = "\n\nReturn a single JSON object and nothing else."
    if data is None:
        return res

    if data.get("ambiguous"):
        res.verdict = "ambiguous"
        res.detail = str(data.get("note", ""))[:200]
        return res
    res.got_kind = data.get("kind")
    res.got_args = list(data.get("args") or [])
    if res.got_kind not in SPECS:
        res.verdict, res.detail = "unparsed", f"unknown predicate {res.got_kind!r}"
        return res
    try:
        back = Atom(
            res.got_kind,
            atom.holder,
            tuple(tuple(x) if isinstance(x, list) else x for x in res.got_args),
        )
        # a name may come back where a symbol is wanted
        sp = SPECS[res.got_kind]
        if "other" in sp.params:
            i = sp.params.index("other")
            want = back.args[i]
            sym = next(
                (
                    x
                    for x in case.characters
                    if want in (x, theme.name(x), theme.name(x).split()[0])
                ),
                want,
            )
            args = list(back.args)
            args[i] = sym
            back = Atom(back.kind, back.holder, tuple(args))
        same, why = atoms_equivalent(
            atom, back, s, list(case.characters), case.tags, random.Random(rng_seed)
        )
        res.verdict = "equivalent" if same else "different"
        res.detail = why
    except Exception as e:  # noqa: BLE001
        res.verdict, res.detail = "unparsed", f"{type(e).__name__}: {e}"
    return res


def _extract_json(text: str) -> dict:
    start = text.find("{")
    if start < 0:
        raise ValueError("no JSON in reply")
    depth, in_str, esc = 0, False, False
    for i, ch in enumerate(text[start:], start):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start : i + 1])
    raise ValueError("unbalanced JSON")


# ------------------------------------------------------------------------- case-level round trip
CASE_SYSTEM = (
    "You read a logic puzzle written in plain English and recover the formal constraints it states. "
    "You are given the exact predicate catalogue. Reply with a single JSON object and nothing else. "
    "Recover every clue: a clue you omit makes the puzzle admit placements it should forbid."
)

CASE_PROMPT = """Below is a puzzle exactly as a player reads it. Recover the constraints.

PREDICATE CATALOGUE — use only these
{catalogue}

CONVENTIONS
  area/areas are 0-based ids in the order the AREAS list below gives them (first listed = 0).
  row/col 0-based · d a signed offset · dr,dc each -1/0/+1 · par "even"/"odd"
  side north/south/east/west · axis "row"/"column"
  "beside" means 4-adjacent AND in the same area.
  The victim's card states the goal, not a constraint — give the victim an empty list.
  A statement about the whole board is a global atom; give it any person as holder.

=== THE PUZZLE ===
{puzzle}
=== END ===

Reply with exactly:
{{"atoms": {{"<person>": [["<kind>", [<args>]], ...]}}, "unsupported": [{{"clue": "...", "needs": "..."}}]}}
"""


def check_case(
    case: Case, theme: Theme, model: str, attempts: int, time_limit_s: float
) -> CaseResult:
    """Render the case, translate the prose back, and require the SAME solution set.

    Not 'the same atoms': a paraphrase may legitimately recover a different but equivalent set. What
    must hold is that the recovered clues admit exactly the one placement the answer key names. If
    they admit more, the prose lost information; if fewer, it says more than the maths does.
    """
    t0 = time.time()
    res = CaseResult(
        case_id=case.content_hash(),
        band=case.target_band,
        size=f"{case.scene.W}x{case.scene.H}",
        n_clues=len(case.clues),
    )
    prose = render_case(case, theme)
    name_to_sym = {theme.name(x): x for x in case.characters}
    prompt = CASE_PROMPT.format(catalogue=catalogue_text(), puzzle=prose)

    feedback = ""
    for _ in range(attempts):
        try:
            reply = LLMClient(model=model).chat(
                [
                    {"role": "system", "content": CASE_SYSTEM},
                    {"role": "user", "content": prompt + feedback},
                ],
                max_tokens=8192,
            )
            data = _extract_json(reply)
        except Exception as e:  # noqa: BLE001
            res.verdict, res.detail = "error", f"{type(e).__name__}: {e}"
            feedback = "\n\nYour previous reply was not valid JSON. Return JSON only."
            continue

        res.unsupported = data.get("unsupported") or []
        clues = []
        for who, atoms in (data.get("atoms") or {}).items():
            sym = name_to_sym.get(who, who if who in case.characters else None)
            if sym is None:
                continue
            built = []
            for entry in atoms or []:
                if not (isinstance(entry, (list, tuple)) and len(entry) == 2):
                    continue
                kind, args = entry[0], list(entry[1])
                if kind not in SPECS or len(args) != len(SPECS[kind].params):
                    continue
                sp = SPECS[kind]
                if "other" in sp.params:
                    i = sp.params.index("other")
                    args[i] = name_to_sym.get(args[i], args[i])
                    if args[i] not in case.characters:
                        continue
                built.append(
                    Atom(
                        kind,
                        sym,
                        tuple(tuple(x) if isinstance(x, list) else x for x in args),
                    )
                )
            if built:
                clues.append(Clue(tuple(built)))
        if not clues:
            res.verdict, res.detail = "unparsed", "no usable atoms recovered"
            feedback = "\n\nNo usable atoms were recovered. Return JSON only, using the catalogue."
            continue

        from dataclasses import replace

        recovered = replace(case, clues=tuple(clues), certificate=None)
        try:
            cnt = count_solutions(recovered, cap=3, time_limit_s=time_limit_s)
        except Exception as e:  # noqa: BLE001
            res.verdict, res.detail = "error", f"solve: {e}"
            break
        res.n_solutions = cnt.count
        if cnt.count == 0:
            res.verdict = "stronger"
            res.detail = (
                "the prose forbids the answer key — a sentence says more than its atom"
            )
            feedback = (
                "\n\nThe constraints you returned admit NO placement, so at least one is "
                "stricter than the sentence warrants. Re-read and return corrected JSON."
            )
            continue
        if cnt.count > 1:
            res.verdict = "weaker"
            res.detail = (
                f"{cnt.count}+ placements: the prose does not pin the puzzle down"
            )
            feedback = (
                f"\n\nThe constraints you returned admit {cnt.count}+ placements, so a clue "
                f"was missed or weakened. Re-read every sentence and return corrected JSON."
            )
            continue
        sols = enumerate_cp(recovered, cap=2, time_limit_s=time_limit_s)
        got = sols.solutions[0] if getattr(sols, "solutions", None) else None
        if got is None:
            from murdoku_lab.solver.exact import unique_solution

            got = unique_solution(recovered, time_limit_s=time_limit_s)
        if got == dict(case.solution):
            res.verdict = "faithful"
            res.detail = "the prose admits exactly the answer key"
            break
        res.verdict = "different"
        res.detail = "unique, but a different placement than the answer key"
        break

    res.wall_s = round(time.time() - t0, 1)
    return res


# ------------------------------------------------------------------------------------------- CLI
def _demo_case(size: int, band: str, seed: int, variant: str):
    from murdoku_lab.setter.pipeline import make_case

    a = make_case(variant=variant, size=size, band=band, seed=seed, attempts=25)
    return a.case


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--mode", choices=["atom", "case", "ambiguity"], default="atom")
    ap.add_argument("--model", default="kimi-k3")
    ap.add_argument(
        "--kinds", default=None, help="comma-separated predicate kinds (default: all)"
    )
    ap.add_argument("--per-kind", type=int, default=1)
    ap.add_argument("--variant", default="course")
    ap.add_argument("--size", type=int, default=12)
    ap.add_argument("--band", default="medium")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--n", type=int, default=4, help="case mode: how many cases")
    ap.add_argument("--attempts", type=int, default=2)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--time-limit", type=float, default=60.0)
    ap.add_argument("--theme", default="canonical")
    ap.add_argument("--out", default=None)
    ap.add_argument(
        "--gate",
        action="store_true",
        help="exit non-zero unless every check passes (for a corpus about to ship)",
    )
    a = ap.parse_args(argv)
    rng = random.Random(a.seed)

    if a.mode == "atom":
        # One board carrying as much variety as possible, so every predicate has something to bite on.
        from murdoku_lab.setter.sampler import gen_scene

        v = VARIANTS[a.variant]
        scene = gen_scene(
            a.size,
            max(4, a.size // 2),
            random.Random(a.seed),
            objects=v.objects,
            **(
                dict(
                    terrain=("fairway", "rough", "sand", "water"),
                    terrain_rate=0.35,
                    blob_scale=3,
                )
                if a.size >= 10
                else {}
            ),
        )
        cast = list("ABCDEFGH"[: min(8, scene.max_characters())])
        tags = {x: frozenset({("man", "woman")[i % 2]}) for i, x in enumerate(cast)}
        kinds = (
            [k for k in a.kinds.split(",") if k]
            if a.kinds
            else sorted(k for k in SPECS if k in v.allowed_kinds)
        )
        atoms = sample_atoms(scene, cast, tags, kinds, a.per_kind, rng)
        shell = Case(
            scene=scene,
            characters=tuple(cast),
            victim=cast[-1],
            clues=(),
            solution={},
            variant=a.variant,
            tags=tags,
        )
        theme = (
            canonical_theme(shell) if a.theme == "canonical" else Theme.load(a.theme)
        )
        print(
            f"checking {len(atoms)} atom(s) over {len(set(x.kind for x in atoms))} predicate(s) "
            f"on a {scene.W}x{scene.H} board with {a.model}\n",
            flush=True,
        )

        results: list[AtomResult] = []
        with ThreadPoolExecutor(max_workers=a.workers) as ex:
            futs = {
                ex.submit(check_atom, at, shell, theme, a.model, a.seed + i): at
                for i, at in enumerate(atoms)
            }
            for fut in as_completed(futs):
                r = fut.result()
                results.append(r)
                flag = {
                    "equivalent": "OK  ",
                    "different": "DIFF",
                    "ambiguous": "AMBIG",
                    "unparsed": "PARSE",
                    "error": "ERR ",
                }.get(r.verdict, "?")
                print(f"  {flag:5} {r.kind:22} {r.sentence[:64]}")
                if r.verdict != "equivalent":
                    print(f"        got {r.got_kind}{r.got_args}  — {r.detail[:90]}")

        print("\n=== per-predicate faithfulness ===")
        tally = Counter(r.verdict for r in results)
        for v_, n in tally.most_common():
            print(f"  {v_:12} {n}")
        okn = tally["equivalent"]
        print(
            f"\nfaithful: {okn}/{len(results)}" f" ({okn / max(1, len(results)):.0%})"
        )
        bad = [r for r in results if r.verdict != "equivalent"]
        if bad:
            print("\ntemplates to fix, worst first:")
            for r in sorted(bad, key=lambda r: r.kind):
                print(f"  {r.kind:22} {r.verdict:10} {r.sentence[:56]}")
        if a.out:
            (ROOT / a.out).write_text(
                "".join(
                    json.dumps(asdict(r), ensure_ascii=False) + "\n" for r in results
                )
            )
            print(f"\nwrote {a.out}")
        return 1 if (a.gate and bad) else 0

    if a.mode == "ambiguity":
        from murdoku_lab.setter.pipeline import make_case

        att = make_case(
            variant=a.variant, size=a.size, band=a.band, seed=a.seed, attempts=25
        )
        if att.case is None:
            print(f"no case: {att.reason}")
            return 1
        case = att.case
        theme = canonical_theme(case) if a.theme == "canonical" else Theme.load(a.theme)
        atoms = [at for c in case.clues for at in c.atoms]
        print(
            f"probing {len(atoms)} rendered sentence(s) for a rival reading, {a.model}\n",
            flush=True,
        )
        rows = []
        with ThreadPoolExecutor(max_workers=a.workers) as ex:
            futs = {
                ex.submit(probe_ambiguity, at, case, theme, a.model, a.time_limit): at
                for at in atoms
            }
            for fut in as_completed(futs):
                r = fut.result()
                rows.append(r)
                mark = {
                    "unambiguous": "ok  ",
                    "harmless": "note",
                    "material": "BUG ",
                    "flagged_no_rival": "?   ",
                    "error": "err ",
                }.get(r["verdict"], "?")
                print(f"  {mark} {r['kind']:20} {r['sentence'][:62]}")
                if r["verdict"] in ("material", "harmless"):
                    print(
                        f"        {r['solutions_intended']} solution(s) intended vs "
                        f"{r['solutions_rival']} under the rival reading — {r['why'][:80]}"
                    )
        bad = [r for r in rows if r["verdict"] == "material"]
        print(
            f"\n=== {len(bad)} sentence(s) whose rival reading CHANGES the puzzle ==="
        )
        for r in bad:
            print(f"  {r['kind']:20} {r['sentence'][:70]}")
            print(f"      {r['why'][:150]}")
        if a.out:
            (ROOT / a.out).write_text(
                "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
            )
            print(f"\nwrote {a.out}")
        return 1 if (a.gate and bad) else 0

    # ---- case mode
    cases = []
    for i in range(a.n):
        c = _demo_case(a.size, a.band, a.seed + i * 101, a.variant)
        if c is not None:
            cases.append(c)
    print(f"round-tripping {len(cases)} case(s) with {a.model}\n", flush=True)
    results2: list[CaseResult] = []
    with ThreadPoolExecutor(max_workers=min(a.workers, max(1, len(cases)))) as ex:
        futs = {
            ex.submit(
                check_case,
                c,
                canonical_theme(c) if a.theme == "canonical" else Theme.load(a.theme),
                a.model,
                a.attempts,
                a.time_limit,
            ): c
            for c in cases
        }
        for fut in as_completed(futs):
            r = fut.result()
            results2.append(r)
            print(
                f"  {r.verdict:10} {r.case_id[:12]} {r.size} clues={r.n_clues} "
                f"sols={r.n_solutions} {r.wall_s}s  {r.detail[:60]}"
            )
    print("\n=== case-level round trip ===")
    t2 = Counter(r.verdict for r in results2)
    for v_, n in t2.most_common():
        print(f"  {v_:10} {n}")
    print(f"\nfaithful: {t2['faithful']}/{len(results2)}")
    if a.out:
        (ROOT / a.out).write_text(
            "".join(json.dumps(asdict(r), ensure_ascii=False) + "\n" for r in results2)
        )
        print(f"wrote {a.out}")
    return 1 if (a.gate and t2["faithful"] != len(results2)) else 0


# ---------------------------------------------------------------------------- ambiguity probing
AMBIG_SYSTEM = (
    "You are proof-reading a logic puzzle for AMBIGUITY. You are shown one sentence and the board it "
    "describes. Your job is to find a SECOND reading a careful solver could take — a different, "
    "defensible interpretation of the same words — not to decide which is intended. Reply with a "
    "single JSON object and nothing else."
)

AMBIG_PROMPT = """BOARD
  grid   : {W} columns x {H} rows. Columns 1..{W} left to right, rows 1..{H} top to bottom.
  areas  : {n_areas}. id -> name: {area_names}
  props  : {objects}
  people : {cast}

PREDICATE CATALOGUE — the formal constraints available
{catalogue}

CONVENTIONS
  area/areas 0-based ids · row/col 0-based · d a signed offset · dr,dc each -1/0/+1
  par "even"/"odd" · side north/south/east/west · axis "row"/"column"

SENTENCE (about {holder})
  {sentence}

The intended constraint is: {intended}

Could a careful solver reasonably read this sentence as stating something DIFFERENT — a stronger,
weaker, or simply other constraint? If so, express that other reading using the catalogue: as a LIST
of atoms, since a stronger reading often needs an extra conjunct.

Reply with exactly:
{{"ambiguous": true|false, "other_reading": [["<kind>", [<args>]], ...], "why": "..."}}
"""


def probe_ambiguity(
    atom: Atom, case: Case, theme: Theme, model: str, time_limit_s: float = 60.0
) -> dict:
    """Ask for a rival reading of one rendered sentence, then price the difference.

    The round-trip check cannot see this class of bug. It asks "which predicate is this sentence?",
    the model answers correctly because the catalogue offers exactly one candidate, and the check
    passes — while the *meaning* a solver attaches to that predicate differs. "X was exactly 3 rows
    below Y" reads in English as implying the same column; the atom constrains only the row
    difference; and on a real board the same-column reading admitted ZERO placements, so a solver
    reading it naturally would conclude the puzzle was broken.

    So instead of asking which predicate, ask for a rival reading and count solutions under it. A
    rival that changes the solution count is a sentence that has to be rewritten.
    """
    from dataclasses import replace

    s = case.scene
    sentence = render_atom(atom, case, theme)
    intended = (
        f"{atom.kind}({', '.join(map(repr, atom.args))})"
        if atom.args
        else f"{atom.kind}()"
    )
    prompt = AMBIG_PROMPT.format(
        W=s.W,
        H=s.H,
        n_areas=s.n_areas,
        area_names="; ".join(f"{i}={theme.area(i)!r}" for i in range(s.n_areas)),
        objects=", ".join(sorted({theme.obj(o) for o in s.obj_of if o})) or "(none)",
        cast=", ".join(theme.name(x) for x in case.characters),
        catalogue=catalogue_text(),
        holder=theme.name(atom.holder),
        sentence=sentence,
        intended=intended,
    )
    out = {
        "kind": atom.kind,
        "sentence": sentence,
        "verdict": "unambiguous",
        "why": "",
        "solutions_intended": None,
        "solutions_rival": None,
    }
    try:
        reply = LLMClient(model=model).chat(
            [
                {"role": "system", "content": AMBIG_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1024,
        )
        data = _extract_json(reply)
    except Exception as e:  # noqa: BLE001
        out["verdict"], out["why"] = "error", f"{type(e).__name__}: {e}"
        return out
    if not data.get("ambiguous"):
        return out
    out["why"] = str(data.get("why", ""))[:300]

    rival = []
    for entry in data.get("other_reading") or []:
        if not (isinstance(entry, (list, tuple)) and len(entry) == 2):
            continue
        kind, args = entry[0], list(entry[1])
        if kind not in SPECS or len(args) != len(SPECS[kind].params):
            continue
        sp = SPECS[kind]
        if "other" in sp.params:
            i = sp.params.index("other")
            args[i] = next(
                (
                    x
                    for x in case.characters
                    if args[i] in (x, theme.name(x), theme.name(x).split()[0])
                ),
                args[i],
            )
            if args[i] not in case.characters:
                continue
        rival.append(
            Atom(
                kind,
                atom.holder,
                tuple(tuple(x) if isinstance(x, list) else x for x in args),
            )
        )
    if not rival:
        out["verdict"] = "flagged_no_rival"
        return out

    # price it: swap the clue containing this atom for the rival reading and re-count
    others = tuple(c for c in case.clues if atom not in c.atoms)
    base = count_solutions(case, cap=3, time_limit_s=time_limit_s).count
    swapped = replace(case, clues=others + (Clue(tuple(rival)),), certificate=None)
    alt = count_solutions(swapped, cap=3, time_limit_s=time_limit_s).count
    out["solutions_intended"], out["solutions_rival"] = base, alt
    out["verdict"] = "material" if alt != base else "harmless"
    return out


if __name__ == "__main__":
    raise SystemExit(main())
