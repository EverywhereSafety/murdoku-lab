"""Public geometry and regional roles applied before placement or clue generation.

Scene requests configure area count, standable anchors, prop-cell budgets and
local terrain/prop profiles. They contain no identities, clues or placements.
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
        "regions",
        "layout",
    }
    if unknown:
        raise ValueError(f"unsupported scene_spec fields: {sorted(unknown)}")
    layout = value.get("layout")
    if layout is not None and (layout != "courtyard" or size < 16):
        raise ValueError("courtyard layout requires a board side of at least 16")
    if layout and value.get("area_count", 14) != 14:
        raise ValueError("courtyard layout requires 14 areas")
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
    area_count = value.get("area_count", 14 if layout else None)
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
    if layout:
        out["layout"] = layout
    if "regions" in value:
        if anchors:
            raise ValueError(
                "region prop budgets and anchors_per_area cannot be combined"
            )
        regions = value["regions"]
        if not isinstance(regions, list) or not regions or len(regions) > 24:
            raise ValueError("regions must contain 1..24 area profiles")
        normalized = []
        for region in regions:
            if not isinstance(region, dict) or set(region) != {
                "name",
                "ground",
                "patches",
                "props",
            }:
                raise ValueError("each region needs name, ground, patches and props")
            if not isinstance(region["name"], str) or not region["name"].strip():
                raise ValueError("region names must be nonempty")
            if (
                not isinstance(region["ground"], str)
                or region["ground"] not in TERRAINS
                or not TERRAINS[region["ground"]].standable
            ):
                raise ValueError("region ground must be standable terrain")
            for field, known, maximum in (
                ("patches", TERRAINS, 0.45),
                ("props", OBJECTS, 0.4),
            ):
                values = region[field]
                if not isinstance(values, dict) or any(
                    key not in known for key in values
                ):
                    raise ValueError(f"unknown region {field}")
                if any(
                    type(rate) not in (int, float)
                    or not math.isfinite(rate)
                    or not 0 < rate <= maximum
                    for rate in values.values()
                ):
                    raise ValueError(f"invalid region {field} density")
                if sum(values.values()) > maximum:
                    raise ValueError(f"region {field} density exceeds {maximum}")
            if region["ground"] in region["patches"]:
                raise ValueError("patch terrain must differ from region ground")
            normalized.append(
                {
                    **region,
                    "patches": dict(region["patches"]),
                    "props": dict(region["props"]),
                }
            )
        out["regions"] = normalized
        if len({region["name"] for region in normalized}) != len(normalized):
            raise ValueError("region role names must be distinct")
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
    if spec.get("layout") == "courtyard":
        from .scene_layout import courtyard_layout

        scene = courtyard_layout(scene, rng)
    if "regions" in spec:
        scene = _apply_regions(
            scene,
            spec["regions"],
            rng,
            allowed_objects,
            arranged=spec.get("layout") == "courtyard",
        )
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


def _apply_regions(scene, regions, rng, allowed_objects, *, arranged=False):
    """Build coherent local footprints before placements or clues exist."""
    from .scene_layout import _patch, furniture_footprint

    neighbours = {k: scene.neighbours(k) for k in range(scene.n_cells)}
    terrain = ["floor"] * scene.n_cells
    footprints = {}
    reserved = {k for door in scene.doors for k in door}
    for area in range(scene.n_areas):
        region = regions[area % len(regions)]
        cells = set(scene.cells_of_area(area))
        for k in cells:
            terrain[k] = region["ground"]
        free = cells - reserved
        for kind, rate in region["patches"].items():
            count = max(1, round(len(cells) * rate))
            patch = _patch(free, count, neighbours, rng, set())
            if patch is None:
                raise SceneSpecInfeasible(f"area {area + 1} cannot fit terrain patch")
            for k in patch:
                terrain[k] = kind
            free -= patch
        free = {k for k in cells - reserved if TERRAINS[terrain[k]].standable}
        for pid, rate in region["props"].items():
            if pid not in allowed_objects:
                raise ValueError(f"region prop {pid!r} is not allowed by this variant")
            remaining = max(1, round(len(cells) * rate))
            # Furniture occupies one compact footprint; trees and flowers form
            # several small groups rather than a single giant icon.
            width = 4 if pid in {"table", "carpet", "bed", "car", "golf_cart"} else 2
            if arranged:
                width = (
                    6
                    if pid in {"table", "bed", "shelf"}
                    else 2 if pid == "piano" else 1
                )
            while remaining:
                count = min(width, remaining)
                walls = {
                    k
                    for k in free
                    if len(neighbours[k]) < 4
                    or any(scene.area_of[m] != area for m in neighbours[k])
                }
                nearby = {
                    k
                    for k in free
                    if any(m in footprints.get("table", set()) for m in neighbours[k])
                }
                preferred = (
                    nearby
                    if pid == "chair"
                    else (
                        walls
                        if pid in {"shelf", "bed", "piano", "crate", "barrel", "tv"}
                        else set()
                    )
                )
                if arranged and pid in {"table", "bed", "shelf", "piano"}:
                    patch = furniture_footprint(
                        free, count, neighbours, rng, preferred, scene.W
                    )
                elif arranged and pid == "chair":
                    seats = {
                        k
                        for k in free
                        if not any(
                            m in footprints.get("chair", set()) for m in neighbours[k]
                        )
                    }
                    patch = _patch(seats or free, count, neighbours, rng, preferred)
                else:
                    patch = _patch(free, count, neighbours, rng, preferred)
                if patch is None:
                    raise SceneSpecInfeasible(f"area {area + 1} cannot fit {pid}")
                footprints.setdefault(pid, set()).update(patch)
                free -= patch
                remaining -= count
    props = tuple(
        Prop(pid, OBJECTS[pid].occupiable, frozenset(cells), OBJECTS[pid].landmark)
        for pid, cells in sorted(footprints.items())
    )
    blocked = {
        k for k in range(scene.n_cells) if not TERRAINS[terrain[k]].standable
    } | {k for p in props if not p.standable for k in p.cells}
    return replace(
        scene,
        obj_of=(None,) * scene.n_cells,
        terrain_of=tuple(terrain),
        props=props,
        doors=frozenset(d for d in scene.doors if not d & blocked),
    )


def theme_for_spec(case, spec, *, title, seed=None):
    """Use the same region roles for presentation and pre-clue geometry."""
    from murdoku_lab.core.name_library import preset_theme

    theme = preset_theme(case, seed=seed)
    regions = spec.get("regions", []) if spec else []
    if regions:
        names = [regions[a % len(regions)]["name"] for a in range(case.scene.n_areas)]
        counts = {name: names.count(name) for name in names}
        names = tuple(
            name if counts[name] == 1 else f"{name} {a // len(regions) + 1}"
            for a, name in enumerate(names)
        )
        theme = replace(
            theme,
            areas=names,
            objects={pid: pid.replace("_", " ") for pid in case.scene.prop_by_id},
        )
        if case.variant != "course":
            theme = replace(
                theme,
                objects={
                    **theme.objects,
                    "fairway": "short grass",
                    "rough": "long grass",
                },
            )
    theme = replace(theme, title=title)
    theme.validate(case)
    return theme


def spec_satisfied(scene, spec):
    if spec.get("area_count", scene.n_areas) != scene.n_areas:
        return False
    if "regions" in spec:
        from .scene_layout import _connected

        neighbours = {k: scene.neighbours(k) for k in range(scene.n_cells)}
        for area in range(scene.n_areas):
            region = spec["regions"][area % len(spec["regions"])]
            cells = set(scene.cells_of_area(area))
            patches = {
                kind: max(1, round(len(cells) * rate))
                for kind, rate in region["patches"].items()
            }
            expected_terrain = {
                region["ground"]: len(cells) - sum(patches.values()),
                **patches,
            }
            if any(
                sum(scene.terrain_of[k] == kind for k in cells)
                != expected_terrain.get(kind, 0)
                for kind in TERRAINS
            ):
                return False
            if any(
                not _connected(
                    {k for k in cells if scene.terrain_of[k] == kind}, neighbours
                )
                for kind in patches
            ):
                return False
            expected_props = {
                pid: max(1, round(len(cells) * rate))
                for pid, rate in region["props"].items()
            }
            if any(
                sum(scene.obj_of[k] == pid for k in cells) != expected_props.get(pid, 0)
                for pid in set(scene.prop_by_id) | set(expected_props)
            ):
                return False
        if any(
            not TERRAINS[scene.terrain_of[k]].standable
            for p in scene.props
            for k in p.cells
        ):
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
