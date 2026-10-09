"""`make_case` — the closed-loop setter, and `gate` — the verification barrier.

The loop: sample scene+solution -> derive every true clue -> **carve** toward the target band,
refusing any drop that overshoots it, then **harden** by swapping strong clues for weak ones if the
result came out too easy. Carving raises difficulty monotonically, so refusing overshoot targets the
band from above. Every attempt is counted, so the hit rate is reported rather than hidden.

On large boards `carve` drops atoms in blocks before it drops singles: one exact solve per candidate
drop is fine for a 60-atom pool and hopeless for the ~1250 a 16x16 board produces.

A note on irredundancy, because it is easy to want the wrong thing here. An irredundant clue set is
the *hardest* case attainable for its solution, so every band below the hardest necessarily contains
a clue whose removal preserves uniqueness. The gate therefore checks that no clue is **useless**
(removable without changing either uniqueness or the difficulty band), not that none is redundant.

`gate` is the only door onto disk. A case that fails it is never emitted.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field, replace
from typing import Sequence

from murdoku_lab.core.atoms import SPECS, Atom
from murdoku_lab.core.instance import Case, MURDERER_RULES, VARIANTS
from murdoku_lab.solver.difficulty import (
    band_index,
    classify,
    respects_caps,
    structural_counts,
    style_ok,
)
from murdoku_lab.solver.exact import count_solutions, enumerate_dfs, unique_solution
from murdoku_lab.solver.logic import Certificate, certify
from .sampler import (
    CHAR_SYMBOLS,
    VICTIM_SYMBOL,
    assign_victim,
    bias_pool,
    build_case,
    carve,
    derive_pool,
    gen_scene,
    harden,
    sample_solution,
    well_posed,
)
from .scene_spec import (
    SceneSpecInfeasible,
    apply_spec,
    choose_area_count,
    normalize_spec,
    sampling_rates,
    spec_satisfied,
)


@dataclass
class Attempt:
    ok: bool
    reason: str = ""
    case: Case | None = None
    certificate: Certificate | None = None
    band: str | None = None


@dataclass
class SetterStats:
    requested: int = 0
    emitted: int = 0
    attempts: int = 0
    rejects: dict[str, int] = field(default_factory=dict)
    bands: dict[str, int] = field(default_factory=dict)

    def reject(self, why: str) -> None:
        self.rejects[why] = self.rejects.get(why, 0) + 1

    @property
    def hit_rate(self) -> float:
        return self.emitted / self.attempts if self.attempts else 0.0

    def to_json(self) -> dict:
        return {
            "requested": self.requested,
            "emitted": self.emitted,
            "attempts": self.attempts,
            "hit_rate": round(self.hit_rate, 4),
            "rejects": dict(sorted(self.rejects.items(), key=lambda kv: -kv[1])),
            "bands": dict(sorted(self.bands.items())),
        }


def _victim_ok(cert: Certificate, victim: str, last_k: int) -> bool:
    """The reveal must land at the end: the victim is among the final `last_k` deductions."""
    if last_k <= 0:
        return True
    order = cert.place_order
    return victim in order[-last_k:] if len(order) >= last_k else victim in order


def make_case(
    *,
    variant: str = "classic",
    size: int = 6,
    band: str = "medium",
    seed: int = 0,
    n_areas: int | None = None,
    attempts: int = 30,
    time_limit_s: float = 10.0,
    stats: SetterStats | None = None,
    scene_spec: dict | None = None,
) -> Attempt:
    """Produce one case in `band`, or report why not. Deterministic given `seed`."""
    v = VARIANTS[variant]
    if size not in v.sizes:
        raise ValueError(f"variant {variant!r} offers sizes {v.sizes}, got {size}")
    spec = normalize_spec(scene_spec, size=size, n_areas=n_areas)
    rng = random.Random(seed)
    st = stats if stats is not None else SetterStats()
    target = band_index(band)
    fallback: Attempt | None = None

    for _ in range(attempts):
        st.attempts += 1
        # Large boards get a terrain layer. Area count varies unless explicitly
        # requested, so full casts need not inherit a fixed number of empty rooms.
        big = size >= 10
        areas = choose_area_count(size, rng, n_areas=n_areas, spec=spec)
        scene = gen_scene(
            size,
            areas,
            rng,
            objects=v.objects,
            prop_mix=v.prop_mix,
            **sampling_rates(spec),
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
            scene = apply_spec(scene, spec, rng, allowed_objects=v.objects)
        except SceneSpecInfeasible:
            st.reject("scene_spec_infeasible")
            continue
        chars = list(CHAR_SYMBOLS[: size - 1]) + [VICTIM_SYMBOL]
        # Structural tags, split deterministically so a seed reproduces the cast exactly.
        tags: dict[str, frozenset[str]] = {}
        if v.tags:
            shuffled = sorted(chars)
            rng.shuffle(shuffled)
            for i, x in enumerate(shuffled):
                tags[x] = frozenset({v.tags[i % len(v.tags)]})
        # several solution draws per scene: scene generation is the expensive part, and whether a
        # two-person area exists depends on the draw, not the scene
        pl = None
        for _try in range(6):
            cand_pl = sample_solution(scene, chars, rng)
            if cand_pl is None:
                break
            if v.answer != "murderer":
                pl = cand_pl
                break
            relabelled = assign_victim(scene, cand_pl, chars, VICTIM_SYMBOL, rng)
            if (
                relabelled is not None
                and MURDERER_RULES[v.murderer_rule](scene, relabelled, VICTIM_SYMBOL)
                is not None
            ):
                pl = relabelled
                break
        if pl is None:
            st.reject("no_two_person_area")
            continue

        pool = derive_pool(scene, chars, VICTIM_SYMBOL, pl, v, rng, tags)
        from .quality import gives_verdict

        pool = [a for a in pool if not gives_verdict(a, VICTIM_SYMBOL, v.murderer_rule)]
        # Deliberately NOT capped. The pool grows as O(cast^2) through the pair predicates, but the
        # information needed for uniqueness is spread thin across it: a strength-ranked 720-atom cap
        # of a 1238-atom 16x16 pool still left four characters unresolved. `carve` handles the size
        # instead, by dropping blocks before it drops singles.
        pool = bias_pool(pool, band, chars, rng)

        def accept(ats: list[Atom], cert: Certificate) -> bool:
            """Veto a carve/swap move. Only the band is a per-move constraint: carving raises
            difficulty monotonically, so refusing overshoot targets the band from above. Style
            floors are *termination* requirements, checked once at acceptance — as a per-move veto
            they would deadlock (the raw pool breaches them before carving has done its work).
            """
            b = classify(cert)
            return b is not None and band_index(b) <= target

        res = carve(
            scene,
            chars,
            VICTIM_SYMBOL,
            pl,
            pool,
            variant,
            rng,
            accept=accept,
            tags=tags,
            time_limit_s=time_limit_s,
        )
        if res is None:
            st.reject("not_well_posed_even_with_full_pool")
            continue

        atoms, cert = list(res.atoms), res.certificate
        cur = classify(cert)
        if cur is None:
            st.reject("unclassifiable")
            continue

        # --- ascend: swap strong clues for weak ones until the band rises to target ------------
        if band_index(cur) < target:
            got = harden(
                scene,
                chars,
                VICTIM_SYMBOL,
                pl,
                atoms,
                pool,
                variant,
                rng,
                budget=40,
                target_index=target,
                band_of=lambda c: (
                    None if classify(c) is None else band_index(classify(c))
                ),
                accept=accept,
                tags=tags,
                time_limit_s=time_limit_s,
            )
            if got is not None:
                atoms, cert = got
                cur = classify(cert)

        if cur != band:
            st.reject(f"band_miss_{cur}")
            cand = build_case(
                scene,
                chars,
                VICTIM_SYMBOL,
                pl,
                atoms,
                variant,
                seed=seed,
                target_band=band,
                tags=tags,
                certificate=cert.to_json(),
            )
            if fallback is None:
                fallback = Attempt(False, f"band_miss_{cur}", cand, cert, cur)
            continue

        case = build_case(
            scene,
            chars,
            VICTIM_SYMBOL,
            pl,
            atoms,
            variant,
            seed=seed,
            target_band=band,
            tags=tags,
            certificate=cert.to_json(),
            meta={
                "carve_rounds": res.rounds,
                "carve_dropped": res.dropped,
                "pool_size": len(pool),
                **({"scene_spec": spec} if spec is not None else {}),
                "quality_version": "scene-design-v1",
            },
        )
        from .quality import implied_atom_refs, prune_implied_atoms

        case, cert, pruned = prune_implied_atoms(case, cert)
        if implied_atom_refs(case):
            st.reject("implied_subclause")
            continue
        case = replace(
            case,
            certificate=cert.to_json(),
            meta={**case.meta, "implied_atoms_removed": pruned},
        )
        atoms = list(case.atoms)
        if not respects_caps(case, band):
            st.reject("caps_violated")
            continue
        if not style_ok(atoms, band, len(chars)):
            st.reject("style_floor")
            continue
        if not _victim_ok(cert, VICTIM_SYMBOL, v.victim_last_k):
            st.reject("victim_not_last")
            continue

        st.emitted += 1
        st.bands[band] = st.bands.get(band, 0) + 1
        return Attempt(True, "", case, cert, band)

    return fallback or Attempt(False, "attempts_exhausted")


# =============================================================================================
# The gate — the only door onto disk (mirrors the sibling repo's generate -> verify -> emit idiom)
# =============================================================================================
@dataclass
class GateReport:
    ok: bool
    checks: dict[str, bool]
    detail: dict = field(default_factory=dict)

    @property
    def failed(self) -> list[str]:
        return [k for k, v in self.checks.items() if not v]


def gate(
    case: Case,
    *,
    expect_band: str | None = None,
    time_limit_s: float = 20.0,
    exact_count: bool = True,
    cross_check_dfs: bool | None = None,
) -> GateReport:
    """Independent re-verification. Trusts nothing the setter said."""
    checks: dict[str, bool] = {}
    detail: dict = {}

    from .quality import direct_verdict_clues, implied_atom_refs

    direct, implied = direct_verdict_clues(case), implied_atom_refs(case)
    checks["no_direct_verdict_clue"] = not direct
    checks["no_implied_subclause"] = not implied
    detail["direct_verdict_clues"], detail["implied_subclauses"] = direct, implied
    if "scene_spec" in case.meta:
        try:
            spec = normalize_spec(case.meta["scene_spec"], size=case.scene.W)
            checks["scene_spec_satisfied"] = spec is not None and spec_satisfied(
                case.scene, spec
            )
        except (TypeError, ValueError) as error:
            checks["scene_spec_satisfied"] = False
            detail["scene_spec_error"] = str(error)

    try:
        case.self_check()
        checks["self_check"] = True
    except Exception as e:  # noqa: BLE001
        checks["self_check"] = False
        detail["self_check_error"] = str(e)
        return GateReport(False, checks, detail)

    r = count_solutions(case, cap=None if exact_count else 2, time_limit_s=time_limit_s)
    checks["not_timed_out"] = not r.timed_out
    checks["unique_solution"] = r.count == 1
    checks["solution_matches"] = bool(r.solutions) and r.solutions[0] == dict(
        case.solution
    )
    detail["solution_count"] = r.count

    use_dfs = len(case.characters) <= 9 if cross_check_dfs is None else cross_check_dfs
    if use_dfs:
        rd = enumerate_dfs(case, cap=2)
        checks["independent_solver_agrees"] = rd.count == min(r.count, 2) and (
            rd.count != 1 or rd.solutions[0] == dict(case.solution)
        )
        detail["dfs_solution_count_capped_at_2"] = rd.count
    else:
        detail["dfs_cross_check"] = "skipped_by_size_or_caller"

    cert = certify(case)
    checks["logic_solvable"] = cert.solved
    checks["logic_agrees"] = cert.placed == dict(case.solution)
    band = classify(cert)
    detail["band"] = band
    detail["certificate"] = cert.to_json()
    detail["structural"] = structural_counts(case)

    if expect_band is not None:
        checks["band_as_requested"] = band == expect_band
        checks["caps_respected"] = respects_caps(case, expect_band)

    v = case.vdef
    checks["victim_reveal_last"] = _victim_ok(cert, case.victim, v.victim_last_k)
    if v.answer == "murderer":
        checks["murderer_defined"] = case.murderer is not None

    # ---- no useless clue -------------------------------------------------------------------
    # NOT plain irredundancy. An irredundant clue set is, by definition, the hardest case attainable
    # for its solution: every clue is load-bearing for uniqueness, so nothing can be removed. It
    # follows that any EASIER band must contain a clue whose removal preserves uniqueness. Demanding
    # both "irredundant" and "band == medium" is therefore unsatisfiable, and demanding it anyway is
    # what made carving keep a clue it had no reason to keep.
    #
    # The property we actually want is that no clue is *doing nothing*: removing it must either
    # break uniqueness, or change the difficulty. A clue that fails both tests is padding and the
    # case is rejected. A clue that only fails the first is what makes an easy case easy.
    from dataclasses import replace as _replace

    useless, redundant = [], []
    band_now = classify(cert)
    for i in range(len(case.clues)):
        trimmed = case.clues[:i] + case.clues[i + 1 :]
        c2 = _replace(case, clues=trimmed, certificate=None)
        if unique_solution(c2, time_limit_s=time_limit_s) != dict(case.solution):
            continue  # load-bearing for uniqueness
        redundant.append(i)
        if classify(certify(c2)) == band_now:
            useless.append(i)  # removable AND changes nothing about the difficulty
    checks["no_useless_clue"] = not useless
    detail["useless_clues"] = useless
    detail["redundant_clues"] = (
        redundant  # informational: expected on every non-hardest band
    )

    return GateReport(all(checks.values()), checks, detail)
