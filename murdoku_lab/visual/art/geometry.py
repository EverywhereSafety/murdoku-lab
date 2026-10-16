"""Board geometry shared by every casebook layer. Reads only the public observation."""

from .palette import delta_e

CELL = 100
PAD = 40
# CIEDE2000 distance that keeps two touching room tints apart at a glance.
MIN_NEIGHBOUR_GAP = 10.0


def origin(cell):
    return PAD + cell["col"] * CELL, PAD + cell["row"] * CELL


def by_label(observation):
    return {c["cell"]: c for c in observation["scene"]["cells"]}


def dimensions(observation):
    scene = observation["scene"]
    return scene["width"] * CELL + PAD * 2, scene["height"] * CELL + PAD * 2


def connected(labels, cells_by_label):
    """Connected pieces of a set of cells, never crossing an area boundary."""
    todo = set(labels)
    while todo:
        start = min(
            todo, key=lambda s: (cells_by_label[s]["row"], cells_by_label[s]["col"])
        )
        todo.remove(start)
        stack, members = [start], []
        while stack:
            label = stack.pop()
            c = cells_by_label[label]
            members.append(c)
            for s in [
                s
                for s in todo
                if cells_by_label[s]["area"] == c["area"]
                and abs(cells_by_label[s]["row"] - c["row"])
                + abs(cells_by_label[s]["col"] - c["col"])
                == 1
            ]:
                todo.remove(s)
                stack.append(s)
        yield sorted(members, key=lambda c: (c["row"], c["col"]))


def bounds(group):
    r0, r1 = min(c["row"] for c in group), max(c["row"] for c in group)
    c0, c1 = min(c["col"] for c in group), max(c["col"] for c in group)
    return r0, c0, r1 - r0 + 1, c1 - c0 + 1


def is_rectangle(group):
    _, _, h, w = bounds(group)
    return len(group) == h * w


def area_adjacency(observation):
    scene = observation["scene"]
    grid = {(c["row"], c["col"]): c["area"] for c in scene["cells"]}
    pairs = set()
    for (r, c), a in grid.items():
        for dr, dc in ((0, 1), (1, 0)):
            b = grid.get((r + dr, c + dc))
            if b is not None and b != a:
                pairs.add((min(a, b), max(a, b)))
    return pairs


def colour_areas(observation, tints):
    """DSATUR graph colouring: touching areas get tints as far apart as the palette allows."""
    areas = [a["id"] for a in observation["scene"]["areas"]]
    neighbours = {a: set() for a in areas}
    for a, b in area_adjacency(observation):
        neighbours[a].add(b)
        neighbours[b].add(a)
    chosen = {}
    while len(chosen) < len(areas):
        pending = [a for a in areas if a not in chosen]
        area = max(
            pending,
            key=lambda a: (
                len({chosen[n] for n in neighbours[a] if n in chosen}),
                len(neighbours[a]),
                -a,
            ),
        )
        used = [tints[chosen[n]] for n in neighbours[area] if n in chosen]
        taken = {chosen[n] for n in neighbours[area] if n in chosen}
        everywhere = set(chosen.values())
        preferred = area % len(tints)

        def gap(i):
            return min((delta_e(tints[i], u) for u in used), default=100.0)

        options = [i for i in range(len(tints)) if i not in taken] or list(
            range(len(tints))
        )
        # Keep the theme's own order when it is already distinct enough from the neighbours;
        # otherwise prefer tints not yet used anywhere, then the largest colour gap.
        if preferred in options and gap(preferred) >= MIN_NEIGHBOUR_GAP:
            chosen[area] = preferred
        else:
            chosen[area] = max(
                options,
                key=lambda i: (
                    gap(i) >= MIN_NEIGHBOUR_GAP,
                    i not in everywhere,
                    gap(i),
                    -abs(i - preferred),
                ),
            )
    return chosen


def wall_runs(observation):
    """Every room boundary as maximal straight runs: [(x1, y1, x2, y2)]."""
    horizontal, vertical = {}, {}
    for c in observation["scene"]["cells"]:
        x, y = origin(c)
        for wall in c["walls"]:
            if wall == "north":
                horizontal.setdefault(y, set()).add(x)
            elif wall == "south":
                horizontal.setdefault(y + CELL, set()).add(x)
            elif wall == "west":
                vertical.setdefault(x, set()).add(y)
            else:
                vertical.setdefault(x + CELL, set()).add(y)
    runs = []
    for y, xs in sorted(horizontal.items()):
        for start, stop in _spans(sorted(xs)):
            runs.append((start, y, stop + CELL, y))
    for x, ys in sorted(vertical.items()):
        for start, stop in _spans(sorted(ys)):
            runs.append((x, start, x, stop + CELL))
    return runs


def _spans(values):
    start = prev = values[0]
    for v in values[1:]:
        if v != prev + CELL:
            yield start, prev
            start = v
        prev = v
    yield start, prev


def is_outer(run, observation):
    width, height = dimensions(observation)
    x1, y1, x2, y2 = run
    return (y1 == y2 and y1 in (PAD, height - PAD)) or (
        x1 == x2 and x1 in (PAD, width - PAD)
    )


def door_geometry(observation, door):
    cells = by_label(observation)
    ca, cb = cells[door[0]], cells[door[1]]
    x = PAD + (ca["col"] + cb["col"] + 1) * CELL / 2
    y = PAD + (ca["row"] + cb["row"] + 1) * CELL / 2
    vertical_wall = ca["row"] == cb["row"]
    return x, y, vertical_wall
