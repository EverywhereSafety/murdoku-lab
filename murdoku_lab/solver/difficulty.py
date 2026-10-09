"""Difficulty: a region in certificate space, declared as data.

`classify` reads a `Certificate` and returns a band name. Bands live in
`murdoku_lab/resources/difficulty_bands.json` so retuning never means editing code. The band order is a total
order easiest-first, and `band_index` exposes it so monotonicity can be asserted in tests:
carving a clue must never *lower* the band.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from murdoku_lab.core.atoms import SPECS
from murdoku_lab.core.instance import Case
from .logic import Certificate

from murdoku_lab.paths import DEFAULTS

CONFIG = DEFAULTS / "difficulty_bands.json"


@lru_cache(maxsize=1)
def _cfg() -> dict:
    return json.loads(CONFIG.read_text())


def band_order() -> list[str]:
    return list(_cfg()["order"])


def band_index(band: str) -> int:
    return band_order().index(band)


def features(cert: Certificate) -> dict:
    """The difficulty vector — everything a band predicate may look at."""
    return {
        "advanced": cert.advanced,
        "tier_max": cert.tier_max,
        "depth": cert.depth,
        "width": cert.max_width,
        "cost": round(cert.cost, 3),
        "guess_free": cert.solved,
    }


def _matches(spec: dict, f: dict) -> bool:
    for key, val in spec.items():
        if key.startswith("_"):
            continue
        name, _, bound = key.rpartition("_")
        if bound == "min" and f.get(name, 0) < val:
            return False
        if bound == "max" and f.get(name, 0) > val:
            return False
    return True


def classify(cert: Certificate) -> str | None:
    """First band (easiest-first) whose predicate the certificate satisfies."""
    if not cert.solved:
        return None
    f = features(cert)
    cfg = _cfg()
    for name in cfg["order"]:
        if _matches(cfg["bands"][name], f):
            return name
    return None


def caps(band: str) -> dict:
    return dict(_cfg()["caps"].get(band, {}))


def style() -> dict:
    return dict(_cfg()["style"])


def structural_counts(case: Case) -> dict:
    """The reference generator's structural proxies, recomputed on our cases for comparability."""
    from murdoku_lab.core.atoms import SPECS

    pos = sum(1 for a in case.atoms if SPECS[a.kind].positional)
    from murdoku_lab.solver.exact import candidate_masks

    masks = candidate_masks(case)
    pins = sum(1 for x in case.characters if len(masks.get(x, ())) == 1)
    return {
        "positional": pos,
        "instant_pins": pins,
        "n_clues": len(case.clues),
        "n_atoms": len(case.atoms),
    }


def respects_caps(case: Case, band: str) -> bool:
    """Structural caps, scaled by cast size.

    The per-band numbers are calibrated on 6-9 person boards. Applied literally to a 16-person cast
    they reject everything: "at most one character may be pinned outright" is unsatisfiable when
    sixteen characters each need a clue. The `scaling` block raises the cap in proportion to the
    cast, and never lowers it below the per-band figure.
    """
    c, st = caps(band), structural_counts(case)
    n = len(case.characters)
    sc = _cfg().get("caps", {}).get("scaling", {})

    def limit(key: str, rate_key: str, default: int = 99) -> int:
        base = int(c.get(key, default))
        rate = float(sc.get(rate_key, 0.0))
        return max(base, round(rate * n)) if rate else base

    return st["positional"] <= limit(
        "max_positional", "max_positional_per_character"
    ) and st["instant_pins"] <= limit(
        "max_instant_pins", "max_instant_pins_per_character"
    )


# Negated predicates. Readable puzzles need positive anchors to hang the deduction on.
#
# Both sets are DERIVED, not listed. Hardcoding them was a trap: the lists were written when there
# were 20 predicates, and every one added since fell outside both — so on a variant allowing the full
# catalogue, a perfectly good carved set of `area_no_gt` / `diagonal` / `on_grid_edge` atoms scored
# ZERO anchors and `style_floor` rejected 280 of 349 attempts. A rule that silently stops applying to
# new predicates is worse than no rule.
# The name heuristic below is right for 8 of 9 candidates and wrong for one, so the exception is
# listed rather than left to bite: `no_empty_area` READS as a denial and IS a positive claim about the
# whole board — every area holds somebody. Counting it as a negation would skew `min_positive_frac`
# against a clue that helps a solver.
_NOT_REALLY_NEGATIVE = frozenset({"no_empty_area"})

# Positive locators the structural rule below misses. `only_beside` is a global non-pinning atom and
# so falls outside it, yet "X was the only person beside a carpet" is one of the strongest anchors
# there is; `on_extreme` names a line of the grid rather than a prop or an area.
_ALSO_ANCHORS = frozenset({"only_beside", "on_extreme"})


def _negative_kinds() -> frozenset[str]:
    """Anything phrased as a denial. The name is the signal, which is how a reader sees it too."""
    return frozenset(
        k
        for k in SPECS
        if (k.startswith("not_") or k.startswith("no_"))
        and k not in _NOT_REALLY_NEGATIVE
    )


def _anchor_kinds() -> frozenset[str]:
    """A clue a solver can hang a deduction on: it says positively where somebody was, in terms of
    something visible on the board — a prop, an area, a corner, a door, or another person's area.

    Excluded: denials, raw coordinates (`abs_row`), and the whole-board general clues, none of which
    localise anybody on their own.
    """
    out = set()
    for k, sp in SPECS.items():
        if k in _negative_kinds() or sp.positional:
            continue
        if (
            sp.arity == "global"
            and not sp.pinning
            and k not in ("alone", "other_beside")
        ):
            continue
        if (
            any(p in sp.params for p in ("obj", "area", "areas", "ter"))
            or not sp.params
        ):
            out.add(k)
        elif sp.relational and k in ("with", "alone_with", "adjacent_to"):
            out.add(k)
    return frozenset(out | _ALSO_ANCHORS)


NEGATIVE_KINDS = _negative_kinds()
ANCHOR_KINDS = _anchor_kinds()


def style_ok(atoms, band: str, n_characters: int | None = None) -> bool:
    """Puzzle-quality floors: enough positive clues, enough anchors, not too many clues.

    `n_characters` makes the atom budget scale with the cast. A fixed cap tuned on a 6x6 board
    rejects every 16x16 case outright — sixteen suspects need roughly one clue each, which is what
    the reference game's own large boards ship. Omit it and the fixed cap applies, so existing
    callers keep their old behaviour.
    """
    st = style()
    atoms = list(atoms)
    if not atoms:
        return False
    pos = sum(1 for a in atoms if a.kind not in NEGATIVE_KINDS)
    if pos / len(atoms) < float(st.get("min_positive_frac", 0.0)):
        return False
    want_anchors = int(st.get("min_anchor_atoms", 0))
    if n_characters:
        want_anchors = max(
            want_anchors,
            round(float(st.get("min_anchor_per_character", 0.0)) * n_characters),
        )
    if sum(1 for a in atoms if a.kind in ANCHOR_KINDS) < want_anchors:
        return False
    cap = st.get("max_atoms_total", {}).get(band)
    if cap is not None:
        limit = int(cap)
        if n_characters:
            limit = max(
                limit,
                round(float(st.get("max_atoms_per_character", 0.0)) * n_characters),
            )
        if len(atoms) > limit:
            return False
    return True
