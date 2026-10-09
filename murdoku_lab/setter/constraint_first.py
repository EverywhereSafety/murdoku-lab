"""Constraint-first generation: choose the clues, let the placement emerge.

The existing setter is **placement-first**. It samples an arrangement, harvests every atom that
happens to be true of it, and carves that pool down. That is why its puzzles are long: measured on a
16x16 board, 98.2% of the harvested pool is *local* atoms ("X was two rows above Y", "X was not beside
a barrel") and `area_occupancy_parity` appeared **zero** times — a random arrangement essentially never
satisfies "every even-numbered area holds an even number of people", so the one clue that constrains
the whole board in a sentence is never available. Lacking it, the carve needs 65 atoms where the
reference game's hand-authored 16x16 says the same thing in 22.

Their curated puzzles are short because a person works the other way round: decide the constraints,
then find an arrangement satisfying them. This module does that mechanically.

    scene = gen_scene(...)                    # geometry only, no placement
    clues = []                                # start with nothing
    loop:
        n = count_solutions(scene, clues)      # the arrangement is whatever satisfies the clues
        n == 1  -> check guess-freedom, emit
        n == 0  -> the last clue over-constrained; drop it
        n >  1  -> add the clue that cuts the most solutions

No arrangement is ever chosen, so no clue is ever "harvested". Powerful global clues are available
from the first step because their truth is something we *impose*, not something we hope for.

The expensive operation is now one capped exact solve per accepted clue. Its returned placements are
reused as witnesses to rank a beam of candidates in memory; below the cap that survivor count is
exact, and while saturated it is a deterministic sample estimate. Independent complete attempts are
parallelised by `murdoku_lab.setter.farm`; `workers` remains in this API for compatibility but is not used here.
"""

from __future__ import annotations

import random
from dataclasses import replace
from dataclasses import dataclass, field
from typing import Sequence

from murdoku_lab.core.atoms import SPECS, Atom, holds_atom, unary_mask
from murdoku_lab.core.board import Scene
from murdoku_lab.core.instance import Case, Clue, MURDERER_RULES, VARIANTS, Variant
from murdoku_lab.solver.difficulty import band_index, classify, respects_caps, style_ok
from murdoku_lab.solver.exact import count_solutions, unique_solution
from murdoku_lab.solver.logic import Certificate, certify
from .quality import (
    SCENE_WIDE_KINDS,
    gives_verdict,
    direct_verdict_clues,
    implied_atom_refs,
    prune_implied_atoms,
)
from .scene_spec import (
    SceneSpecInfeasible,
    apply_spec,
    choose_area_count,
    normalize_spec,
    sampling_rates,
)

# Strong candidates for post-uniqueness logic repair. Initial search interleaves
# all kinds; it does not give this list unconditional priority.
DENSE_KINDS = (
    "area_occupancy_parity",
    "no_empty_area",
    "exactly_one_on",
    "only_on",
    "only_beside",
    "only_tag_on",
    "alone",
    "area_empty",
    "other_beside",
    "tag_in_area_on",
    "tag_in_area",
)


@dataclass
class CFResult:
    case: Case | None = None
    certificate: Certificate | None = None
    band: str | None = None
    reason: str = ""
    n_clues: int = 0
    n_atoms: int = 0
    solves: int = 0  # exact solves spent, the honest cost measure
    trace: list = field(default_factory=list)


def candidate_atoms(
    scene: Scene,
    chars: Sequence[str],
    v: Variant,
    tags: dict,
    rng: random.Random,
    *,
    per_kind: int = 3,
) -> list[Atom]:
    """Atoms that COULD be stated about this scene — not about any arrangement.

    This is the inversion. `derive_pool` needs a placement to test against; here an atom is a candidate
    purely because its arguments name things the board has.
    """
    objs = sorted({o for o in scene.prop_of if o})
    standable_objs = [o for o in objs if scene.prop_by_id[o].cells & scene.open_cells]
    ters = sorted(set(scene.terrain_of))
    tag_names = sorted({t for ts in tags.values() for t in ts})
    out: list[Atom] = []

    def add(kind: str, holder: str, args: tuple = ()) -> bool:
        if kind not in v.allowed_kinds:
            return False
        atom = Atom(kind, holder, args)
        if atom.spec.mask is not None:
            mask = unary_mask(atom, scene)
            if not mask or (atom.spec.arity == "unary" and mask == scene.open_cells):
                return False
        out.append(atom)
        return True

    for kind in sorted(v.allowed_kinds):
        sp = SPECS[kind]
        holders = list(chars[:1]) if kind in SCENE_WIDE_KINDS else list(chars)
        for holder in holders:
            made = 0
            for _ in range(per_kind * 4):
                if made >= per_kind:
                    break
                args, ok = [], True
                for p in sp.params:
                    if p == "area":
                        args.append(rng.randrange(scene.n_areas))
                    elif p == "areas":
                        n = min(scene.n_areas, rng.randint(2, 3))
                        args.append(tuple(sorted(rng.sample(range(scene.n_areas), n))))
                    elif p == "obj":
                        choices = (
                            standable_objs
                            if kind
                            in {
                                "on",
                                "not_on",
                                "only_on",
                                "on_in_areas",
                                "only_tag_on",
                                "tag_in_area_on",
                                "exactly_one_on",
                            }
                            else objs
                        )
                        if not choices:
                            ok = False
                            break
                        args.append(rng.choice(choices))
                    elif p == "ter":
                        args.append(rng.choice(ters))
                    elif p == "other":
                        o = rng.choice([c for c in chars if c != holder])
                        args.append(o)
                    elif p == "row":
                        args.append(rng.randrange(scene.H))
                    elif p == "col":
                        args.append(rng.randrange(scene.W))
                    elif p == "d":
                        args.append(rng.choice([-3, -2, -1, 1, 2, 3]))
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
                if ok and add(kind, holder, tuple(args)):
                    made += 1
    # de-duplicate, keeping order stable for a fixed seed
    seen, uniq = set(), []
    for a in out:
        key = (a.kind, a.holder, a.args)
        if key not in seen:
            seen.add(key)
            uniq.append(a)
    return uniq


def _interleave_candidates(atoms, rng):
    """Give each kind beam exposure; its number of subject/argument combinations
    must not set its prior probability. Candidate gains still choose the winner.
    """
    atoms = list(atoms)
    rng.shuffle(atoms)
    groups = {}
    for atom in atoms:
        groups.setdefault(atom.kind, []).append(atom)
    kinds = list(groups)
    rng.shuffle(kinds)
    return [
        groups[kind][i]
        for i in range(max(map(len, groups.values()), default=0))
        for kind in kinds
        if i < len(groups[kind])
    ]


def _shell(
    scene: Scene,
    chars: Sequence[str],
    victim: str,
    variant: str,
    tags: dict,
    atoms: Sequence[Atom],
) -> Case:
    return Case(
        scene=scene,
        characters=tuple(chars),
        victim=victim,
        clues=tuple(Clue((a,)) for a in atoms),
        solution={},
        variant=variant,
        tags=tags,
    )


def _certificate_gap(cert: Certificate) -> tuple[int, int, int]:
    """Lexicographic distance from a completed human-style deduction.

    Fewer unresolved characters dominates, then fewer excess candidates, then a deeper chain.  The
    final component is negative because more justified progress is better.  This is a search
    heuristic only; every accepted case is still re-certified from scratch.
    """
    return (
        len(cert.stuck),
        sum(max(0, len(v) - 1) for v in cert.stuck.values()),
        -cert.depth,
    )


def _touches_victim(atom: Atom, victim: str) -> bool:
    return atom.holder == victim or atom.other == victim


def _victim_late(cert: Certificate, victim: str, last_k: int) -> bool:
    if last_k <= 0:
        return True
    return victim in cert.place_order[-last_k:]


def _swap_symbols(case: Case, a: str, b: str) -> Case:
    """Return the same mathematical puzzle with two character labels exchanged."""
    rename = {a: b, b: a}
    clues = []
    for clue in case.clues:
        atoms = []
        for atom in clue.atoms:
            args = list(atom.args)
            if "other" in atom.spec.params:
                i = atom.spec.params.index("other")
                args[i] = rename.get(args[i], args[i])
            atoms.append(
                Atom(atom.kind, rename.get(atom.holder, atom.holder), tuple(args))
            )
        clues.append(Clue(tuple(atoms)))
    return replace(
        case,
        clues=tuple(clues),
        solution={rename.get(x, x): k for x, k in case.solution.items()},
        tags={rename.get(x, x): v for x, v in case.tags.items()},
        certificate=None,
    )


def _relabel_for_late_victim(
    case: Case,
    cert: Certificate,
    *,
    time_limit_s: float,
    avoid_verdict_hints: bool = False,
) -> tuple[Case, Certificate] | None:
    """Move the victim label to a late-deduced two-person area without changing the puzzle shape."""
    v = case.vdef
    if _victim_late(cert, case.victim, v.victim_last_k):
        return case, cert
    if v.murderer_rule != "classic" or v.victim_last_k <= 0:
        return None
    occupants: dict[int, list[str]] = {}
    for x, k in case.solution.items():
        occupants.setdefault(case.scene.area_of[k], []).append(x)
    for candidate in reversed(cert.place_order[-v.victim_last_k :]):
        if candidate == case.victim:
            continue
        if len(occupants[case.scene.area_of[case.solution[candidate]]]) != 2:
            continue
        trial = _swap_symbols(case, case.victim, candidate)
        if avoid_verdict_hints and direct_verdict_clues(trial):
            continue
        if unique_solution(trial, time_limit_s=time_limit_s) != dict(trial.solution):
            continue
        trial_cert = certify(trial)
        if (
            trial_cert.solved
            and trial_cert.placed == dict(trial.solution)
            and _victim_late(trial_cert, trial.victim, v.victim_last_k)
        ):
            return trial, trial_cert
    return None


def _prune_useless(
    case: Case, cert: Certificate, *, time_limit_s: float
) -> tuple[Case, Certificate]:
    """Drop clues that preserve uniqueness, band, human solvability and the reveal order."""
    wanted = classify(cert)
    changed = True
    while changed:
        changed = False
        for i in range(len(case.clues)):
            trial = replace(
                case, clues=case.clues[:i] + case.clues[i + 1 :], certificate=None
            )
            if unique_solution(trial, time_limit_s=time_limit_s) != dict(case.solution):
                continue
            trial_cert = certify(trial)
            if (
                not trial_cert.solved
                or trial_cert.placed != dict(case.solution)
                or classify(trial_cert) != wanted
            ):
                continue
            if not _victim_late(trial_cert, case.victim, case.vdef.victim_last_k):
                relabelled = _relabel_for_late_victim(
                    trial,
                    trial_cert,
                    time_limit_s=time_limit_s,
                    avoid_verdict_hints=True,
                )
                if relabelled is None or classify(relabelled[1]) != wanted:
                    continue
                trial, trial_cert = relabelled
            case, cert, changed = trial, trial_cert, True
            break
    return case, cert


def generate(
    *,
    variant: str = "course",
    size: int = 9,
    n_areas: int | None = None,
    band: str | None = None,
    seed: int = 0,
    workers: int = 8,
    beam: int = 24,
    max_clues: int = 40,
    cap: int = 200,
    attempts: int = 6,
    time_limit_s: float = 10.0,
    scene_spec: dict | None = None,
) -> CFResult:
    """Retry the search a few times before giving up.

    Placement-first could *relabel* the cast so the victim sat in a two-person area, making the
    murderer rule true by construction. Here the arrangement emerges from the clues, so there is
    nothing to relabel: whether the victim ends up alone with exactly one person is an outcome. When it
    does not, that is a rejection to retry with a different clue ordering, not a failure — the same
    shape as `no_two_person_area` in the placement-first setter.
    """
    spec = normalize_spec(scene_spec, size=size, n_areas=n_areas)
    best = CFResult(reason="attempts_exhausted")
    for k in range(attempts):
        r = _generate_once(
            variant=variant,
            size=size,
            n_areas=n_areas,
            band=band,
            seed=seed + k * 7919,
            workers=workers,
            beam=beam,
            max_clues=max_clues,
            cap=cap,
            time_limit_s=time_limit_s,
            scene_spec=spec,
        )
        r.solves += best.solves
        if r.case is not None and not r.reason:
            return r
        if best.case is None and r.case is not None:
            best = r
        else:
            best.solves = r.solves
            best.reason = best.reason if best.case is not None else r.reason
            best.trace = r.trace or best.trace
    return best


def _generate_once(
    *,
    variant: str,
    size: int,
    n_areas: int | None,
    band: str | None,
    seed: int,
    workers: int,
    beam: int,
    max_clues: int,
    cap: int,
    time_limit_s: float,
    scene_spec: dict | None = None,
) -> CFResult:
    """Build a case by choosing clues until exactly one arrangement survives.

    `beam` is how many candidates are compared per step.  A single capped exact solve supplies up to
    `cap` witness placements; candidate atoms are scored against those witnesses in memory.  When
    the base count is below `cap` this ranking is exact, and while saturated it is a deterministic
    sample estimate.  The previous implementation launched one CP-SAT solve per candidate, spending
    roughly `beam * clues` solves on a case and timing out most 16x16 attempts.
    """
    v = VARIANTS[variant]
    if size not in v.sizes:
        raise ValueError(f"variant {variant!r} offers {v.sizes}")
    rng = random.Random(seed)
    # With no requested band, two positional clues can produce an easy puzzle
    # that immediately fails its one-positional-clue gate. Be conservative in
    # the shared candidate pool instead of relaxing the final acceptance criteria.
    cap_band = band or "medium"
    from .sampler import gen_scene

    big = size >= 10
    areas = choose_area_count(size, rng, n_areas=n_areas, spec=scene_spec)
    scene = gen_scene(
        size,
        areas,
        rng,
        objects=v.objects,
        prop_mix=v.prop_mix,
        **sampling_rates(scene_spec),
        **(
            dict(
                terrain=("fairway", "rough", "sand", "water"),
                terrain_rate=0.40,
                blob_scale=max(3, size // 4),
            )
            if big
            else {}
        ),
    )
    try:
        scene = apply_spec(scene, scene_spec, rng, allowed_objects=v.objects)
    except SceneSpecInfeasible as error:
        return CFResult(reason=f"scene_spec_infeasible: {error}")
    from .sampler import CHAR_SYMBOLS, VICTIM_SYMBOL

    chars = list(CHAR_SYMBOLS[: size - 1]) + [VICTIM_SYMBOL]
    tags: dict[str, frozenset[str]] = {}
    if v.tags:
        sh = sorted(chars)
        rng.shuffle(sh)
        for i, x in enumerate(sh):
            tags[x] = frozenset({v.tags[i % len(v.tags)]})

    if scene.max_characters() < len(chars):
        return CFResult(reason="board cannot seat the cast")

    cands = candidate_atoms(scene, chars, v, tags, rng)
    cands = [a for a in cands if not gives_verdict(a, VICTIM_SYMBOL, v.murderer_rule)]
    cands = _interleave_candidates(cands, rng)
    if not cands:
        return CFResult(reason="no candidate atoms on this board")

    chosen: list[Atom] = []
    solves = 0
    trace: list = []
    base = None
    for _step in range(max_clues):
        if base is None:
            base = count_solutions(
                _shell(scene, chars, VICTIM_SYMBOL, variant, tags, chosen),
                cap=cap,
                time_limit_s=time_limit_s,
            )
            solves += 1
        if base.timed_out:
            return CFResult(reason="base count timed out", solves=solves, trace=trace)
        if base.count == 0:
            # Witness scoring always retains at least one concrete placement, so reaching zero is
            # an internal consistency failure rather than an ordinary search branch.
            return CFResult(
                reason="witness-preserving clue produced zero solutions",
                solves=solves,
                trace=trace,
            )
        if base.count == 1:
            break
        trace.append(
            {
                "clues": len(chosen),
                "solutions": base.count,
                "saturated": base.count >= cap,
            }
        )

        # Score candidate clues against placements the exact solver has ALREADY produced. Adding a
        # clue can only remove placements, never add one. Below the cap this is the exact survivor
        # count; at the cap it is a useful witness estimate instead of the old all-candidates-equal
        # value `cap`. Requiring one surviving witness guarantees consistency without another solve.
        batch = [a for a in cands if a not in chosen][:beam]
        if not batch:
            return CFResult(reason="ran out of candidates", solves=solves, trace=trace)
        viable = []
        for i, atom in enumerate(batch):
            if not respects_caps(
                _shell(scene, chars, VICTIM_SYMBOL, variant, tags, chosen + [atom]),
                cap_band,
            ):
                continue
            survivors = sum(
                1 for pl in base.solutions if holds_atom(atom, scene, pl, tags)
            )
            if 1 <= survivors < base.count:
                viable.append((_touches_victim(atom, VICTIM_SYMBOL), survivors, i))
        if not viable:
            cands = cands[beam:] + cands[:beam]
            continue
        viable.sort()
        chosen.append(batch[viable[0][2]])
        base = None
    else:
        return CFResult(
            reason=f"no unique case within {max_clues} candidate rounds",
            solves=solves,
            trace=trace,
        )

    # ---- the arrangement is whatever the clues determine
    case0 = _shell(scene, chars, VICTIM_SYMBOL, variant, tags, chosen)
    sol = unique_solution(case0, time_limit_s=time_limit_s * 3)
    solves += 1
    if sol is None:
        return CFResult(
            reason="unique solution did not resolve", solves=solves, trace=trace
        )
    if MURDERER_RULES[v.murderer_rule](scene, sol, VICTIM_SYMBOL) is None:
        return CFResult(
            reason="murderer ill-defined for the arrangement that emerged",
            solves=solves,
            trace=trace,
        )

    from .sampler import build_case

    case = build_case(
        scene,
        chars,
        VICTIM_SYMBOL,
        sol,
        chosen,
        variant,
        tags=tags,
        seed=seed,
        target_band=band,
    )
    cert = certify(case, include_probe=False)
    # Uniqueness and human solvability are different. Once exact search isolates one placement,
    # add only clues true of that placement and greedily choose one that advances the deterministic
    # deduction certificate. This is cheap compared with CP-SAT and turns "unique but opaque" into a
    # useful setter signal instead of throwing the whole 16x16 attempt away immediately.
    repair = [a for a in cands if a not in chosen and holds_atom(a, scene, sol, tags)]
    repair.sort(key=lambda a: (a.kind not in DENSE_KINDS, a.kind, a.holder, a.args))
    while not cert.solved and len(chosen) < max_clues and repair:
        before = _certificate_gap(cert)
        # First prefer a true unary clue that directly removes the most candidates from one of the
        # stuck characters. This score is exact, essentially free, and avoids running the complete
        # deduction engine once per candidate on a 256-cell board.
        direct = []
        for i, atom in enumerate(repair):
            if not respects_caps(
                _shell(scene, chars, VICTIM_SYMBOL, variant, tags, chosen + [atom]),
                cap_band,
            ):
                continue
            mask = (
                unary_mask(atom, scene) if SPECS[atom.kind].mask is not None else None
            )
            live = set(cert.stuck.get(atom.holder, ()))
            if mask is None or not live:
                continue
            gain = len(live - set(mask))
            if gain:
                direct.append(
                    (
                        _touches_victim(atom, VICTIM_SYMBOL),
                        -gain,
                        not SPECS[atom.kind].pinning,
                        i,
                        atom,
                    )
                )
        if direct:
            direct.sort(key=lambda x: (x[0], x[1], x[2], x[3]))
            _, _, _, i, atom = direct[0]
            repair.pop(i)
        else:
            # Relational/global clues have no unary mask. Sample only a small bounded batch and ask
            # the cheap ladder (probe excluded) whether one advances the certificate.
            batch, repair = repair[:8], repair[8:]
            ranked = []
            for i, atom in enumerate(batch):
                trial = build_case(
                    scene,
                    chars,
                    VICTIM_SYMBOL,
                    sol,
                    chosen + [atom],
                    variant,
                    tags=tags,
                    seed=seed,
                    target_band=band,
                )
                if not respects_caps(trial, cap_band):
                    continue
                trial_cert = certify(trial, include_probe=False)
                ranked.append((_certificate_gap(trial_cert), i, atom))
            if not ranked:
                continue
            ranked.sort(key=lambda x: (x[0], x[1]))
            after, _, atom = ranked[0]
            if after >= before:
                continue
        chosen.append(atom)
        case = build_case(
            scene,
            chars,
            VICTIM_SYMBOL,
            sol,
            chosen,
            variant,
            tags=tags,
            seed=seed,
            target_band=band,
        )
        cert = certify(case, include_probe=False)
        trace.append(
            {
                "logic_repair": atom.kind,
                "clues": len(chosen),
                "unresolved": len(cert.stuck),
                "candidate_excess": sum(
                    max(0, len(v) - 1) for v in cert.stuck.values()
                ),
            }
        )
    # The canonical certificate includes every published technique, including probe. It is run once
    # after the cheap repair search rather than once per candidate.
    cert = certify(case)
    if not cert.solved:
        return CFResult(
            reason="not solvable by pure logic",
            solves=solves,
            trace=trace,
            case=case,
            certificate=cert,
            n_clues=len(case.clues),
            n_atoms=len(case.atoms),
        )
    got = classify(cert)
    if band is not None and got != band:
        return CFResult(
            reason=f"band_miss_{got}",
            solves=solves,
            trace=trace,
            case=case,
            certificate=cert,
            band=got,
            n_clues=len(case.clues),
            n_atoms=len(case.atoms),
        )
    if not _victim_late(cert, VICTIM_SYMBOL, v.victim_last_k):
        relabelled = _relabel_for_late_victim(
            case, cert, time_limit_s=time_limit_s, avoid_verdict_hints=True
        )
        if relabelled is None:
            return CFResult(
                reason="victim_not_last",
                solves=solves,
                trace=trace,
                band=got,
                case=case,
                certificate=cert,
                n_clues=len(case.clues),
                n_atoms=len(case.atoms),
            )
        case, cert = relabelled
        got = classify(cert)
        if band is not None and got != band:
            return CFResult(
                reason=f"band_miss_{got}",
                solves=solves,
                trace=trace,
                case=case,
                certificate=cert,
                band=got,
                n_clues=len(case.clues),
                n_atoms=len(case.atoms),
            )
    if not respects_caps(case, got or "medium"):
        return CFResult(
            reason="caps_violated",
            solves=solves,
            trace=trace,
            band=got,
            case=case,
            certificate=cert,
            n_clues=len(case.clues),
            n_atoms=len(case.atoms),
        )
    case, cert, pruned = prune_implied_atoms(case, cert)
    if implied_atom_refs(case):
        return CFResult(
            reason="implied_subclause",
            solves=solves,
            trace=trace,
            band=got,
            case=case,
            certificate=cert,
            n_clues=len(case.clues),
            n_atoms=len(case.atoms),
        )
    case, cert = _prune_useless(case, cert, time_limit_s=time_limit_s)
    if cert.placed != dict(case.solution):
        return CFResult(
            reason="logic_solution_mismatch",
            solves=solves,
            trace=trace,
            band=got,
            case=case,
            certificate=cert,
            n_clues=len(case.clues),
            n_atoms=len(case.atoms),
        )
    if direct_verdict_clues(case):
        return CFResult(
            reason="direct_verdict_clue",
            solves=solves,
            trace=trace,
            band=got,
            case=case,
            certificate=cert,
            n_clues=len(case.clues),
            n_atoms=len(case.atoms),
        )
    if not style_ok(list(case.atoms), got or "medium", len(chars)):
        return CFResult(
            reason="style_floor",
            solves=solves,
            trace=trace,
            band=got,
            case=case,
            certificate=cert,
            n_clues=len(case.clues),
            n_atoms=len(case.atoms),
        )
    case = replace(
        case,
        certificate=cert.to_json(),
        meta={
            **case.meta,
            "quality_version": "scene-design-v1",
            "implied_atoms_removed": pruned,
            **({"scene_spec": scene_spec} if scene_spec is not None else {}),
        },
    )
    return CFResult(
        case=case,
        certificate=cert,
        band=got,
        reason="",
        n_clues=len(case.clues),
        n_atoms=len(case.atoms),
        solves=solves,
        trace=trace,
    )
