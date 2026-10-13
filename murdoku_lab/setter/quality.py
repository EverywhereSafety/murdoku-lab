"""Clue utility and optional deduction-flow checks for generated cases."""

import math


def normalize_rhythm_policy(value):
    """Validate explicit thresholds; no human-quality score is implied."""
    if value is None:
        return None
    if not isinstance(value, dict) or value.get("schema") != "murdoku.rhythm_policy/1":
        raise ValueError("expected murdoku.rhythm_policy/1")
    bounds = {
        "max_first_progress_step",
        "max_progress_gap",
        "max_initial_singleton_fraction",
        "min_verdict_determined_fraction",
        "max_probe_fraction",
    }
    if (
        set(value)
        - bounds
        - {
            "schema",
            "orders",
            "seeds",
            "excluded_kinds",
            "balance_clues",
            "simplify_area_options",
        }
    ):
        raise ValueError("unknown rhythm policy fields")
    for key in ("balance_clues", "simplify_area_options"):
        if key in value and type(value[key]) is not bool:
            raise ValueError(f"{key} must be boolean")
    for key in bounds & value.keys():
        number = value[key]
        if (
            isinstance(number, bool)
            or not isinstance(number, (int, float))
            or not math.isfinite(number)
            or number < 0
        ):
            raise ValueError(f"invalid rhythm threshold {key}")
        if "fraction" in key and number > 1:
            raise ValueError(f"fraction outside 0..1 for {key}")
    orders = value.get("orders", ["canonical", "characters", "clues"])
    seeds = value.get("seeds", [0, 1])
    if (
        not isinstance(orders, list)
        or not orders
        or any(
            order not in ("canonical", "characters", "clues", "techniques")
            for order in orders
        )
    ):
        raise ValueError("invalid deduction orders")
    if (
        not isinstance(seeds, list)
        or not seeds
        or any(type(seed) is not int for seed in seeds)
    ):
        raise ValueError("seeds must be a nonempty integer list")
    from murdoku_lab.core.atoms import SPECS

    excluded = value.get("excluded_kinds", [])
    if not isinstance(excluded, list) or any(
        not isinstance(kind, str) or kind not in SPECS for kind in excluded
    ):
        raise ValueError("excluded_kinds must list known clue kinds")
    return {
        **value,
        "orders": list(dict.fromkeys(orders)),
        "seeds": list(dict.fromkeys(seeds)),
        **({"excluded_kinds": list(dict.fromkeys(excluded))} if excluded else {}),
    }


def flow_profile(case):
    from murdoku_lab.solver.reasoning_profile import profile_case

    return profile_case(case, keep_trace=False, measure_opening=False)


def improves_flow(baseline, without_clue):
    """Preserve a clue when removing it measurably worsens canonical progress."""
    if baseline["solved"] and not without_clue["solved"]:
        return True
    return any(
        baseline[key] is not None
        and without_clue[key] is not None
        and baseline[key] < without_clue[key]
        for key in (
            "first_progress_step",
            "first_determination_step",
            "progress_gap_max",
            "determination_gap_max",
            "probe_attempts",
        )
    )


def check_rhythm(case, policy):
    """Check several deduction schedules without exposing profiles in queries."""
    from murdoku_lab.solver.reasoning_profile import profile_case

    policy = normalize_rhythm_policy(policy)
    if policy is None:
        return {"ok": True, "runs": []}
    runs = []
    for order in policy["orders"]:
        for seed in ([0] if order == "canonical" else policy["seeds"]):
            p = profile_case(
                case, order=order, seed=seed, keep_trace=False, measure_opening=False
            )
            checks = {
                "solved": p["solved"],
                "matches_solution": p["matches_solution"] is True,
                "retains_solution": p["retains_solution_at_every_step"] is True,
            }
            if policy.get("excluded_kinds"):
                checks["clue_vocabulary"] = not any(
                    a.kind in policy["excluded_kinds"] for a in case.atoms
                )
            metrics = {
                "max_first_progress_step": p["first_progress_step"],
                "max_progress_gap": p["progress_gap_max"],
                "max_initial_singleton_fraction": p["initial_singletons"]
                / len(case.characters),
                "min_verdict_determined_fraction": p[
                    "verdict_reveal_determined_fraction"
                ],
                "max_probe_fraction": p["probe_steps"] / max(1, p["steps"]),
            }
            for key, actual in metrics.items():
                if key in policy:
                    checks[key] = actual is not None and (
                        actual >= policy[key]
                        if key.startswith("min_")
                        else actual <= policy[key]
                    )
            runs.append(
                {"order": order, "seed": seed, "checks": checks, "metrics": metrics}
            )
    return {"ok": all(all(run["checks"].values()) for run in runs), "runs": runs}


def improves_rhythm(baseline, without_clue):
    """Recognize flow clues under any of the same configured schedules."""
    other = {(r["order"], r["seed"]): r for r in without_clue["runs"]}
    for run in baseline["runs"]:
        removed = other[(run["order"], run["seed"])]
        if all(run["checks"].values()) and not all(removed["checks"].values()):
            return True
        for key in (
            "max_first_progress_step",
            "max_progress_gap",
            "max_probe_fraction",
            "min_verdict_determined_fraction",
        ):
            a, b = run["metrics"][key], removed["metrics"][key]
            if (
                a is not None
                and b is not None
                and (a > b if key.startswith("min_") else a < b)
            ):
                return True
    return False


# Arity "global" describes how many placements a predicate reads. Most such
# predicates still have a named subject. Only these facts are subject-free.
SCENE_WIDE_KINDS = frozenset(
    {"area_empty", "no_empty_area", "exactly_one_on", "area_occupancy_parity"}
)


def gives_verdict(atom, victim, murderer_rule="classic"):
    """In classic play, naming anyone in the victim's area names the murderer.

    This is a spoiler in the problem statement, not a private-key access check.
    A relationship between two suspects, and open/victim-cell games, is allowed.
    """
    if murderer_rule != "classic" or victim not in (atom.holder, atom.other):
        return False
    return atom.kind in ("with", "alone_with") or (
        atom.kind == "area_no_offset" and atom.get("d") == 0
    )


def direct_verdict_clues(case):
    return [
        i
        for i, clue in enumerate(case.clues)
        if any(
            gives_verdict(a, case.victim, case.vdef.murderer_rule) for a in clue.atoms
        )
    ]


def implied_atom_refs(case):
    """Obvious semantic implications, with no solution or solver-dependent masks.

    Restrict this to established definitions. Generic empirical co-occurrence on
    a sampled placement is not an implication and must never justify a deletion.
    """
    stronger = {
        "against_wall": {"in_corner", "in_grid_corner", "on_grid_edge"},
        "on_grid_edge": {"in_grid_corner"},
        "in_corner": {"in_grid_corner"},
    }
    out = []
    for i, clue in enumerate(case.clues):
        for j, weak in enumerate(clue.atoms):
            if any(
                strong.holder == weak.holder
                and (
                    strong.kind in stronger.get(weak.kind, ())
                    or (
                        weak.kind == "beside_through_wall"
                        and strong.kind == "beside"
                        and strong.args == weak.args
                    )
                )
                for strong in case.atoms
            ):
                out.append((i, j))
    return out


def fold_area_options(case):
    """Combine explicit area alternatives and exclusions for the same person.

    Only intersect stated sets. No placement, hidden answer or deduction engine
    is consulted. Leave purely negative statements and contradictions untouched.
    """
    from dataclasses import replace
    from murdoku_lab.core.atoms import Atom
    from murdoku_lab.core.instance import Clue

    rewrites = {}
    for holder in case.characters:
        atoms = [a for a in case.atoms if a.holder == holder]
        positives = [a for a in atoms if a.kind in ("in_area", "in_areas")]
        negatives = [a for a in atoms if a.kind == "not_in_area"]
        if not positives or len(positives) + len(negatives) < 2:
            continue
        areas = set(range(case.scene.n_areas))
        for atom in positives:
            areas &= (
                {atom.get("area")} if atom.kind == "in_area" else set(atom.get("areas"))
            )
        areas -= {a.get("area") for a in negatives}
        if not areas:
            continue
        rewrites[holder] = (
            Atom("in_area", holder, (next(iter(areas)),))
            if len(areas) == 1
            else Atom("in_areas", holder, (tuple(sorted(areas)),))
        )
    clues, inserted = [], set()
    for clue in case.clues:
        atoms = []
        for atom in clue.atoms:
            if atom.holder in rewrites and atom.kind in (
                "in_area",
                "in_areas",
                "not_in_area",
            ):
                if atom.holder not in inserted:
                    atoms.append(rewrites[atom.holder])
                    inserted.add(atom.holder)
            else:
                atoms.append(atom)
        if atoms:
            clues.append(Clue(tuple(atoms)))
    return replace(case, clues=tuple(clues), certificate=None)


def prune_implied_atoms(case, certificate, *, simplify_options=False):
    """Remove implied subclauses while retaining band, placement and late reveal.

    Equivalence follows from the implications above. The final caller still runs
    the ordinary independent gate. Certificates are recomputed after each edit.
    """
    from dataclasses import replace
    from murdoku_lab.core.instance import Clue
    from murdoku_lab.solver.difficulty import classify, respects_caps, style_ok
    from murdoku_lab.solver.logic import certify

    wanted = classify(certificate)
    removed = 0
    if wanted is None:
        return case, certificate, removed
    if simplify_options:
        trial = fold_area_options(case)
        if trial.clues != case.clues:
            cert = certify(trial)
            late = case.vdef.victim_last_k
            if (
                cert.solved
                and cert.placed == dict(case.solution)
                and classify(cert) == wanted
                and (late <= 0 or case.victim in cert.place_order[-late:])
                and respects_caps(trial, wanted)
                and style_ok(trial.atoms, wanted, len(case.characters))
            ):
                removed += len(case.atoms) - len(trial.atoms)
                case, certificate = trial, cert
    while True:
        changed = False
        for i, j in implied_atom_refs(case):
            remaining = case.clues[i].atoms[:j] + case.clues[i].atoms[j + 1 :]
            clues = (
                case.clues[:i]
                + ((Clue(remaining),) if remaining else ())
                + case.clues[i + 1 :]
            )
            trial = replace(case, clues=clues, certificate=None)
            cert = certify(trial)
            late = case.vdef.victim_last_k
            if (
                cert.solved
                and cert.placed == dict(case.solution)
                and classify(cert) == wanted
                and (late <= 0 or case.victim in cert.place_order[-late:])
                and respects_caps(trial, wanted)
                and style_ok(trial.atoms, wanted, len(case.characters))
            ):
                case, certificate = trial, cert
                removed += 1
                changed = True
                break
        if not changed:
            return case, certificate, removed
