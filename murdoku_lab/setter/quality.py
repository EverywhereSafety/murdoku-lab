"""Cheap presentation-quality checks over formal clues, without reading an answer."""

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


def prune_implied_atoms(case, certificate):
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
