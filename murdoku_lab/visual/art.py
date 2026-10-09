"""Original flat vector artwork. Every export and the interactive board uses these functions.

No remote fonts, bitmap dependencies or official-game artwork. Geometry is read only from
the public observation; illustration can never access the hidden solution.
"""

from html import escape
import math
import textwrap

INK = "#334b42"
PAPER = "#fafaf3"
CELL = 100
PAD = 40


def esc(value):
    return escape(str(value), quote=True)


def txt(x, y, text, size=13, fill=INK, **attrs):
    extra = " ".join(f'{k.replace("_", "-")}="{esc(v)}"' for k, v in attrs.items())
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" {extra}>{esc(text)}</text>'


def portrait_inner(index, victim=False):
    """Six distinct faces; symbol badges remain the authoritative identity on large casts."""
    i = index % 8
    bg = (
        "#f0cf9e",
        "#d4dfeb",
        "#dae4ba",
        "#eee0b0",
        "#e8d8e7",
        "#d5e1df",
        "#e3d9c3",
        "#e1e2ed",
    )[i]
    skin = (
        "#e6af89",
        "#dfb696",
        "#9a6249",
        "#edc2a4",
        "#d9a17d",
        "#d7b696",
        "#c49171",
        "#e9ba9f",
    )[i]
    coat = (
        "#b65f44",
        "#546e8c",
        "#56765c",
        "#b68b44",
        "#846079",
        "#546f6b",
        "#917341",
        "#6b6f9a",
    )[i]
    hair = (
        "#804832",
        "#584337",
        "#353b31",
        "#d6d4bc",
        "#363d3c",
        "#777c73",
        "#3f322e",
        "#ad8060",
    )[i]
    o = [f'<circle cx="50" cy="50" r="48" fill="{bg}"/>']
    if i in (0, 4, 6):
        o.append(f'<path d="M25 48Q19 12 49 12Q79 11 76 50L79 73H21Z" fill="{hair}"/>')
    o.append(f'<path d="M14 99Q12 72 35 69L64 69Q88 73 88 99Z" fill="{coat}"/>')
    o.append(
        f'<path d="M40 61H61V75L50 82 39 74Z" fill="{skin}" stroke="{INK}" stroke-width="1.3"/>'
    )
    o.append(
        f'<ellipse cx="50" cy="43" rx="22" ry="27" fill="{skin}" stroke="{INK}" stroke-width="1.5"/>'
    )
    if i == 0:
        o.append(
            f'<path d="M27 40Q19 10 49 11Q76 10 75 38L61 25Q52 36 27 40Z" fill="{hair}"/>'
        )
        o.append('<path d="m34 71 16 11-8 11-12-18m20 7 12 12 6-21" fill="#f0c56e"/>')
    elif i == 1:
        o.append(
            f'<path d="M28 39V28Q33 11 58 15Q74 18 73 37L66 25Q46 32 32 27Z" fill="{hair}"/>'
        )
        o.append(
            f'<path d="M41 57Q45 50 50 55Q57 50 61 57Q56 61 50 57Q45 61 41 57" fill="{hair}"/>'
        )
        o.append(
            f'<g fill="none" stroke="{INK}" stroke-width="2"><circle cx="40" cy="43" r="8"/><circle cx="61" cy="43" r="8"/><path d="M48 42h5M31 42l-5-1M70 42l5-1"/></g>'
        )
        o.append(
            '<path d="m34 72 13 12-6 9-12-19m18 10 18-13 4 9-14 13" fill="#e4e0cd"/><path d="m47 85 7 1 1 14H45Z" fill="#c48b53"/>'
        )
    elif i == 2:
        o.append(
            f'<path d="M26 39Q15 30 24 25Q18 16 31 15Q31 6 43 12Q51 5 58 13Q70 8 74 21Q83 28 73 39L65 30 57 32 51 27 43 32 33 28Z" fill="{hair}"/>'
        )
        o.append(
            '<path d="m35 72 15 9 15-9-3 22H37Z" fill="#f2d28a"/><path d="M50 82v17" stroke="#3b5944" stroke-width="2"/>'
        )
    elif i == 3:
        o.append(
            f'<path d="M28 38Q20 15 41 14Q59 3 72 24L73 38 65 30Q44 34 31 25Z" fill="{hair}"/>'
        )
        o.append(
            f'<path d="m28 47 9 8 13 3 14-4 8-8Q73 70 51 75Q31 71 28 47" fill="{hair}"/>'
        )
        o.append(
            f'<path d="M44 60q7 4 13-1" fill="none" stroke="{INK}" stroke-width="1.3"/>'
        )
        o.append(
            '<path d="m34 74 15 8 15-8-3 22H38Z" fill="#e9e4d2"/><path d="m49 81-10 8 11 3 10-4Z" fill="#637c70"/>'
        )
    elif i == 4:
        o.append(
            f'<path d="M25 45Q23 11 52 12Q79 10 76 54L69 48 64 27 31 40 29 58 23 56Z" fill="{hair}"/>'
        )
        o.append(
            '<circle cx="30" cy="55" r="3" fill="#e7bd64"/><circle cx="71" cy="55" r="3" fill="#e7bd64"/><path d="M36 73q14 21 29-1" fill="none" stroke="#e5d6c0" stroke-width="3"/>'
        )
    else:
        o.append(
            f'<path d="M28 38Q23 16 43 15Q63 10 73 28L73 38 65 26 55 31 35 29Z" fill="{hair}"/>'
        )
        o.append(
            '<path d="m35 71 15 11 15-11-3 27H38Z" fill="#e6dec7"/><path d="m46 81 7 1 4 18H43Z" fill="#9e7257"/>'
        )
    o.extend(
        [
            f'<path d="m34 36 10-1m13 0 9 2" stroke="{INK}" stroke-width="1.8" stroke-linecap="round" fill="none"/>',
            f'<circle cx="40" cy="44" r="1.7" fill="{INK}"/><circle cx="60" cy="44" r="1.7" fill="{INK}"/>',
            '<path d="m50 45-2 7h4" fill="none" stroke="#9b6c52" stroke-width="1.4" stroke-linecap="round"/>',
        ]
    )
    if i not in (1, 3):
        o.append(
            f'<path d="M45 59q5 3 10-1" fill="none" stroke="{INK}" stroke-width="1.4" stroke-linecap="round"/>'
        )
    # Outline and clipping are native vectors, deterministic across raster exports.
    o.append(
        f'<circle cx="50" cy="50" r="48" fill="none" stroke="{INK}" stroke-width="1.5"/>'
    )
    return "".join(o)


def portrait_svg(index, victim=False):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">'
        f'<defs><clipPath id="face-clip"><circle cx="50" cy="50" r="48"/></clipPath></defs>'
        f'<g clip-path="url(#face-clip)">{portrait_inner(index, victim)}</g></svg>'
    )


def prop_svg(kind):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">{prop_shape(kind,100,100)}</svg>'


def prop_shape(kind, w, h, name="", *, pack=None, asset=None):
    """Draw within a prop's exact footprint, with a quiet flat offset shadow."""
    if pack == "fluent":
        from murdoku_lab.visual.asset_catalog import prop_image

        image = prop_image(asset or kind, w, h)
        if image is not None:
            return image
    # Geometry is local to a 100x100 drawing, stretched only for rectangular multi-cell props.
    base = f'<g transform="scale({w / 100:.5f} {h / 100:.5f})" stroke="{INK}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round">'
    if kind in ("table", "bed", "carpet", "car", "golf_cart"):
        if kind == "table":
            inner = '<rect x="13" y="29" width="78" height="53" rx="13" fill="#334b4215" stroke="none"/><rect x="9" y="22" width="78" height="55" rx="13" fill="#bb835b"/><rect x="15" y="28" width="66" height="43" rx="9" fill="#d4a376"/><path d="M20 61h55M33 34h23" stroke="#ac7954"/><ellipse cx="42" cy="45" rx="12" ry="10" fill="#f3ebd0"/><ellipse cx="62" cy="51" rx="7" ry="6" fill="#758b6d"/>'
        elif kind == "carpet":
            inner = '<path d="M7 23H94M7 31H94M7 39H94M7 47H94M7 55H94M7 63H94M7 71H94M7 79H94" stroke="#a6856c"/><rect x="12" y="16" width="76" height="69" rx="3" fill="#b96f52"/><rect x="18" y="22" width="64" height="57" rx="1" fill="#d99169" stroke="#e6bb85"/><path d="m50 34 17 17-17 17-17-17Z" fill="#f0cc8d" stroke="none"/><path d="m50 42 9 9-9 9-9-9Z" fill="#809080" stroke="none"/>'
        elif kind == "bed":
            inner = '<rect x="18" y="15" width="64" height="74" rx="6" fill="#bd956f"/><rect x="23" y="20" width="54" height="63" rx="4" fill="#f4ebd8"/><rect x="29" y="26" width="42" height="18" rx="6" fill="#fffdf1"/><path d="M23 47H77V82H23Z" fill="#9bafad"/><path d="M30 53H70" stroke="#e6e6cf"/>'
        else:
            inner = '<rect x="10" y="22" width="80" height="61" rx="22" fill="#829c8d"/><path d="M32 24H65L73 40H23Z" fill="#dbe2d1"/><path d="M23 61H75L67 77H32Z" fill="#dbe2d1"/><path d="M12 36h9m58 0h10M12 69h9m58 0h10" stroke="#ead9ad" stroke-width="4"/>'
    elif kind in ("plant", "tree", "shrub", "palm", "flowers"):
        if kind == "flowers":
            inner = '<path d="m30 56 6 25h31l6-25Z" fill="#c8956d"/><path d="M41 62 36 35m16 25 1-35m7 36 10-19" fill="none" stroke="#688057" stroke-width="3"/>'
            for x, y, color in (
                (34, 33, "#bd6f73"),
                (54, 27, "#e7bf5f"),
                (70, 39, "#d79181"),
            ):
                inner += f'<g fill="{color}" stroke-width="1.3"><circle cx="{x-6}" cy="{y}" r="6"/><circle cx="{x+6}" cy="{y}" r="6"/><circle cx="{x}" cy="{y-6}" r="6"/><circle cx="{x}" cy="{y+6}" r="6"/><circle cx="{x}" cy="{y}" r="4" fill="#f7d98f"/></g>'
        elif kind == "tree":
            inner = '<ellipse cx="51" cy="79" rx="28" ry="10" fill="#53694815" stroke="none"/><path d="M44 56h13l3 24H40Z" fill="#b18b62"/><path d="M22 50Q9 35 28 27Q23 12 42 16Q52 3 67 18Q84 13 84 35Q99 51 81 62Q72 77 57 64Q33 77 27 61Q14 62 22 50Z" fill="#809774"/><path d="m40 31 12 22 13-21m-13 21 0 13" fill="none" stroke="#536e57"/>'
        elif kind == "shrub":
            inner = '<path d="M22 73Q8 65 19 49Q13 34 30 34Q30 19 47 28Q62 14 71 31Q90 32 82 48Q97 64 80 76Z" fill="#809575"/><path d="M31 52q10-9 15 3m8-14q8 0 8 8m-10 15q9-8 14-1" stroke="#aabd88" fill="none"/>'
            inner += '<circle cx="33" cy="44" r="5" fill="#cb8c81"/><circle cx="66" cy="57" r="6" fill="#d99b8a"/>'
        elif kind == "palm":
            inner = '<path d="m46 42-7 42h17l-5-42" fill="#bd9669"/><path d="M49 40Q19 6 12 33Q27 27 49 40Q36 4 61 9Q57 19 49 40Q72 3 89 29Q70 27 49 40Q86 27 84 57Q68 42 49 40Q14 31 16 59Q34 40 49 40" fill="#77936c"/>'
        else:
            inner = '<path d="m32 58 6 26h25l7-26Z" fill="#cd9b78"/><path d="M30 58h42v8H30Z" fill="#e1b695"/><path d="M50 58V27" fill="none"/><path d="M50 43Q25 50 22 29Q43 21 50 43ZM51 34Q53 12 75 19Q79 39 51 43ZM48 54Q23 66 16 43Q31 34 48 54ZM53 56Q68 35 83 47Q75 69 53 56Z" fill="#809b6c"/>'
    elif kind == "chair":
        inner = '<ellipse cx="52" cy="76" rx="27" ry="8" fill="#334b4215" stroke="none"/><path d="M26 43 23 79m48-36 5 36" stroke="#876449" stroke-width="5"/><rect x="22" y="40" width="54" height="34" rx="10" fill="#bc8f62"/><rect x="27" y="38" width="44" height="27" rx="8" fill="#e2c28d"/><path d="M22 45V29Q22 20 31 20H66Q76 20 76 29v16Z" fill="#b68759"/><path d="M30 28H67" stroke="#dcc19b"/>'
    elif kind == "shelf":
        inner = '<rect x="11" y="17" width="79" height="68" rx="3" fill="#a77e58"/><rect x="17" y="22" width="67" height="57" rx="1" fill="#d6b28b"/><path d="M15 51H86" stroke-width="4"/>'
        for x, y, h2, col in (
            (22, 29, 18, "#819a85"),
            (34, 26, 21, "#d49079"),
            (47, 30, 17, "#c6b268"),
            (61, 27, 20, "#91a5ae"),
            (21, 57, 17, "#cc9d67"),
            (39, 56, 18, "#90a19c"),
            (52, 59, 15, "#c88c7e"),
            (67, 57, 17, "#ddca9c"),
        ):
            inner += f'<rect x="{x}" y="{y}" width="9" height="{h2}" rx="1" fill="{col}" stroke-width="1.2"/>'
    elif kind == "piano":
        inner = '<path d="M20 76V38Q22 14 49 17L75 25Q87 31 79 47L72 76Z" fill="#56655d"/><path d="M27 66h40v15H27Z" fill="#f3ead0"/><path d="M33 66v15m7-15v15m7-15v15m7-15v15m7-15v15" stroke-width="1.3"/><path d="M28 40q21-19 41 0" fill="none" stroke="#93a091"/>'
    elif kind in ("flag", "tee"):
        inner = '<ellipse cx="48" cy="79" rx="24" ry="8" fill="#729274" stroke="none"/><ellipse cx="46" cy="76" rx="10" ry="4" fill="#3f584a"/><path d="M47 19v57" stroke-width="3"/><path d="M49 20 78 30 49 42Z" fill="#bd7355"/>'
    elif kind in ("water", "sand"):
        col = "#91bec4" if kind == "water" else "#e1cd9e"
        inner = f'<path d="M13 45Q13 21 41 25Q57 10 76 30Q95 39 82 65Q59 87 26 73Q8 64 13 45Z" fill="{col}"/>'
        inner += '<path d="M24 48q10 6 19 0m12 13q10 6 19 0m-28-26q10 6 19 0" fill="none" stroke="#e4f0e4"/>'
    elif kind in ("statue", "boulder"):
        inner = '<path d="M17 70 26 38 47 20 69 27 84 66 66 80H35Z" fill="#adb6ac"/><path d="m47 20-7 35 26 25m-26-25 42 10" fill="none" stroke="#8b9a91"/>'
        if kind == "statue":
            inner = '<path d="M24 71h52v13H24Z" fill="#adb6ac"/><path d="m35 70 5-27h21l7 27Z" fill="#c2c8b9"/><circle cx="51" cy="29" r="15" fill="#c2c8b9"/><path d="M49 25v9h5m-5 7h10" stroke="#899c8d" fill="none"/>'
    elif kind in ("crate", "box", "barrel"):
        inner = '<rect x="22" y="24" width="55" height="58" rx="6" fill="#bc956c"/><path d="M25 38h49M25 66h49M37 27v52m24-52v52" fill="none" stroke="#947857"/>'
    elif kind == "tv":
        inner = '<rect x="15" y="24" width="70" height="48" rx="7" fill="#6d7d74"/><rect x="21" y="30" width="57" height="35" rx="5" fill="#b5c9c3"/><path d="m34 18 13 6 15-8M50 72v9m-18 0h37" fill="none"/>'
    elif kind == "void":
        inner = '<path d="M25 25 75 75M75 25 25 75" stroke="#8a9185" stroke-width="3"/>'
    else:
        # Unknown board-local props remain labelled, never guessed from a themed noun.
        inner = '<rect x="14" y="24" width="72" height="52" rx="10" fill="#d4c6ae"/><path d="m38 43 12-7 12 7v15l-12 7-12-7Z" fill="#f1e7ce"/>'
    return base + inner + "</g>"


def connected_components(cells, by_label):
    todo = set(cells)
    while todo:
        start = min(todo)
        todo.remove(start)
        stack, members = [start], []
        while stack:
            label = stack.pop()
            c = by_label[label]
            members.append(c)
            neighbours = [
                s
                for s in todo
                if by_label[s]["area"] == c["area"]
                and abs(by_label[s]["row"] - c["row"])
                + abs(by_label[s]["col"] - c["col"])
                == 1
            ]
            for s in neighbours:
                todo.remove(s)
                stack.append(s)
        yield members


def dimensions(observation):
    return (
        observation["scene"]["width"] * CELL + PAD * 2,
        observation["scene"]["height"] * CELL + PAD * 2,
    )


def scene_svg(observation, *, style="art", selected=None, focus_cells=()):
    if style not in ("art", "diagram", "fluent", "classic"):
        raise ValueError("style must be art, diagram, fluent or classic")
    scene = observation["scene"]
    width, height = dimensions(observation)
    cells, areas = scene["cells"], {a["id"]: a for a in scene["areas"]}
    by_label = {c["cell"]: c for c in cells}
    props = {p["id"]: p for p in scene["props"]}
    cast = {p["id"]: p for p in observation["people"]}
    selected_cells = set(observation["marks"].get(selected, ())) | set(focus_cells)
    root = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" class="scene-svg" data-style="{style}" data-revision="{observation["revision"]}" role="group" aria-label="{esc(observation["setting"])}; {scene["width"]} by {scene["height"]} board">',
        '<defs><pattern id="wood" width="100" height="100" patternUnits="userSpaceOnUse"><path d="M0 25H100M0 75H100M45 0V25M76 25V75M30 75V100" fill="none" stroke="#6c644b" stroke-width="1" opacity=".08"/></pattern>',
        '<pattern id="tile" width="25" height="25" patternUnits="userSpaceOnUse"><path d="M25 0H0V25" fill="none" stroke="#6c644b" stroke-width="1" opacity=".12"/><circle cx="12.5" cy="12.5" r="1.5" fill="#6c644b" opacity=".1"/></pattern>',
        '<pattern id="grass" width="32" height="32" patternUnits="userSpaceOnUse"><path d="m5 16 2-4 3 4m14 9 2-5 2 5" fill="none" stroke="#426d4e" stroke-width="1.4" opacity=".16"/></pattern>',
        '<pattern id="water" width="40" height="28" patternUnits="userSpaceOnUse"><path d="M3 8q7 6 14 0m8 14q7 6 14 0" fill="none" stroke="#eff5eb" stroke-width="2" opacity=".55"/></pattern>',
        '<pattern id="sand" width="24" height="24" patternUnits="userSpaceOnUse"><circle cx="5" cy="6" r="1.3" fill="#9b885d" opacity=".4"/><circle cx="18" cy="19" r="1" fill="#9b885d" opacity=".3"/></pattern>',
        '<clipPath id="token-clip"><circle cx="50" cy="50" r="48"/></clipPath></defs>',
        "<style>text{font-family:Arial,sans-serif} .cell-hit{cursor:pointer;outline:none}.cell-hit:hover .hit-box{fill:#ffffff30;stroke:#507768;stroke-width:2}.cell-hit:focus .hit-box{stroke:#b56c36;stroke-width:4;fill:#ffffff20}.board-decoration{pointer-events:none}</style>",
        f'<rect width="{width}" height="{height}" rx="12" fill="{PAPER}"/>',
    ]
    root.append('<g class="board-decoration">')
    # Area fills form one continuous map; the fine cell grid is subordinate to room walls.
    for cell in cells:
        x, y = PAD + cell["col"] * CELL, PAD + cell["row"] * CELL
        color = areas[cell["area"]]["color"]
        if style == "classic":
            palette = ("#ffe095", "#cce8b4", "#f0c5ad", "#c9c0ed", "#b6dedc", "#f5c6db")
            color = palette[list(areas).index(cell["area"]) % len(palette)]
        t = cell["terrain"]
        if t == "water":
            color = "#a2cbd0"
        elif t == "sand":
            color = "#e6d8b0"
        elif t == "rough":
            color = "#adbf96"
        root.append(f'<rect x="{x}" y="{y}" width="100" height="100" fill="{color}"/>')
        if style in ("art", "classic"):
            pattern = {
                "floor": "wood",
                "tile": "tile",
                "water": "water",
                "sand": "sand",
                "fairway": "grass",
                "rough": "grass",
            }.get(t, "wood")
            root.append(
                f'<rect x="{x}" y="{y}" width="100" height="100" fill="url(#{pattern})"/>'
            )
        root.append(
            f'<rect x="{x}" y="{y}" width="100" height="100" fill="none" stroke="{"#292929" if style == "classic" else "#51624d"}" stroke-opacity="{".8" if style == "classic" else ".16"}" stroke-width="{3 if style == "classic" else 1}"/>'
        )
    # Merge only filled rectangular connected footprints. Never stretch an illustration over
    # a hole, an unrelated cell, a disconnected instance or an area boundary.
    for prop in scene["props"]:
        if style == "diagram":
            for label in prop["cells"]:
                c = by_label[label]
                x, y = PAD + c["col"] * CELL, PAD + c["row"] * CELL
                root.append(
                    f'<rect x="{x+8}" y="{y+33}" width="84" height="33" rx="5" fill="#ffffffbb" stroke="#6b7563" stroke-width="1"/>'
                )
                short = prop["name"] if len(prop["name"]) <= 14 else prop["id"]
                root.append(
                    txt(
                        x + 50,
                        y + 54,
                        short,
                        min(13, 95 / max(6, len(short)) * 1.5),
                        text_anchor="middle",
                    )
                )
            continue
        for group in connected_components(prop["cells"], by_label):
            r0, r1 = min(c["row"] for c in group), max(c["row"] for c in group)
            c0, c1 = min(c["col"] for c in group), max(c["col"] for c in group)
            merge = len(group) == (r1 - r0 + 1) * (c1 - c0 + 1) and prop["art"] in (
                "table",
                "carpet",
                "bed",
                "car",
                "golf_cart",
                "water",
                "sand",
                "generic",
            )
            spans = (
                [(r0, c0, r1 - r0 + 1, c1 - c0 + 1)]
                if merge
                else [(c["row"], c["col"], 1, 1) for c in group]
            )
            for r, c, h, w in spans:
                x, y = PAD + c * CELL, PAD + r * CELL
                root.append(
                    f'<g data-prop="{esc(prop["id"])}" transform="translate({x+10} {y+15})">{prop_shape(prop["art"], w*CELL-20, h*CELL-22, prop["name"], pack="fluent" if style == "fluent" or prop.get("asset") else None, asset=prop.get("asset"))}</g>'
                )
                if prop["art"] == "generic":
                    label = prop["id"][:13]
                    root.append(
                        txt(
                            x + w * CELL / 2,
                            y + 15 + (h * CELL - 22) * 0.83,
                            label,
                            11,
                            text_anchor="middle",
                        )
                    )
    # Walls are a partition boundary even at a doorway; the opening is shown explicitly.
    edges = set()
    for c in cells:
        x, y = PAD + c["col"] * CELL, PAD + c["row"] * CELL
        for wall in c["walls"]:
            edges.add(
                {
                    "north": (x, y, x + CELL, y),
                    "south": (x, y + CELL, x + CELL, y + CELL),
                    "west": (x, y, x, y + CELL),
                    "east": (x + CELL, y, x + CELL, y + CELL),
                }[wall]
            )
    for x1, y1, x2, y2 in sorted(edges):
        root.append(
            f'<path d="M{x1} {y1}L{x2} {y2}" fill="none" stroke="{"#222222" if style == "classic" else "#526253"}" stroke-width="{7 if style == "classic" else 5.5}" stroke-linecap="round"/>'
        )
        root.append(
            f'<path d="M{x1} {y1}L{x2} {y2}" fill="none" stroke="#faf6dd" stroke-width="1.2" stroke-opacity=".7"/>'
        )
    for a, b in scene["doors"]:
        ca, cb = by_label[a], by_label[b]
        x = PAD + (ca["col"] + cb["col"] + 1) * CELL / 2
        y = PAD + (ca["row"] + cb["row"] + 1) * CELL / 2
        if ca["row"] == cb["row"]:
            path, cross = f"M{x} {y-16}V{y+16}", f"M{x-6} {y-16}h12M{x-6} {y+16}h12"
        else:
            path, cross = f"M{x-16} {y}H{x+16}", f"M{x-16} {y-6}v12M{x+16} {y-6}v12"
        root.append(
            f'<g data-door="{esc(a)}:{esc(b)}"><path d="{path}" stroke="{PAPER}" stroke-width="8"/><path d="{path}" stroke="#b58f5f" stroke-width="2" stroke-dasharray="3 3"/><path d="{cross}" stroke="#526253" stroke-width="2"/></g>'
        )
    # One label per connected patch. Put it at the first horizontal run, not at the centroid
    # (which can be outside a concave room).
    for area in scene["areas"]:
        if style == "diagram":
            continue
        members = [c["cell"] for c in cells if c["area"] == area["id"]]
        for group in connected_components(members, by_label):
            r = min(c["row"] for c in group)
            run = sorted(c["col"] for c in group if c["row"] == r)
            c0 = run[0]
            c1 = c0
            while c1 + 1 in run:
                c1 += 1
            available = (c1 - c0 + 1) * CELL - 18
            full = f'{area["number"]:02d}  {area["name"].upper()}'
            if len(full) * 7.3 + 16 > available:
                full = f'{area["number"]:02d}'
            tw = min(available, len(full) * 7.3 + 16)
            x, y = PAD + c0 * CELL + 8, PAD + r * CELL + 6
            root.append(
                f'<rect x="{x}" y="{y}" width="{tw:.1f}" height="19" rx="3" fill="{PAPER}" fill-opacity=".91"/>'
            )
            root.append(
                txt(x + 8, y + 13.5, full, 10.5, font_weight="700", letter_spacing=".9")
            )
    for c in cells:
        x, y = PAD + c["col"] * CELL, PAD + c["row"] * CELL
        label = c["cell"]
        occupants = [
            p for p, value in observation["placements"].items() if value == label
        ]
        marks = [p for p, values in observation["marks"].items() if label in values]
        if label in selected_cells:
            root.append(
                f'<rect x="{x+4}" y="{y+4}" width="92" height="92" rx="5" fill="#f4f3b642" stroke="#356e55" stroke-width="3" stroke-dasharray="5 3"/>'
            )
        if len(occupants) == 1:
            person = cast[occupants[0]]
            ring = "#c6844f" if selected == person["id"] else person["color"]
            root.append(
                f'<circle cx="{x+50}" cy="{y+55}" r="32" fill="{PAPER}" stroke="{ring}" stroke-width="3"/>'
            )
            root.append(
                f'<g transform="translate({x+20} {y+25}) scale(.6)" clip-path="url(#token-clip)">{portrait_inner(person["portrait"], person["victim"])}</g>'
            )
            root.append(
                f'<rect x="{x+63}" y="{y+67}" width="21" height="21" rx="6" fill="{person["color"]}" stroke="{PAPER}" stroke-width="1.5"/>'
            )
            root.append(
                txt(
                    x + 73.5,
                    y + 82,
                    person["id"],
                    13,
                    "#fffdf3",
                    text_anchor="middle",
                    font_weight="700",
                )
            )
        elif occupants:
            # Upstream scratchpad permits wrong claims. Show ALL collided identities.
            root.append(
                f'<rect x="{x+8}" y="{y+31}" width="84" height="39" rx="7" fill="#f7e1d7" stroke="#b65f49" stroke-width="2"/>'
            )
            joined = " · ".join(occupants)
            root.append(
                txt(
                    x + 50,
                    y + 54,
                    joined,
                    min(15, 125 / max(1, len(joined))),
                    "#8c4539",
                    text_anchor="middle",
                    font_weight="700",
                )
            )
        if marks:
            shown = " ".join(marks)
            root.append(
                f'<rect x="{x+6}" y="{y+26 if occupants else y+47}" width="88" height="18" rx="4" fill="#faf9ecdf"/>'
            )
            root.append(
                txt(
                    x + 50,
                    y + (39 if occupants else 60),
                    shown,
                    min(13, 130 / max(1, len(shown))),
                    text_anchor="middle",
                    font_weight="700",
                )
            )
        if not c["standable"]:
            root.append(
                f'<circle cx="{x+12}" cy="{y+87}" r="6" fill="{PAPER}" fill-opacity=".9" stroke="#926953" stroke-width="1"/><path d="m{x+9.5} {y+84.5} 5 5m0-5-5 5" stroke="#926953" stroke-width="1.4"/>'
            )
        if style == "diagram":
            root.append(
                txt(
                    x + 9,
                    y + 17,
                    f'R{c["area"]+1:02d}',
                    10,
                    fill="#455f50",
                    font_weight="700",
                )
            )
            if c["terrain"] != "floor":
                root.append(txt(x + 50, y + 80, c["terrain"], 10, text_anchor="middle"))
    for c in range(scene["width"]):
        root.append(
            txt(
                PAD + c * CELL + 50,
                25,
                chr(97 + c).upper(),
                13,
                font_weight="700",
                text_anchor="middle",
            )
        )
    for r in range(scene["height"]):
        root.append(
            txt(
                20,
                PAD + r * CELL + 56,
                r + 1,
                13,
                font_weight="700",
                text_anchor="middle",
            )
        )
    root.append("</g>")
    # Transparent accessible hit areas are the only interaction layer. They do not alter geometry.
    for c in cells:
        x, y = PAD + c["col"] * CELL, PAD + c["row"] * CELL
        who = [
            cast[p]["name"]
            for p, k in observation["placements"].items()
            if k == c["cell"]
        ]
        details = f'{c["cell"]}; area {c["area"]+1}, {areas[c["area"]]["name"]}; {c["terrain"]}; '
        if c["prop"]:
            details += props[c["prop"]]["name"] + "; "
        details += "standable" if c["standable"] else "blocked"
        if who:
            details += "; placed: " + ", ".join(who)
        root.append(
            f'<g class="cell-hit" data-cell="{c["cell"]}" role="button" tabindex="0" aria-label="{esc(details)}"><title>{esc(details)}</title><rect class="hit-box" x="{x+3}" y="{y+3}" width="94" height="94" rx="3" fill="transparent"/>'
        )
        root.append(
            f'<rect x="{x+72}" y="{y+80}" width="23" height="16" rx="3" fill="{PAPER}" fill-opacity=".78" pointer-events="none"/>'
        )
        root.append(
            txt(
                x + 83.5,
                y + 92,
                c["cell"],
                10,
                fill="#425748",
                text_anchor="middle",
                pointer_events="none",
            )
        )
        root.append("</g>")
    root.append("</svg>")
    return "".join(root)


def board_svg(observation, *, style="art"):
    """Board and visual keys for image + textual-clue queries. No clue sidebar."""
    bw, bh = dimensions(observation)
    props = observation["scene"]["props"]
    terrains = observation["scene"]["terrains"]
    columns = max(2, min(4, int(bw // 230)))
    slot = bw / columns
    wrap = max(14, int((slot - 70) / 7))
    row_height = max(
        [78] + [46 + 17 * len(textwrap.wrap(p["name"], wrap)) for p in props]
    )
    key_y = bh + 37
    terrain_y = key_y + math.ceil(len(props) / columns) * row_height + 25
    height = terrain_y + math.ceil(len(terrains) / columns) * 55 + 48
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{bw}" height="{height}" viewBox="0 0 {bw} {height}">',
        "<style>text{font-family:Arial,sans-serif}</style>",
        f'<rect width="{bw}" height="{height}" fill="{PAPER}"/>',
        scene_svg(observation, style=style),
        txt(
            24,
            bh + 16,
            "OBJECT KEY · crossed squares are blocked",
            15,
            font_weight="700",
        ),
    ]
    for i, prop in enumerate(props):
        x, y = 22 + (i % columns) * slot, key_y + (i // columns) * row_height
        out.append(
            f'<g transform="translate({x} {y})">{prop_shape(prop["art"], 45, 45, pack="fluent" if style == "fluent" or prop.get("asset") else None, asset=prop.get("asset"))}</g>'
        )
        name = (
            f'{prop["id"]} · {prop["name"]}'
            if prop["art"] == "generic"
            else prop["name"]
        )
        lines = textwrap.wrap(name, wrap)
        for j, line in enumerate(lines):
            out.append(txt(x + 57, y + 16 + j * 17, line, 14))
        out.append(
            txt(
                x + 57,
                y + 18 + len(lines) * 17,
                "standable object" if prop["standable"] else "blocking object",
                12,
                fill="#657363",
            )
        )
    out.append(
        txt(
            24,
            terrain_y - 12,
            "GROUND KEY · separate from objects",
            15,
            font_weight="700",
        )
    )
    for i, terrain in enumerate(terrains):
        x, y = 24 + (i % columns) * slot, terrain_y + (i // columns) * 55
        color = {"water": "#a2cbd0", "sand": "#e6d8b0", "rough": "#adbf96"}.get(
            terrain["id"], "#e1e7d4"
        )
        pattern = {
            "floor": "wood",
            "tile": "tile",
            "water": "water",
            "sand": "sand",
            "fairway": "grass",
            "rough": "grass",
        }.get(terrain["id"], "wood")
        out.append(
            f'<rect x="{x}" y="{y}" width="39" height="30" rx="4" fill="{color}"/>'
            f'<rect x="{x}" y="{y}" width="39" height="30" rx="4" fill="url(#{pattern})"/>'
        )
        out.append(txt(x + 53, y + 13, terrain["name"], 14))
        out.append(
            txt(
                x + 53,
                y + 31,
                "standable ground" if terrain["standable"] else "blocked ground",
                12,
                fill="#657363",
            )
        )
    out.append(
        txt(
            24,
            height - 16,
            f'Board revision {observation["revision"]} · coordinates: column letter + row number',
            13,
            fill="#657363",
        )
    )
    return "".join(out) + "</svg>"


def observation_svg(observation, *, style="art", selected=None, focus_cells=()):
    """A complete visual-only task observation: board, legend, cast, rules and every clue.
    Unlike a board crop, this is sufficient to solve a case without a parallel JSON scene.
    """
    bw, bh = dimensions(observation)
    board_display = bw  # retain native cell resolution on large visual observations
    scale = board_display / bw
    left = board_display + 64
    side = 530
    width = left + side + 42
    wraps = [(c, textwrap.wrap(c["text"], width=51)) for c in observation["clues"]]
    clue_h = sum(51 + len(lines) * 22 for _, lines in wraps)
    cast_rows = math.ceil(len(observation["people"]) / 6)
    legend_rows = math.ceil(len(observation["scene"]["areas"]) / 3)
    key_columns = 3
    key_cell_width = board_display / key_columns
    key_wrap = max(12, int((key_cell_width - 60) / 6.2))
    key_row_height = max(
        [65]
        + [
            14
            * len(
                textwrap.wrap(
                    (
                        f'{p["id"]} · {p["name"]}'
                        if p["art"] == "generic"
                        else p["name"]
                    ),
                    key_wrap,
                )
            )
            + 28
            for p in observation["scene"]["props"]
        ]
    )
    prop_key_height = (
        math.ceil(len(observation["scene"]["props"]) / key_columns) * key_row_height
    )
    rule_height = max(
        400,
        110
        + sum(len(textwrap.wrap(rule, 57)) * 19 + 12 for rule in observation["rules"]),
    )
    # Props and terrain are named in the full image as well: a novel p10 illustration alone
    # cannot tell a visual-only solver which themed noun the clue refers to.
    height = max(
        int(
            200
            + bh * scale
            + cast_rows * 124
            + legend_rows * 30
            + 130
            + prop_key_height
        ),
        195 + clue_h + rule_height + len(observation["scene"]["terrains"]) * 30,
    )
    o = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>text{font-family:Arial,sans-serif}</style>",
        f'<rect width="{width}" height="{height}" fill="{PAPER}"/>',
        txt(
            38,
            39,
            "MURDOKU / THE ILLUSTRATED CASEBOOK",
            13,
            font_weight="700",
            letter_spacing="2",
        ),
        txt(38, 88, observation["title"], 32, font_family="Georgia, serif"),
        txt(38, 117, observation["goal"], 14),
        txt(
            38,
            151,
            f'{observation["scene"]["width"]} × {observation["scene"]["height"]}  ·  {len(observation["people"])} people  ·  {observation["variant"]}',
            13,
            fill="#697769",
        ),
        f'<g transform="translate(20 169) scale({scale:.6f})">{scene_svg(observation,style=style,selected=selected,focus_cells=focus_cells)}</g>',
    ]
    y = 185 + bh * scale
    for i, area in enumerate(observation["scene"]["areas"]):
        xx, yy = 41 + (i % 3) * (board_display / 3), y + (i // 3) * 29
        o.append(
            f'<rect x="{xx}" y="{yy-12}" width="14" height="14" rx="3" fill="{area["color"]}" stroke="#7f8b78" stroke-width=".5"/>'
        )
        o.append(txt(xx + 23, yy, f'{area["number"]:02d} {area["name"]}', 12))
    y += legend_rows * 30 + 24
    o.append(
        txt(
            41,
            y,
            "THE PEOPLE · LETTERS IDENTIFY EVERY TOKEN",
            11,
            font_weight="700",
            letter_spacing="1",
        )
    )
    for i, p in enumerate(observation["people"]):
        xx, yy = 38 + (i % 6) * (board_display / 6), y + 15 + (i // 6) * 124
        o.append(
            f'<g transform="translate({xx+13} {yy}) scale(.63)">{portrait_inner(p["portrait"],p["victim"])}</g>'
        )
        o.append(
            txt(
                xx + 44,
                yy + 81,
                f'{p["id"]} · {p["name"]}',
                12,
                text_anchor="middle",
                font_weight="700",
            )
        )
        label = "VICTIM" if p["victim"] else "SUSPECT"
        if p["tags"]:
            label += " / " + ", ".join(p["tags"])
        o.append(txt(xx + 44, yy + 97, label, 8, fill="#697769", text_anchor="middle"))
    o.append(f'<path d="M{left-17} 176V{height-30}" stroke="#d9dfd2"/>')
    o.append(
        txt(
            left + 10,
            193,
            "WITNESS STATEMENTS",
            12,
            font_weight="700",
            letter_spacing="1.7",
        )
    )
    yy = 223
    for clue, lines in wraps:
        o.append(
            txt(
                left + 10,
                yy,
                f'{clue["number"]:02d}',
                12,
                fill="#a8774e",
                font_weight="700",
            )
        )
        for line in lines:
            o.append(txt(left + 45, yy, line, 15))
            yy += 22
        yy += 29
    o.append(
        txt(
            left + 10,
            yy + 9,
            "RULES & SYMBOLS",
            12,
            font_weight="700",
            letter_spacing="1.5",
        )
    )
    yy += 39
    for rule in observation["rules"]:
        for line in textwrap.wrap(rule, 57):
            o.append(txt(left + 10, yy, line, 13, fill="#5b6f60"))
            yy += 19
        yy += 12
    key_y = y + cast_rows * 124 + 24
    o.append(txt(41, key_y, "OBJECT KEY", 11, font_weight="700", letter_spacing="1.5"))
    key_y += 24
    for i, prop in enumerate(observation["scene"]["props"]):
        px, py = (
            38 + (i % key_columns) * key_cell_width,
            key_y + (i // key_columns) * key_row_height,
        )
        o.append(
            f'<g transform="translate({px} {py-5})">{prop_shape(prop["art"],39,39)}</g>'
        )
        name = (
            f'{prop["id"]} · {prop["name"]}'
            if prop["art"] == "generic"
            else prop["name"]
        )
        lines = textwrap.wrap(name, key_wrap)
        for j, line in enumerate(lines):
            o.append(txt(px + 48, py + 11 + j * 14, line, 11.5))
        o.append(
            txt(
                px + 48,
                py + 11 + len(lines) * 14,
                "standable" if prop["standable"] else "blocked",
                9,
                fill="#7f8e77",
            )
        )
    yy += 20
    o.append(
        txt(left + 10, yy, "TERRAIN KEY", 12, font_weight="700", letter_spacing="1.5")
    )
    yy += 28
    for terrain in observation["scene"]["terrains"]:
        kind = terrain["id"]
        color = {"water": "#a2cbd0", "sand": "#e6d8b0", "rough": "#adbf96"}.get(
            kind, "#e1e7d4"
        )
        pattern = {
            "floor": "wood",
            "tile": "tile",
            "water": "water",
            "sand": "sand",
            "fairway": "grass",
            "rough": "grass",
        }.get(kind, "wood")
        o.append(
            f'<rect x="{left+12}" y="{yy-14}" width="24" height="20" rx="3" fill="{color}"/><rect x="{left+12}" y="{yy-14}" width="24" height="20" rx="3" fill="url(#{pattern})"/>'
        )
        o.append(
            txt(
                left + 55,
                yy,
                f'{terrain["name"]} · {"standable" if terrain["standable"] else "blocked"}',
                12,
            )
        )
        yy += 30
    o.append(
        txt(
            38,
            height - 30,
            f'Observation revision {observation["revision"]} · Cross = blocked · Letters = your pencil marks · No hidden solution included',
            11,
            fill="#657363",
        )
    )
    o.append("</svg>")
    return "".join(o)
