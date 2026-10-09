"""Exact solving: the oracle layer.

Two independent implementations, on purpose:

* `enumerate_cp` — CP-SAT (ortools). Production path. It supports complete model counting; the
  uniqueness front door stops at 2 because a second witness already proves non-uniqueness.
* `enumerate_dfs` — a plain depth-first search with candidate-mask pruning, written from
  `murdoku_lab.core.atoms.holds_atom` only. Slower, but it shares no code with the encoder, so
  `tests/test_encoding_agreement.py` can use it to catch encoder bugs.

Both return placements as `{character: cell}`. `count_solutions` reports `timed_out` honestly
instead of silently treating a timeout as uniqueness.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from ortools.sat.python import cp_model

from murdoku_lab.core.atoms import SPECS, Atom, unary_mask
from murdoku_lab.core.board import Scene
from murdoku_lab.core.instance import Case


@dataclass
class CountResult:
    count: int
    solutions: list[dict[str, int]]
    timed_out: bool

    @property
    def unique(self) -> bool:
        return self.count == 1 and not self.timed_out


# =============================================================================================
# Candidate masks — shared preprocessing. Sound for both back ends: a unary atom's mask is an
# exact characterisation of the cells its holder may occupy.
# =============================================================================================
def candidate_masks(case: Case) -> dict[str, frozenset[int]]:
    scene = case.scene
    cand = {x: frozenset(scene.open_cells) for x in case.characters}
    for a in case.atoms:
        if SPECS[a.kind].arity != "unary":
            continue
        m = unary_mask(a, scene)
        if m is not None:
            cand[a.holder] &= m
    # exclusive atoms also pin their own holder through a mask, when they have one
    for a in case.atoms:
        spec = SPECS[a.kind]
        if spec.arity == "global" and spec.mask is not None:
            m = unary_mask(a, scene)
            if m is not None:
                cand[a.holder] &= m
    return cand


# =============================================================================================
# CP-SAT encoder
# =============================================================================================
class CpEncoder:
    def __init__(self, case: Case):
        self.case = case
        self.scene = case.scene
        self.model = cp_model.CpModel()
        self.cand = candidate_masks(case)
        m = self.model
        s = self.scene
        self.cell, self.row, self.col, self.area = {}, {}, {}, {}
        for x in case.characters:
            dom = sorted(self.cand[x])
            if not dom:
                # infeasible by construction; encode a trivially false model
                self.cell[x] = m.NewIntVar(0, 0, f"cell_{x}")
                m.Add(self.cell[x] == 0)
                m.Add(self.cell[x] == 1)
                self.row[x] = m.NewIntVar(0, s.H - 1, f"row_{x}")
                self.col[x] = m.NewIntVar(0, s.W - 1, f"col_{x}")
                self.area[x] = m.NewIntVar(0, s.n_areas - 1, f"area_{x}")
                continue
            self.cell[x] = m.NewIntVarFromDomain(
                cp_model.Domain.FromValues(dom), f"cell_{x}"
            )
            self.row[x] = m.NewIntVar(0, s.H - 1, f"row_{x}")
            self.col[x] = m.NewIntVar(0, s.W - 1, f"col_{x}")
            self.area[x] = m.NewIntVar(0, s.n_areas - 1, f"area_{x}")
            # one table constraint ties cell to its derived coordinates and area
            m.AddAllowedAssignments(
                [self.cell[x], self.row[x], self.col[x], self.area[x]],
                [(k, s.row(k), s.col(k), s.area_of[k]) for k in dom],
            )

        # ---- the murderer rule is a RULE of the game, not a clue -----------------------------
        # The statement promises the solver that exactly one person was alone with the victim, so the
        # victim's area holds exactly two people. The reference counter enforces this as a hard prune
        # (`isVictim && L[te] > 1 || !s && te === W && L[te] >= 2`), and we did not — which let our
        # counts include arrangements their rules exclude, so a puzzle that is genuinely unique got
        # rejected as having several solutions, and constraint-first search wandered into arrangements
        # with no well-defined murderer at all. `open` mode drops the rule, matching their `!s`.
        if case.vdef.murderer_rule == "classic":
            v = case.victim
            for ar in range(s.n_areas):
                lits = []
                for z in case.characters:
                    if z == v:
                        continue
                    b = m.NewBoolVar(f"vic_{z}_a{ar}")
                    m.Add(self.area[z] == ar).OnlyEnforceIf(b)
                    m.Add(self.area[z] != ar).OnlyEnforceIf(b.Not())
                    lits.append(b)
                if not lits:
                    continue
                inv = m.NewBoolVar(f"victim_in_a{ar}")
                m.Add(self.area[v] == ar).OnlyEnforceIf(inv)
                m.Add(self.area[v] != ar).OnlyEnforceIf(inv.Not())
                # victim in this area  =>  exactly one other character is here
                m.Add(sum(lits) == 1).OnlyEnforceIf(inv)

        chars = list(case.characters)
        m.AddAllDifferent([self.cell[x] for x in chars])
        m.AddAllDifferent([self.row[x] for x in chars])
        m.AddAllDifferent([self.col[x] for x in chars])

        for a in case.atoms:
            self._encode(a)

    # ------------------------------------------------------------------------------- helpers
    def _member(self, x: str, S: Iterable[int]):
        """Boolean b <=> cell[x] in S."""
        S = set(S)
        b = self.model.NewBoolVar(f"in_{x}_{abs(hash(frozenset(S))) % 10**6}")
        self.model.AddAllowedAssignments(
            [self.cell[x], b], [(k, 1 if k in S else 0) for k in sorted(self.cand[x])]
        )
        return b

    def _forbid(self, x: str, S: Iterable[int]) -> None:
        bad = [(k,) for k in sorted(set(S) & self.cand[x])]
        if bad:
            self.model.AddForbiddenAssignments([self.cell[x]], bad)

    def _others(self, holder: str, *also: str) -> list[str]:
        skip = {holder, *also}
        return [x for x in self.case.characters if x not in skip]

    # ------------------------------------------------------------------------------ encoding
    def _encode(self, a: Atom) -> None:
        k, m, s = a.kind, self.model, self.scene
        spec = SPECS[k]

        # unary atoms are already in the domain via candidate_masks(); nothing more to add
        if spec.arity == "unary":
            return

        if k == "only_on":
            tgt = s.cells_with_object(a["obj"])
            for z in self._others(a.holder):
                self._forbid(z, tgt)
        elif k == "only_beside":
            tgt = s.cells_beside(a["obj"])
            for z in self._others(a.holder):
                self._forbid(z, tgt)
        elif k == "alone":
            for z in self._others(a.holder):
                m.Add(self.area[z] != self.area[a.holder])
        elif k == "area_empty":
            for z in self.case.characters:
                m.Add(self.area[z] != a["area"])
        elif k == "no_empty_area":
            for ar in range(s.n_areas):
                lits = []
                for z in self.case.characters:
                    b = m.NewBoolVar(f"{z}_in_a{ar}")
                    m.Add(self.area[z] == ar).OnlyEnforceIf(b)
                    m.Add(self.area[z] != ar).OnlyEnforceIf(b.Not())
                    lits.append(b)
                m.AddBoolOr(lits)
        elif k == "exactly_one_on":
            tgt = s.cells_with_object(a["obj"])
            m.Add(sum(self._member(z, tgt) for z in self.case.characters) == 1)
        elif k == "tag_in_area":
            tagged = [
                z
                for z in self._others(a.holder)
                if a["tag"] in self.case.tags.get(z, frozenset())
            ]
            if not tagged:
                m.Add(
                    self.cell[a.holder] == -1
                )  # unsatisfiable: nobody carries the tag
                return
            lits = []
            for z in tagged:
                b = m.NewBoolVar(f"tag_{z}_{a.holder}")
                m.Add(self.area[z] == self.area[a.holder]).OnlyEnforceIf(b)
                m.Add(self.area[z] != self.area[a.holder]).OnlyEnforceIf(b.Not())
                lits.append(b)
            m.AddBoolOr(lits)
        elif k == "with":
            m.Add(self.area[a.holder] == self.area[a["other"]])
        elif k == "not_with":
            m.Add(self.area[a.holder] != self.area[a["other"]])
        elif k == "alone_with":
            o = a["other"]
            m.Add(self.area[a.holder] == self.area[o])
            for z in self._others(a.holder, o):
                m.Add(self.area[z] != self.area[a.holder])
        elif k == "row_offset":
            m.Add(self.row[a.holder] - self.row[a["other"]] == a["d"])
        elif k == "col_offset":
            m.Add(self.col[a.holder] - self.col[a["other"]] == a["d"])
        elif k == "compass":
            for v, d in ((self.row, a["dr"]), (self.col, a["dc"])):
                lhs, rhs = v[a.holder], v[a["other"]]
                if d < 0:
                    m.Add(lhs < rhs)
                elif d > 0:
                    m.Add(lhs > rhs)
                else:
                    m.Add(lhs == rhs)
        elif k == "diagonal":
            o = a["other"]
            dr = m.NewIntVar(-s.H, s.H, f"dr_{a.holder}{o}")
            dc = m.NewIntVar(-s.W, s.W, f"dc_{a.holder}{o}")
            ar = m.NewIntVar(0, s.H, f"ar_{a.holder}{o}")
            ac = m.NewIntVar(0, s.W, f"ac_{a.holder}{o}")
            m.Add(dr == self.row[a.holder] - self.row[o])
            m.Add(dc == self.col[a.holder] - self.col[o])
            m.AddAbsEquality(ar, dr)
            m.AddAbsEquality(ac, dc)
            m.Add(ar == ac)
        elif k == "adjacent_to":
            o = a["other"]
            pairs = [
                (p, q)
                for p in sorted(self.cand[a.holder])
                for q in s.neighbours(p)
                if q in self.cand[o]
            ]
            if not pairs:
                m.Add(self.cell[a.holder] == -1)
                return
            m.AddAllowedAssignments([self.cell[a.holder], self.cell[o]], pairs)
        elif k == "other_beside":
            # at least one OTHER character shares the holder's area and is beside `obj`
            tgt = set(s.cells_beside(a["obj"]))
            lits = []
            for z in self._others(a.holder):
                b = m.NewBoolVar(f"ob_{z}_{a.holder}")
                same = m.NewBoolVar(f"obsame_{z}_{a.holder}")
                m.Add(self.area[z] == self.area[a.holder]).OnlyEnforceIf(same)
                m.Add(self.area[z] != self.area[a.holder]).OnlyEnforceIf(same.Not())
                near = self._member(z, tgt)
                m.AddBoolAnd([same, near]).OnlyEnforceIf(b)
                m.AddBoolOr([same.Not(), near.Not()]).OnlyEnforceIf(b.Not())
                lits.append(b)
            if not lits:
                m.Add(self.cell[a.holder] == -1)
                return
            m.AddBoolOr(lits)
        elif k == "area_no_gt":
            # area_no is area_of + 1, so comparing the ids is the same comparison.
            m.Add(self.area[a.holder] > self.area[a["other"]])
        elif k == "area_no_lt":
            m.Add(self.area[a.holder] < self.area[a["other"]])
        elif k == "area_no_offset":
            m.Add(self.area[a.holder] - self.area[a["other"]] == a["d"])
        elif k == "not_area_no_offset":
            m.Add(self.area[a.holder] - self.area[a["other"]] != a["d"])
        elif k == "only_tag_on":
            # the holder standing on `obj` is already in its domain via the mask; what remains is
            # that no OTHER tag-bearer stands on one.
            tgt = s.cells_with_object(a["obj"])
            for z in self._others(a.holder):
                if a["tag"] in self.case.tags.get(z, frozenset()):
                    self._forbid(z, tgt)
        elif k == "tag_in_area_on":
            tagged = [
                z
                for z in self._others(a.holder)
                if a["tag"] in self.case.tags.get(z, frozenset())
            ]
            tgt = s.cells_with_object(a["obj"])
            lits = []
            for z in tagged:
                b = m.NewBoolVar(f"tagobj_{z}_{a.holder}")
                on = self._member(z, tgt)
                same = m.NewBoolVar(f"same_{z}_{a.holder}")
                m.Add(self.area[z] == self.area[a.holder]).OnlyEnforceIf(same)
                m.Add(self.area[z] != self.area[a.holder]).OnlyEnforceIf(same.Not())
                # b <-> (z is on the object AND z shares the holder's area)
                m.AddBoolAnd([same, on]).OnlyEnforceIf(b)
                m.AddBoolOr([same.Not(), on.Not()]).OnlyEnforceIf(b.Not())
                lits.append(b)
            if not lits:
                m.Add(
                    self.cell[a.holder] == -1
                )  # nobody carries the tag: unsatisfiable
                return
            m.AddBoolOr(lits)
        elif k == "area_occupancy_parity":
            want = 0 if a["par"] == "even" else 1
            for ar in range(s.n_areas):
                if (ar + 1) % 2 != want:
                    continue
                lits = []
                for z in self.case.characters:
                    b = m.NewBoolVar(f"occ_{z}_a{ar}")
                    m.Add(self.area[z] == ar).OnlyEnforceIf(b)
                    m.Add(self.area[z] != ar).OnlyEnforceIf(b.Not())
                    lits.append(b)
                cnt = m.NewIntVar(0, len(lits), f"cnt_a{ar}")
                m.Add(cnt == sum(lits))
                par = m.NewIntVar(0, 1, f"par_a{ar}")
                m.AddModuloEquality(par, cnt, 2)
                m.Add(par == want)
        else:
            raise NotImplementedError(f"no CP encoding for atom kind {k!r}")


class _Collector(cp_model.CpSolverSolutionCallback):
    def __init__(self, enc: CpEncoder, cap: int | None):
        super().__init__()
        self.enc, self.cap, self.out = enc, cap, []

    def on_solution_callback(self) -> None:
        self.out.append({x: self.Value(v) for x, v in self.enc.cell.items()})
        if self.cap is not None and len(self.out) >= self.cap:
            self.StopSearch()


def enumerate_cp(
    case: Case, cap: int | None = None, time_limit_s: float = 20.0
) -> CountResult:
    """Enumerate solutions with CP-SAT. `cap=None` means *all* of them (exact count)."""
    enc = CpEncoder(case)
    solver = cp_model.CpSolver()
    solver.parameters.enumerate_all_solutions = True
    solver.parameters.max_time_in_seconds = time_limit_s
    solver.parameters.num_workers = 1  # enumeration must be deterministic
    solver.parameters.random_seed = 0
    col = _Collector(enc, cap)
    status = solver.Solve(enc.model, col)
    timed_out = status == cp_model.UNKNOWN or (
        solver.WallTime() >= time_limit_s
        and status != cp_model.OPTIMAL
        and not (cap is not None and len(col.out) >= cap)
    )
    return CountResult(len(col.out), col.out, timed_out)


# =============================================================================================
# Independent DFS reference implementation — evaluates atoms only through holds_atom()
# =============================================================================================
def enumerate_dfs(case: Case, cap: int | None = None) -> CountResult:
    scene = case.scene
    cand = candidate_masks(case)
    # order by fewest candidates: cheap and makes the search behave on 8-9 boards
    order = sorted(case.characters, key=lambda x: len(cand[x]))
    out: list[dict[str, int]] = []
    pl: dict[str, int] = {}
    used_rows: set[int] = set()
    used_cols: set[int] = set()

    # atoms grouped by the last character to be placed, so each is checked as early as possible
    pos = {x: i for i, x in enumerate(order)}
    ready_at: dict[int, list[Atom]] = {i: [] for i in range(len(order))}
    for a in case.atoms:
        deps = [x for x in (a.holder, a.other) if x]
        # Scheduled by ARITY, not by a flag. A `global` atom quantifies over the whole cast, so it can
        # only be judged once everyone is placed — and crucially a POSITIVE existential ("someone else
        # in my area was beside a chair") is FALSE on every partial placement, so testing it early
        # prunes every branch. This used to key off `exclusive`, which `other_beside` does not set:
        # the DFS found 0 solutions where CP-SAT found 40. Keying off arity means a newly registered
        # predicate cannot reintroduce it by forgetting a flag.
        if SPECS[a.kind].arity == "global" or SPECS[a.kind].needs_tags:
            ready_at[len(order) - 1].append(a)  # needs the whole placement
        else:
            ready_at[max(pos[x] for x in deps)].append(a)

    victim = case.victim if case.vdef.murderer_rule == "classic" else None

    def victim_area_ok() -> bool:
        """The victim's area holds exactly two people once everyone is placed, and never more than two
        along the way. Same rule the reference counter prunes on."""
        if victim is None or victim not in pl:
            return True
        va = scene.area_of[pl[victim]]
        n_here = sum(1 for x, k in pl.items() if scene.area_of[k] == va)
        if n_here > 2:
            return False
        return not (len(pl) == len(order) and n_here != 2)

    def rec(i: int) -> bool:
        if i == len(order):
            # A pair clue such as alone_with can become false when a later
            # character enters its area. Early checks are only pruning hints.
            if victim_area_ok() and case.satisfies(pl):
                out.append(dict(pl))
            return cap is not None and len(out) >= cap
        x = order[i]
        for k in sorted(cand[x]):
            r, c = scene.row(k), scene.col(k)
            if r in used_rows or c in used_cols or k in pl.values():
                continue
            pl[x] = k
            used_rows.add(r)
            used_cols.add(c)
            from murdoku_lab.core.atoms import holds_atom

            ok = victim_area_ok() and all(
                holds_atom(a, scene, pl, case.tags) for a in ready_at[i]
            )
            if ok and rec(i + 1):
                return True
            del pl[x]
            used_rows.discard(r)
            used_cols.discard(c)
        return False

    rec(0)
    return CountResult(len(out), out, False)


# =============================================================================================
# Front doors
# =============================================================================================
def count_solutions(
    case: Case, cap: int | None = None, time_limit_s: float = 20.0
) -> CountResult:
    return enumerate_cp(case, cap=cap, time_limit_s=time_limit_s)


def unique_solution(case: Case, time_limit_s: float = 20.0) -> dict[str, int] | None:
    """Return the solution iff there is exactly one; else None. Uniqueness is *proved*."""
    r = enumerate_cp(case, cap=2, time_limit_s=time_limit_s)
    if r.timed_out or r.count != 1:
        return None
    return r.solutions[0]
