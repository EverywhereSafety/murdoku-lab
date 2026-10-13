"""Shared spatial organization before either setter creates clues.

Works only with geometry and prop classes. It neither sees a solution nor changes
the variant's vocabulary, standability flags, solver or acceptance criteria.
"""

from collections import defaultdict
from murdoku_lab.core.board import Prop, Scene, TERRAINS

# Only these named objects are naturally drawn as a footprint. Anonymous props
# already describe one board-local thing, so their whole footprint is clustered.
_WIDE = frozenset({"bed", "carpet", "table", "car", "golf_cart", "sand", "water"})


def _connected(cells, neighbours):
    if not cells:
        return False
    seen, todo = set(), [min(cells)]
    while todo:
        k = todo.pop()
        if k in seen:
            continue
        seen.add(k)
        todo.extend(m for m in neighbours[k] if m in cells and m not in seen)
    return len(seen) == len(cells)


def _shape_areas(scene, rng, neighbours, *, protected_areas=frozenset()):
    areas = list(scene.area_of)
    members = {a: set(scene.cells_of_area(a)) for a in range(scene.n_areas)}
    candidates = list(range(scene.n_cells))
    rng.shuffle(candidates)
    touches = defaultdict(int)
    moves = 0
    for k in candidates:
        source = areas[k]
        if source in protected_areas:
            continue
        targets = sorted({areas[m] for m in neighbours[k]} - {source} - protected_areas)
        rng.shuffle(targets)
        for target in targets:
            if max(touches[source], touches[target]) >= 3:
                continue
            take = {k}
            along = [
                m
                for m in neighbours[k]
                if areas[m] == source and any(areas[j] == target for j in neighbours[m])
            ]
            if scene.W >= 10 and along and rng.random() < 0.6:
                take.add(rng.choice(along))
            remaining = members[source] - take
            if len(remaining) < 4 or not _connected(remaining, neighbours):
                continue
            members[source] = remaining
            members[target] |= take
            for m in take:
                areas[m] = target
            touches[source] += 1
            touches[target] += 1
            moves += 1
            break
        if moves >= scene.n_areas:
            break
    return areas, members


def _doors(areas, dry, neighbours, n_areas, rng, rate):
    contacts = defaultdict(list)
    for k in sorted(dry):
        for m in neighbours[k]:
            if m > k and m in dry and areas[k] != areas[m]:
                contacts[tuple(sorted((areas[k], areas[m])))].append((k, m))
    pairs = sorted(contacts)
    rng.shuffle(pairs)
    parent = list(range(n_areas))

    def root(a):
        while parent[a] != a:
            a = parent[a]
        return a

    doors = []
    for a, b in pairs:
        ra, rb = root(a), root(b)
        if ra != rb or rng.random() < rate:
            parent[ra] = rb
            doors.append(frozenset(rng.choice(contacts[a, b])))
    return frozenset(doors)


def _patch(available, count, neighbours, rng, preferred):
    anchors = sorted(available)
    rng.shuffle(anchors)
    anchors.sort(key=lambda k: k not in preferred)
    for start in anchors:
        found, frontier = {start}, [start]
        while frontier and len(found) < count:
            k = frontier.pop(0)
            options = [m for m in neighbours[k] if m in available and m not in found]
            rng.shuffle(options)
            for m in options:
                found.add(m)
                frontier.append(m)
                if len(found) == count:
                    break
        if len(found) == count:
            return found
    return None


def enrich_scene(scene, rng, *, anonymous=False, door_rate=0.35, shape_areas=True):
    """Keep prop-cell budgets; cluster footprints and reserve coherent room passages.

    With unusual inputs a whole anonymous footprint may not fit in one room. Split
    it into the largest available connected patches rather than lose cells or loop.
    """
    neighbours = {k: scene.neighbours(k) for k in range(scene.n_cells)}
    if shape_areas:
        areas, members = _shape_areas(scene, rng, neighbours)
    else:
        areas = list(scene.area_of)
        members = {a: set(scene.cells_of_area(a)) for a in range(scene.n_areas)}
    dry = {k for k, t in enumerate(scene.terrain_of) if TERRAINS[t].standable}
    doors = (
        _doors(areas, dry, neighbours, scene.n_areas, rng, door_rate)
        if door_rate
        else frozenset()
    )
    reserved = {k for d in doors for k in d}
    free = set(range(scene.n_cells))
    used = defaultdict(int)
    walls = {
        k
        for k in free
        if len(neighbours[k]) < 4 or any(areas[k] != areas[m] for m in neighbours[k])
    }
    props = []
    ordered = sorted(scene.props, key=lambda p: (p.standable, -len(p.cells), p.pid))
    for prop in ordered:
        remaining, placed = len(prop.cells), set()
        while remaining:
            size = (
                remaining
                if anonymous
                else min(remaining, 2 if prop.pid in _WIDE else 1)
            )
            allowed = (free & dry) - (reserved if not prop.standable else set())
            preferred = (
                walls
                if not prop.standable and not prop.landmark
                else {
                    k
                    for k in allowed
                    if any(
                        m not in free and areas[m] == areas[k] for m in neighbours[k]
                    )
                }
            )
            order = list(members)
            rng.shuffle(order)
            order.sort(key=lambda a: (used[a] / len(members[a])))
            chosen = None
            while size and chosen is None:
                for area in order:
                    available = allowed & members[area]
                    if len(available) < size:
                        continue
                    chosen = _patch(available, size, neighbours, rng, preferred)
                    if chosen is not None:
                        break
                if chosen is None:
                    size -= 1
            if chosen is None:
                # Pathological density / terrain inputs: preserve budgets and formal
                # flags even if a nice dry footprint is impossible. Remove any door
                # whose endpoint becomes blocked; normal setter feasibility gates apply.
                chosen = {min(free)}
            free -= chosen
            placed |= chosen
            remaining -= len(chosen)
            for k in chosen:
                used[areas[k]] += 1
        props.append(Prop(prop.pid, prop.standable, frozenset(placed), prop.landmark))
    blocked = {k for p in props if not p.standable for k in p.cells} | (
        set(range(scene.n_cells)) - dry
    )
    doors = frozenset(d for d in doors if not d & blocked)
    return Scene(
        scene.W,
        scene.H,
        tuple(areas),
        (None,) * scene.n_cells,
        doors,
        terrain_of=scene.terrain_of,
        props=tuple(props),
    )


def courtyard_layout(scene, rng):
    """Four wings around a connected gallery and central open courtyard.

    Applied before props and hidden placements. Room widths vary by seed;
    area IDs remain aligned with the fourteen regional role profiles.
    """
    from dataclasses import replace

    if scene.W != scene.H or scene.W < 16 or scene.n_areas != 14:
        raise ValueError("courtyard layout needs a square board >=16 and 14 areas")
    n = scene.W
    wing = min((n - 8) // 2, n // 4 + rng.choice((-1, 0, 1)))
    middle = n // 2 + rng.choice((-1, 0, 1))
    cuts = [0, n // 4, middle, n - n // 4, n]
    # Vary the two internal subdivisions without creating tiny rooms.
    cuts[1] += rng.choice((-1, 0, 1))
    cuts[3] += rng.choice((-1, 0, 1))
    areas = []
    for r in range(n):
        for c in range(n):
            if r < wing or r >= n - wing:
                area = next(i for i in range(4) if cuts[i] <= c < cuts[i + 1])
                area += 0 if r < wing else 4
            elif c < wing:
                area = 8 if r < middle else 9
            elif c >= n - wing:
                area = 10 if r < middle else 11
            elif wing + 2 <= r < n - wing - 2 and wing + 2 <= c < n - wing - 2:
                area = 13
            else:
                area = 12
            areas.append(area)
    neighbours = {k: scene.neighbours(k) for k in range(scene.n_cells)}
    shaped = replace(scene, area_of=tuple(areas))
    areas, _ = _shape_areas(shaped, rng, neighbours, protected_areas={12, 13})
    doors = _doors(areas, set(range(scene.n_cells)), neighbours, 14, rng, 0.3)
    return replace(scene, area_of=tuple(areas), doors=doors)


def furniture_footprint(available, count, neighbours, rng, preferred, width):
    """Prefer straight or rectangular furniture instead of bent flood-fill blobs."""
    shapes = [(h, count // h) for h in range(1, count + 1) if count % h == 0]
    candidates = []
    for start in sorted(available):
        r, c = divmod(start, width)
        for h, w in shapes:
            if c + w > width or max(h, w) > 4:
                continue
            cells = {((r + dr) * width + c + dc) for dr in range(h) for dc in range(w)}
            if cells <= available:
                # Compact tables/beds; wall contact wins ties among similar shapes.
                score = (max(h, w) - min(h, w), -len(cells & preferred))
                candidates.append((score, cells))
    if candidates:
        rng.shuffle(candidates)
        return min(candidates, key=lambda item: item[0])[1]
    return _patch(available, count, neighbours, rng, preferred)
