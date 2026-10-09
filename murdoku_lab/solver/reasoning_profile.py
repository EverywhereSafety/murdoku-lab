"""Observational deduction profiles; never used by generation admission.

The observer calls the production deduction engine. Candidate changes, not
Step.removed, determine information reduction. Neither scheduling nor verdict
support reads the hidden answer. The answer is used only afterwards as a check.
"""

from __future__ import annotations

import itertools
import random
import statistics
from dataclasses import replace

from murdoku_lab.core.atoms import SPECS, unary_mask
from .logic import Deducer


class ProfileDeducer(Deducer):
    """Observe unchanged rules, optionally varying one scheduling axis."""

    def __init__(self, case, *, order="canonical", seed=0):
        super().__init__(case)
        if order not in ("canonical", "clues", "characters", "techniques"):
            raise ValueError(f"unknown order mode: {order}")
        self.order, self.seed = order, seed
        self.snapshots = []
        self.probe_attempts = 0
        self.probe_contradictions = 0
        self._inside_technique = False
        self._state = None
        rng = random.Random(seed)
        if order == "characters":
            rng.shuffle(self.chars)
        elif order == "clues":
            clues = list(case.clues)
            rng.shuffle(clues)
            self.atoms = [atom for clue in clues for atom in clue.atoms]

    def _snapshot(self, state):
        self.snapshots.append(
            {
                "candidates": {x: sorted(c) for x, c in state.cand.items()},
                "registered": dict(state.placed),
                "probe_attempts": self.probe_attempts,
                "probe_contradictions": self.probe_contradictions,
            }
        )

    def initial(self):
        state, step = super().initial()
        self._state = state
        self._snapshot(state)
        return state, step

    def _place(self, state, character, cell):
        removed = super()._place(state, character, cell)
        # The engine promotes remaining singletons after the technique loop.
        # Probe's temporary assignments must never enter the observed trace.
        if not self._inside_technique and state is self._state:
            self._snapshot(state)
        return removed

    def _propagate_cheap(self, state, limit=200):
        self.probe_attempts += 1
        consistent = super()._propagate_cheap(state, limit=limit)
        self.probe_contradictions += not consistent
        return consistent

    def techniques(self, *, include_probe=True):
        ladder = super().techniques(include_probe=include_probe)
        if self.order == "techniques":
            rng = random.Random(self.seed)
            # Preserve tier boundaries, closing move and probe positions.
            # Only shuffle contiguous peers; single remains first.
            start = 0
            while start < len(ladder):
                name, tier, _ = ladder[start]
                if name in ("single", "last", "probe"):
                    start += 1
                    continue
                end = start + 1
                while (
                    end < len(ladder)
                    and ladder[end][1] == tier
                    and ladder[end][0] not in ("single", "last", "probe")
                ):
                    end += 1
                peers = ladder[start:end]
                rng.shuffle(peers)
                ladder[start:end] = peers
                start = end

        def observed(fn):
            def apply(state):
                self._inside_technique = True
                try:
                    step = fn(state)
                finally:
                    self._inside_technique = False
                if step is not None:
                    self._snapshot(state)
                return step

            return apply

        return [(name, tier, observed(fn)) for name, tier, fn in ladder]


def verdict_support(case, candidates):
    """Conservative classic-murderer support from current domains and game rules.

    A suspect needs a row/column-compatible pair of cells in one victim area,
    and every other character needs some candidate outside that area. Joint
    feasibility among other characters is not checked: this is a superset,
    not exact solution enumeration. One supported suspect is sufficient to
    deduce the verdict; several supported suspects do not prove ambiguity.
    """
    if case.vdef.murderer_rule != "classic":
        return None
    scene, victim = case.scene, case.victim
    areas = {x: {scene.area_of[k] for k in cells} for x, cells in candidates.items()}
    supported = []
    for suspect in case.characters:
        if suspect == victim:
            continue
        for area in areas[victim] & areas[suspect]:
            if any(
                not (areas[x] - {area})
                for x in case.characters
                if x not in (victim, suspect)
            ):
                continue
            victim_cells = [k for k in candidates[victim] if scene.area_of[k] == area]
            suspect_cells = [k for k in candidates[suspect] if scene.area_of[k] == area]
            if any(
                scene.row(v) != scene.row(s) and scene.col(v) != scene.col(s)
                for v in victim_cells
                for s in suspect_cells
            ):
                supported.append(suspect)
                break
    return sorted(supported)


def percentile(values, q):
    """Linear interpolation, including singleton samples."""
    if not values:
        return None
    values = sorted(values)
    position = (len(values) - 1) * q
    lo = int(position)
    hi = min(lo + 1, len(values) - 1)
    return values[lo] + (values[hi] - values[lo]) * (position - lo)


def opening_unary_witnesses(case, *, max_clues=3):
    """Smallest unary-clue subsets isolating an initial singleton, up to a cap.

    Counts presented clues, not atoms. This describes the collapsed setup only,
    not a minimal proof for a relational/advanced first placement.
    """
    open_cells = set(case.scene.open_cells)
    masks = {x: [] for x in case.characters}
    for index, clue in enumerate(case.clues):
        by_holder = {}
        for atom in clue.atoms:
            spec = SPECS[atom.kind]
            if spec.arity != "unary" and not (
                spec.arity == "global" and spec.mask is not None
            ):
                continue
            mask = unary_mask(atom, case.scene)
            if mask is not None:
                by_holder.setdefault(atom.holder, set(open_cells)).intersection_update(
                    mask
                )
        for holder, mask in by_holder.items():
            if mask != open_cells:
                masks[holder].append((index, mask))
    result = []
    for character, restrictions in masks.items():
        combined = set(open_cells)
        for _, mask in restrictions:
            combined &= mask
        if len(combined) != 1:
            continue
        witness = None
        for count in range(min(max_clues, len(restrictions)) + 1):
            for subset in itertools.combinations(restrictions, count):
                remaining = set(open_cells)
                for _, mask in subset:
                    remaining &= mask
                if len(remaining) == 1:
                    witness = [index + 1 for index, _ in subset]
                    break
            if witness is not None:
                break
        result.append(
            {
                "character": character,
                "minimum_clues": len(witness) if witness is not None else None,
                "witness_clue_ids": witness,
                "search_cap": max_clues,
                "exceeds_cap": witness is None,
            }
        )
    return result


def profile_case(
    case,
    *,
    order="canonical",
    seed=0,
    include_probe=True,
    keep_trace=True,
    measure_opening=True,
    max_steps=4000,
):
    engine = ProfileDeducer(case, order=order, seed=seed)
    certificate = engine.run(max_steps=max_steps, include_probe=include_probe)
    if len(engine.snapshots) != len(certificate.steps):
        raise RuntimeError("deduction snapshots and certificate steps disagree")
    total_open = len(case.scene.open_cells) * len(case.characters)
    raw_uncertainty = total_open - len(case.characters)
    initial_uncertainty = sum(
        len(c) - 1 for c in engine.snapshots[0]["candidates"].values()
    )
    trace, previous, previous_fixed = [], None, set()
    for index, (snapshot, step) in enumerate(zip(engine.snapshots, certificate.steps)):
        candidates = snapshot["candidates"]
        if previous is not None and any(
            not set(candidates[x]) <= set(previous[x]) for x in candidates
        ):
            raise RuntimeError("deduction increased a candidate domain")
        fixed = {x for x, cells in candidates.items() if len(cells) == 1}
        uncertainty = sum(max(0, len(c) - 1) for c in candidates.values())
        supported = verdict_support(case, candidates)
        trace.append(
            {
                "step": index,
                **step.to_json(),
                "candidate_count": sum(map(len, candidates.values())),
                "uncertainty": uncertainty,
                "uncertainty_fraction": (
                    uncertainty / initial_uncertainty if initial_uncertainty else 0.0
                ),
                "determined": len(fixed),
                "registered": len(snapshot["registered"]),
                "newly_determined": sorted(fixed - previous_fixed),
                "verdict_support": supported,
                "probe_attempts": snapshot["probe_attempts"],
                "probe_contradictions": snapshot["probe_contradictions"],
                "candidates": candidates,
            }
        )
        previous, previous_fixed = candidates, fixed
    placement_indices = [i for i, step in enumerate(certificate.steps) if step.placed]
    gaps = [b - a - 1 for a, b in zip(placement_indices, placement_indices[1:])]
    discovery_indices = [row["step"] for row in trace if row["newly_determined"]]
    discovery_gaps = [
        b - a - 1 for a, b in zip(discovery_indices, discovery_indices[1:])
    ]
    reveal = next(
        (
            row
            for row in trace
            if row["verdict_support"] is not None and len(row["verdict_support"]) == 1
        ),
        None,
    )
    consecutive, longest = 0, 0
    for step in certificate.steps[1:]:
        consecutive = consecutive + 1 if step.placed else 0
        longest = max(longest, consecutive)
    # Check the hidden solution only after solving; never a scheduling feature.
    retains_answer = (
        all(
            case.solution.get(x) in cells
            for row in trace
            for x, cells in row["candidates"].items()
        )
        if case.solution
        else None
    )
    return {
        "schema": "murdoku.reasoning_profile/1",
        "order": order,
        "seed": seed,
        "include_probe": include_probe,
        "solved": certificate.solved,
        "matches_solution": (
            certificate.placed == dict(case.solution) if case.solution else None
        ),
        "retains_solution_at_every_step": retains_answer,
        "steps": len(certificate.steps) - 1,
        "advanced_steps": certificate.advanced,
        "probe_steps": sum(step.kind == "probe" for step in certificate.steps),
        "probe_attempts": engine.probe_attempts,
        "probe_contradictions": engine.probe_contradictions,
        "probe_max_assumption_depth": int(engine.probe_attempts > 0),
        "initial_singletons": trace[0]["determined"],
        "setup_removed_candidates": total_open - trace[0]["candidate_count"],
        "setup_uncertainty_fraction_removed": (
            1 - initial_uncertainty / raw_uncertainty if raw_uncertainty else 0.0
        ),
        "first_placement_delay": (
            placement_indices[0] - 1 if placement_indices else None
        ),
        "first_determination_step": discovery_indices[0] if discovery_indices else None,
        "placement_gap_median": statistics.median(gaps) if gaps else None,
        "placement_gap_p90": percentile(gaps, 0.9),
        "placement_gap_max": max(gaps, default=0),
        "determination_gap_max": max(discovery_gaps, default=0),
        "longest_placement_run": longest,
        "max_newly_determined": max(
            (len(row["newly_determined"]) for row in trace[1:]), default=0
        ),
        "verdict_reveal_step": reveal["step"] if reveal else None,
        "verdict_reveal_determined_fraction": (
            reveal["determined"] / len(case.characters) if reveal else None
        ),
        "verdict_supported_character": reveal["verdict_support"][0] if reveal else None,
        "opening_unary_witnesses": (
            opening_unary_witnesses(case) if measure_opening else None
        ),
        "technique_counts": {
            kind: sum(step.kind == kind for step in certificate.steps)
            for kind in sorted({step.kind for step in certificate.steps})
        },
        "trace": trace if keep_trace else None,
    }


def clue_ablation(case, baseline=None, *, exact_time_limit_s=0.5):
    """Leave out each presented clue; distinguish lost uniqueness from lost flow.

    Logical changes are observed with probe enabled. Exact counting is used only
    to classify the ablated puzzle, and timeout never means proved unique.
    """
    from .exact import enumerate_cp

    baseline = baseline or profile_case(case, keep_trace=False, measure_opening=False)
    rows = []
    for index, clue in enumerate(case.clues):
        trial = replace(
            case, clues=case.clues[:index] + case.clues[index + 1 :], certificate=None
        )
        profile = profile_case(trial, keep_trace=False, measure_opening=False)
        count = enumerate_cp(trial, cap=2, time_limit_s=exact_time_limit_s)
        status = (
            "multiple"
            if count.count >= 2
            else (
                "timeout"
                if count.timed_out
                else "unique" if count.count == 1 else "unsatisfiable"
            )
        )
        metrics = ("steps", "first_placement_delay", "placement_gap_max", "probe_steps")
        delta = {
            key: (
                profile[key] - baseline[key]
                if profile[key] is not None and baseline[key] is not None
                else None
            )
            for key in metrics
        }
        rows.append(
            {
                "clue_id": index + 1,
                "holder": clue.holder,
                "exact_status": status,
                "solutions_found_capped_at_two": count.count,
                "exact_timed_out": count.timed_out,
                "solved": profile["solved"],
                "matches_solution": profile["matches_solution"],
                "retains_solution_at_every_step": profile[
                    "retains_solution_at_every_step"
                ],
                "delta": delta,
            }
        )
    return rows
