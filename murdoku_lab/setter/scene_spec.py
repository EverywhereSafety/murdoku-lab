"""Small, public scene requirements for the unified setter.

This is a deterministic CPU interface a later text/LLM planner can target.
Version 1 supports area count, standable anchor counts and optional prop cell budgets. It does not
introduce rules, identities, clues, arbitrary graph layouts or hidden placements.
"""

from dataclasses import replace
import math

from murdoku_lab.core.board import OBJECTS, Prop, TERRAINS

SCHEMA = "murdoku.scene_spec/1"


class SceneSpecInfeasible(ValueError):
    """The sampled board cannot satisfy an otherwise well-formed scene request."""


def normalize_spec(value, *, size, n_areas=None):
    if value is None:
        return None
    if not isinstance(value, dict) or value.get("schema") != SCHEMA:
        raise ValueError(f"scene_spec must be an object with schema {SCHEMA!r}")
    unknown = set(value) - {
        "schema",
        "area_count",
        "anchors_per_area",
        "blocker_rate",
        "furniture_rate",
    }
    if unknown:
        raise ValueError(f"unsupported scene_spec fields: {sorted(unknown)}")
    rates = {}
    for name, default in (("blocker_rate", 0.14), ("furniture_rate", 0.10)):
        rate = value.get(name, default)
        if (
            isinstance(rate, bool)
            or not isinstance(rate, (int, float))
            or not math.isfinite(rate)
            or not 0 <= rate <= 0.6
        ):
            raise ValueError(f"{name} must be finite and in 0..0.6")
        if name in value:
            rates[name] = float(rate)
    if value.get("blocker_rate", 0.14) + value.get("furniture_rate", 0.10) > 0.65:
        raise ValueError("combined prop density must not exceed 0.65")
    area_count = value.get("area_count")
    if area_count is not None:
        if type(area_count) is not int or not 1 <= area_count <= size:
            raise ValueError(
                "scene_spec area_count must be an integer in 1..board side"
            )
        if n_areas is not None and n_areas != area_count:
            raise ValueError("n_areas conflicts with scene_spec area_count")
    anchors = value.get("anchors_per_area", {})
    if not isinstance(anchors, dict) or len(anchors) > 8:
        raise ValueError("anchors_per_area must map at most 8 prop IDs to counts")
    for prop, count in anchors.items():
        if not isinstance(prop, str) or not prop or len(prop) > 80:
            raise ValueError(
                "anchor IDs must be nonempty strings of at most 80 characters"
            )
        if type(count) is not int or not 1 <= count <= 4:
            raise ValueError("anchor counts must be integers in 1..4")
    out = {"schema": SCHEMA, "anchors_per_area": dict(sorted(anchors.items()))}
    if area_count is not None:
        out["area_count"] = area_count
    out.update(rates)
    return out


def choose_area_count(size, rng, *, n_areas=None, spec=None):
    requested = spec.get("area_count") if spec else None
    if requested is None:
        requested = n_areas
    if requested is not None:
        if type(requested) is not int or not 1 <= requested <= size:
            raise ValueError("n_areas must be an integer in 1..board side")
        return requested
    if size >= 10:
        return rng.choice((max(4, size // 2 - 1), size // 2, size // 2 + 1))
    lower, upper = max(3, size // 2), min(size - 1, (3 * size + 3) // 4)
    return rng.randint(lower, max(lower, upper))


def apply_spec(scene, spec, rng, *, allowed_objects=()):
    if spec is None:
        return scene
    if spec.get("area_count", scene.n_areas) != scene.n_areas:
        raise SceneSpecInfeasible("sampled board has the wrong area count")
    anchors = spec["anchors_per_area"]
    if not anchors:
        return scene
    definitions = {}
    for pid in anchors:
        if pid in scene.prop_by_id:
            prop = scene.prop_by_id[pid]
            definitions[pid] = (prop.standable, prop.landmark)
        elif pid in allowed_objects and pid in OBJECTS:
            kind = OBJECTS[pid]
            definitions[pid] = (kind.occupiable, kind.landmark)
        else:
            raise ValueError(f"anchor {pid!r} is not declared by this board or variant")
        if not definitions[pid][0]:
            raise ValueError(f"anchor {pid!r} must be standable in scene_spec/1")

    kept = [p for p in scene.props if p.pid not in anchors]
    occupied = {k for p in kept for k in p.cells}
    free = {
        k
        for k, terrain in enumerate(scene.terrain_of)
        if TERRAINS[terrain].standable and k not in occupied
    }
    footprints = {pid: set() for pid in anchors}
    needed = sum(anchors.values())
    for area in range(scene.n_areas):
        candidates = sorted(free & set(scene.cells_of_area(area)))
        if len(candidates) < needed:
            raise SceneSpecInfeasible(f"area {area + 1} cannot fit {needed} anchors")
        cells = rng.sample(candidates, needed)
        cursor = 0
        for pid, count in anchors.items():
            footprints[pid].update(cells[cursor : cursor + count])
            cursor += count
    props = kept + [
        Prop(pid, definitions[pid][0], frozenset(cells), definitions[pid][1])
        for pid, cells in footprints.items()
    ]
    return replace(scene, props=tuple(sorted(props, key=lambda p: p.pid)))


def spec_satisfied(scene, spec):
    if spec.get("area_count", scene.n_areas) != scene.n_areas:
        return False
    for pid, count in spec.get("anchors_per_area", {}).items():
        prop = scene.prop_by_id.get(pid)
        if prop is None or not prop.standable:
            return False
        if any(
            sum(scene.area_of[k] == area for k in prop.cells) != count
            for area in range(scene.n_areas)
        ):
            return False
        if any(not scene.standable(k) for k in prop.cells):
            return False
    return True


def sampling_rates(spec):
    """Optional cell budgets applied before placement/clue generation."""
    return {
        name: spec[name]
        for name in ("blocker_rate", "furniture_rate")
        if spec and name in spec
    }
