"""Render formal cases and themes as public text observations."""

from __future__ import annotations

import re

from murdoku_lab.core.atoms import COMPASS_WORDS, SPECS, Atom
from murdoku_lab.core.board import DEFAULT_TERRAIN, OBJECTS, TERRAINS
from murdoku_lab.core.instance import Case, Clue
from murdoku_lab.core.theme import Theme, canonical_theme


def cell_label(case: Case, k: int) -> str:
    r, c = case.scene.rc(k)
    return f"{chr(ord('a') + c)}{r + 1}"


def parse_cell(case: Case, s: str) -> int | None:
    s = s.strip().lower()
    if len(s) < 2 or not s[0].isalpha():
        return None
    c = ord(s[0]) - ord("a")
    try:
        r = int(s[1:]) - 1
    except ValueError:
        return None
    if not (0 <= c < case.scene.W and 0 <= r < case.scene.H):
        return None
    return case.scene.k(r, c)


# =============================================================================================
# Clue text
# =============================================================================================
def _area_phrase(label: str) -> str:
    parts = label.split()
    numbered = (
        len(parts) == 2
        and parts[0].lower() in {"area", "hole", "room", "cell"}
        and (any(c.isdigit() for c in parts[1]) or len(parts[1]) == 1)
    )
    return label if numbered or label.lower().startswith("the ") else "the " + label


_PAR = {"even": "偶数", "odd": "奇数"}
_SIDE = {"north": "北", "south": "南", "west": "西", "east": "东"}
_AXIS = {"row": "行", "column": "列"}


def render_atom(a: Atom, case: Case, th: Theme) -> str:
    s, spec = case.scene, SPECS[a.kind]
    who, other = th.name(a.holder), th.name(a.other) if a.other else ""
    noun = th.cast_noun

    # 短陈述式线索；每个主语都显式写出，避免复合线索里"另一只"存在句继承后面谓词。
    if a.kind == "in_corner":
        return f"{who}站在所处区域的墙角。"
    if a.kind == "not_in_corner":
        return f"{who}没有站在所处区域的墙角。"
    if a.kind == "alone":
        return f"{who}是独自一只——所在区域里没有别的{noun}。"
    if a.kind == "in_area":
        return f"{who}在{th.area(a['area'])}里。"
    if a.kind == "not_in_area":
        return f"{who}不在{th.area(a['area'])}里。"
    if a.kind == "area_empty":
        return f"{th.area(a['area'])}里一只{noun}都没有。"
    if a.kind == "area_no_parity":
        return f"{who}所在区域的编号是{_PAR[a['par']]}。"
    if a.kind == "on_grid_edge":
        return f"{who}站在棋盘的外边界。"
    if a.kind == "beside_terrain":
        return f"{who}在某{th.obj(a['ter'])}地面的格子旁边。"
    if a.kind == "beside" and a["obj"] == "flowers" and th.obj("flowers") == "flowers":
        return f"{who}在花旁边。"

    if a.kind in ("row_offset", "col_offset"):
        d = a["d"]
        n = abs(d)
        # 只约束行/列之差，明确写出来，避免读者误读成同一列/行。
        if a.kind == "row_offset":
            word = "下方" if d > 0 else "上方"
            return f"{who}正好在{other}{word} {n} 行（只比较行，不要求同列）。"
        word = "右侧" if d > 0 else "左侧"
        return f"{who}正好在{other}{word} {n} 列（只比较列，不要求同行）。"
    if a.kind == "compass":
        return f"{who}在{other}的{COMPASS_WORDS[(a['dr'], a['dc'])]}方向。"
    if a.kind == "in_areas":
        names = "或".join(th.area(x) for x in a["areas"])
        return f"{who}在以下区域之一：{names}。"
    if a.kind == "tag_in_area":
        return f"有一只{th.tag(a['tag'])}在{who}所在区域里。"
    if a.kind == "on_in_areas":
        names = "或".join(th.area(x) for x in a["areas"])
        obj = th.obj(a["obj"])
        return f"{who}在{names}里的一个{obj}上。"
    if a.kind == "area_no_offset":
        d = a["d"]
        if d == 0:
            return f"{who}和{other}在同一个区域。"
        word = "大" if d > 0 else "小"
        return f"{who}所在区域的编号比{other}{word} {abs(d)}。"
    if a.kind == "not_area_no_offset":
        d = a["d"]
        if abs(d) == 1:
            word = "之后" if d > 0 else "之前"
            return f"{who}所在区域的编号不是紧接在{other}{word}。"
        word = "大" if d > 0 else "小"
        return f"{who}所在区域的编号不比{other}{word} {abs(d)}。"
    if a.kind == "area_occupancy_parity":
        return f"每个编号为{_PAR[a['par']]}的区域里都有{_PAR[a['par']]}只{noun}（0 算偶数）。"

    # 每个声明的参数都留一个槽位，主题能给词的用主题词；side/axis/par 等英文枚举译成中文。
    fields = {"holder": who, "other": other, "cast_noun": noun}
    for name in spec.params:
        if name in fields:
            continue
        val = a[name]
        if name == "area":
            fields[name] = th.area(val)
        elif name == "areas":
            fields[name] = "或".join(th.area(x) for x in val)
        elif name == "obj":
            fields[name] = th.obj(val)
        elif name == "ter":
            fields[name] = th.obj(val)
        elif name == "tag":
            fields[name] = th.tag(val)
        elif name in ("row", "col"):
            fields[name] = val + 1
        elif name == "par":
            fields[name] = _PAR[val]
        elif name == "side":
            fields[name] = _SIDE[val]
        elif name == "axis":
            fields[name] = _AXIS[val]
        else:
            fields[name] = val
    return spec.template.format(**fields)


def render_clue(c: Clue, case: Case, th: Theme) -> str:
    parts = [render_atom(a, case, th) for a in c.atoms]
    if len(parts) == 1:
        return parts[0]
    # Each atom carries its own subject. Existential clauses such as
    # "Someone else in V's area ..." must not inherit V's later predicates.
    return " ".join(parts)


# =============================================================================================
# Scene text
# =============================================================================================
def render_scene(case: Case, th: Theme, *, solution: bool = False) -> str:
    s = case.scene
    at = {k: th.name(x)[:2] for x, k in case.solution.items()} if solution else {}
    # The commonest terrain is the *background* and is left unmarked, exactly as the reference game
    # leaves fairway unlabelled and paints only the sand, water and rough. Marking every cell makes a
    # 16x16 map unreadable and says nothing.
    from collections import Counter

    ground = (
        Counter(s.terrain_of).most_common(1)[0][0] if s.terrain_of else DEFAULT_TERRAIN
    )
    # A 16-wide board at 11 columns per cell is 176 characters and wraps in any terminal.
    width = 11 if s.W <= 9 else 8
    lines = ["     " + "".join(f"{chr(ord('a')+c):^{width}}" for c in range(s.W))]
    for r in range(s.H):
        row = [f"{r+1:>3}  "]
        for c in range(s.W):
            k = s.k(r, c)
            if k in at:
                token = f"[{at[k]}]"
            elif s.obj_of[k] is not None:
                o = s.obj_of[k]
                token = th.obj(o)
                token = token if len(token) <= width - 2 else token[: width - 3] + "."
                token = f"({token})" if not s.prop_standable(o) else f"<{token}>"
            elif s.terrain_of[k] != ground:
                # Terrain is a *region*, so it must be visible or the clues that reference it
                # ("beside a water square") are unanswerable. Braced to read as ground rather than
                # as an object, and marked `~` where nobody can stand.
                t = s.terrain_of[k]
                nm = th.obj(t)
                nm = nm if len(nm) <= width - 3 else nm[: width - 3]
                token = f"{{{nm}}}" if TERRAINS[t].standable else f"~{nm}~"
            else:
                token = "."
            row.append(f"{token:^{width}}")
        lines.append("".join(row))
        if r < s.H - 1:
            seg = ["     "]
            for c in range(s.W):
                a1, a2 = s.area_of[s.k(r, c)], s.area_of[s.k(r + 1, c)]
                seg.append(("=" * width) if a1 != a2 else (" " * width))
            lines.append("".join(seg))
    return "\n".join(lines)


def render_scene_compact(case: Case, th: Theme, *, solution: bool = False) -> str:
    """A compact, lossless scene view for language-model and terminal use.

    Emoji are deliberately confined to the legends: their display width and tokenisation differ
    across clients, so they must never carry unique information.  The grids themselves use stable
    ASCII codes and contain every cell exactly once.  A reader can reconstruct area membership,
    props, terrain, standability and doors from this block without interpreting wall art.
    """
    s = case.scene
    area_codes = {a: f"A{a + 1}" for a in range(s.n_areas)}
    props = sorted(s.props, key=lambda p: p.pid)
    prop_codes = {p.pid: f"P{i + 1}" for i, p in enumerate(props)}
    terrains = sorted(set(s.terrain_of))
    terrain_codes = {t: f"T{i + 1}" for i, t in enumerate(terrains)}
    at = {k: x for x, k in case.solution.items()} if solution else {}

    def grid(title: str, token) -> list[str]:
        values = [[str(token(s.k(r, c))) for c in range(s.W)] for r in range(s.H)]
        width = max(2, max(len(x) for row in values for x in row))
        lines = [
            title,
            "     " + " ".join(f"{chr(ord('a') + c):>{width}}" for c in range(s.W)),
        ]
        for r, row in enumerate(values):
            lines.append(f"{r + 1:>3}  " + " ".join(f"{x:>{width}}" for x in row))
        return lines

    def cell_feature(k: int) -> str:
        if k in at:
            return f"[{at[k]}]"
        pid = s.prop_of[k]
        if pid is not None:
            return prop_codes[pid]
        return "." if k in s.open_cells else "#"

    out = [
        "紧凑场景图——用坐标推理；emoji 只是冗余标注，不作为信息依据。",
        "每个「区域/道具」格子给出所在区域和道具编号。'.' 表示无道具；'#' 表示地形使格子不可站。能否站立以图例为准。",
        *grid(
            "区域/道具图",
            lambda k: f"{area_codes[s.area_of[k]]}/{cell_feature(k)}",
        ),
        "",
        "区域图例",
    ]
    for a in range(s.n_areas):
        out.append(f"  {area_codes[a]} = {th.area(a)}")

    out.append("\n道具图例")
    if not props:
        out.append("  （无）")
    for p in props:
        icon = "🟢" if p.standable else "⛔"
        landmark = " 📍地标" if p.landmark else ""
        cells = " ".join(cell_label(case, k) for k in sorted(p.cells))
        out.append(
            f"  {prop_codes[p.pid]} {icon} {th.obj(p.pid)} — "
            f"{'可站立' if p.standable else '阻挡'}{landmark}; 格子: {cells}"
        )

    # 地形是独立一层，因为一个格子可以同时有地形和道具。统一地板只需一句话；非平凡地形给出完整图层。
    if len(terrains) == 1 and terrains[0] == DEFAULT_TERRAIN:
        out.append("\n地形\n  所有格子: 地面 🗺 可站立")
    else:
        out.extend(
            [
                "",
                *grid("地形图", lambda k: terrain_codes[s.terrain_of[k]]),
                "",
                "地形图例",
            ]
        )
        for t in terrains:
            standable = TERRAINS[t].standable
            out.append(
                f"  {terrain_codes[t]} 🗺 {th.obj(t)} — "
                f"{'可站立' if standable else '阻挡'}"
            )

    out.append("\n门/窗")
    if not s.doors:
        out.append("  （无）")
    else:
        for d in sorted((tuple(sorted(x)) for x in s.doors)):
            out.append(f"  🚪 {cell_label(case, d[0])} <-> {cell_label(case, d[1])}")
    return "\n".join(out)


def render_areas(case: Case, th: Theme) -> str:
    s = case.scene
    out = []
    for a in range(s.n_areas):
        cells = " ".join(cell_label(case, k) for k in s.cells_of_area(a))
        out.append(f"  {th.area(a)}: {cells}")
    return "\n".join(out)


RULES = """规则
  1. 每只{cast_noun}恰好站在一个格子上。任意两只不同行，也不同列。（在 {W}x{H} 的棋盘上放 {n} 只{cast_noun}，每行每列恰好一只。）
  2. 标 (...) 的格子放着你不能站的东西；标 <...> 的格子放着可站的家具；光秃秃的 '.' 是空地。
  3. 棋盘被 '=' 的墙分成若干区域；下面列出的区域列表为准。
  4. 受害者 {victim} 是这 {n} 只{cast_noun}之一，和其他{cast_noun}一样占一个格子——把它想成案发那一刻大家站的位置。
"""

COMPACT_RULES = """规则
  1. 每只{cast_noun}恰好站在一个格子上。任意两只不同行，也不同列。（在 {W}x{H} 的棋盘上放 {n} 只{cast_noun}，每行每列恰好一只。）
  2. 在"区域/道具"图中，A1/A2/... 是区域，P1/P2/... 是道具，'.' 表示无道具，'#' 表示地形让格子不可站。道具和地形图例会说明能否站立。
  3. 每个格子都明确给出所在区域；门/窗按两端格子列出。
  4. 受害者 {victim} 是这 {n} 只{cast_noun}之一，和其他{cast_noun}一样占一个格子——把它想成案发那一刻大家站的位置。
"""

TERMS = """术语
  「旁边」：上、下、左、右相邻一格，且在同一区域内（除非线索另有说明）。
  「墙角」：与所在区域两面相邻边界（含外边界）相接的格子。
  「外边界」：整个棋盘的第一行/最后一行，或第一列/最后一列。
  「门/窗前面」：该开口连接的两个格子之一；区域之间互不相通。
  「同区域」：在同一区域内。「独自」：所在区域里没有别的{cast_noun}（含受害者）。
  「单独在一起」：那个区域里恰好只有这两只{cast_noun}。
  行/列偏移只比较指出的那一行或列。区域编号从 1 开始。
  空区域里有 0 只{cast_noun}；0 算偶数。
  地形是地面层，与可能同名道具相互独立。
"""

GOAL_MURDERER = """目标
  {victim} {note}。凶手就是那个和{victim}「单独在一起」的{cast_noun}——与它在同一区域，且该区域没有第三只{cast_noun}。
  你的答案要给出完整布局：每只{cast_noun}及所站格子。也要指出凶手，但判定的是整个布局——嫌疑只有几只时，光报一个名字和猜没什么区别。
"""

GOAL_VICTIM_CELL = """目标
  {victim} {note}。你的答案要给出完整布局：每只{cast_noun}及所站格子。关键在于{victim}所占的格子，但判定的是整个布局。
"""


def render_case(
    case: Case,
    th: Theme | None = None,
    *,
    include_solution: bool = False,
    scene_format: str = "classic",
) -> str:
    th = th or canonical_theme(case)
    th.validate(case)
    if scene_format not in ("classic", "compact"):
        raise ValueError(f"未知场景格式 {scene_format!r}")
    n = len(case.characters)
    goal = GOAL_MURDERER if case.vdef.answer == "murderer" else GOAL_VICTIM_CELL
    rules = COMPACT_RULES if scene_format == "compact" else RULES
    scene = (
        render_scene_compact(case, th, solution=include_solution)
        if scene_format == "compact"
        else render_scene(case, th, solution=include_solution)
    )
    cast = ", ".join(
        f"{th.name(x)}" + ("（受害者）" if x == case.victim else "")
        for x in case.characters
    )
    clues = "\n".join(
        f"  {i+1}. {render_clue(c, case, th)}" for i, c in enumerate(case.clues)
    )
    attributes = (
        (
            "属性\n"
            + "\n".join(
                f"  {th.name(x)}: "
                + (
                    "、".join(th.tag(t) for t in sorted(case.tags.get(x, ()), key=str))
                    or "无列出属性"
                )
                for x in case.characters
            )
            + "\n"
        )
        if case.tags
        else ""
    )
    parts = [
        f"案卷：{th.title}",
        (f"\n{th.blurb}\n" if th.blurb else ""),
        rules.format(
            n=n,
            W=case.scene.W,
            H=case.scene.H,
            victim=th.name(case.victim),
            cast_noun=th.cast_noun,
        ),
        TERMS.format(cast_noun=th.cast_noun),
        goal.format(
            victim=th.name(case.victim), note=th.victim_note, cast_noun=th.cast_noun
        ),
        f"角色（{n}只）\n  {cast}\n",
        attributes,
        "场景\n" + scene + "\n",
        (
            ("区域\n" + render_areas(case, th) + "\n")
            if scene_format == "classic"
            else ""
        ),
        f"线索（{len(case.clues)}）\n{clues}\n",
    ]
    return "\n".join(p for p in parts if p)


def render_certificate(case: Case, certificate, th: Theme | None = None) -> str:
    """Render a deterministic certificate as themed, human-readable numbered steps.

    The certificate remains the machine-checkable source. This function changes names and cell
    notation only; it never asks an LLM to invent a reason or a deduction.
    """
    th = th or canonical_theme(case)
    th.validate(case)
    icons = {1: "🔹", 2: "🔸", 3: "🧠", 4: "✅"}

    def humanise(text: str) -> str:
        text = re.sub(
            r"\br(\d+)c(\d+)\b",
            lambda m: f"{chr(ord('a') + int(m.group(2)) - 1)}{int(m.group(1))}",
            text,
        )
        for sym in sorted(case.characters, key=len, reverse=True):
            text = re.sub(rf"(?<!\w){re.escape(sym)}(?!\w)", th.name(sym), text)
        return text

    lines = []
    for i, step in enumerate(certificate.steps, 1):
        lines.append(
            f"{i:>2}. {icons.get(step.tier, '•')} "
            f"[{step.kind}, tier {step.tier}] {humanise(step.text)}"
        )
    if not certificate.solved:
        lines.append(
            f"\n在 {len(certificate.stuck)} 只未确定角色处停下。"
        )
    return "\n".join(lines)
