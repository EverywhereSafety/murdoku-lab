"""Shared puzzle scratchpad and placement actions."""

from __future__ import annotations

from dataclasses import dataclass, field
from murdoku_lab.core.instance import Case
from murdoku_lab.core.theme import Theme
from murdoku_lab.core.render import cell_label, parse_cell


@dataclass
class Scratchpad:
    case: Case
    theme: Theme
    placed: dict[str, int] = field(default_factory=dict)
    marks: dict[str, set[int]] = field(default_factory=dict)

    def sym(self, name: str) -> str | None:
        """Resolve a person by display name, first name, or bare symbol."""
        n = name.strip().lower().rstrip(".,!")
        for x in self.case.characters:
            full = self.theme.name(x).lower()
            if n in (x.lower(), full, full.split()[0]):
                return x
        for x in self.case.characters:
            if self.theme.name(x).lower().startswith(n) and len(n) >= 3:
                return x
        return None

    def render(self) -> str:
        s = self.case.scene
        rows = []
        head = "     " + "".join(f"{chr(ord('a')+c):^7}" for c in range(s.W))
        rows.append(head)
        for r in range(s.H):
            line = [f"{r+1:>3}  "]
            for c in range(s.W):
                k = s.k(r, c)
                who = next((x for x, kk in self.placed.items() if kk == k), None)
                if who:
                    line.append(f"{'['+who+']':^7}")
                elif k in s.info.blocked:
                    line.append(f"{'###':^7}")
                else:
                    cands = "".join(
                        sorted(x for x, ms in self.marks.items() if k in ms)
                    )
                    line.append(f"{cands or '.':^7}")
            rows.append("".join(line))
        placed = (
            ", ".join(
                f"{self.theme.name(x)}={cell_label(self.case, k)}"
                for x, k in sorted(self.placed.items())
            )
            or "(nobody placed yet)"
        )
        return "\n".join(rows) + f"\n\nPlaced: {placed}"

    def violations(self) -> list[str]:
        """Base-rule violations only. Never looks at a clue."""
        s, out = self.case.scene, []
        rows: dict[int, list[str]] = {}
        cols: dict[int, list[str]] = {}
        for x, k in self.placed.items():
            if k in s.info.blocked:
                out.append(
                    f"{self.theme.name(x)} is on {cell_label(self.case, k)}, "
                    f"which cannot be stood on."
                )
            rows.setdefault(s.row(k), []).append(x)
            cols.setdefault(s.col(k), []).append(x)
        for r, xs in rows.items():
            if len(xs) > 1:
                out.append(
                    f"Row {r+1} holds {len(xs)} people "
                    f"({', '.join(self.theme.name(x) for x in xs)})."
                )
        for c, xs in cols.items():
            if len(xs) > 1:
                out.append(
                    f"Column {chr(ord('a')+c)} holds {len(xs)} people "
                    f"({', '.join(self.theme.name(x) for x in xs)})."
                )
        return out


def apply_action(pad: Scratchpad, raw: str) -> tuple[str, str | None]:
    """Execute one action. Returns (observation, submitted_answer_or_None)."""
    parts = raw.split()
    if not parts:
        return "Empty action.", None
    verb, args = parts[0].lower(), parts[1:]
    case = pad.case

    if verb in ("solve", "answer"):
        # `answer` is kept as an alias so an agent written against the old protocol still works,
        # but the arrangement is what gets scored either way.
        return "Submitted.", " ".join(args).strip() or "(see placement lines)"
    if verb == "board":
        return pad.render(), None
    if verb == "check":
        v = pad.violations()
        return (
            "No base-rule breaches among your placements."
            if not v
            else "Base-rule breaches:\n  - " + "\n  - ".join(v)
        ), None
    if verb in ("mark", "unmark", "place", "unplace"):
        if not args:
            return f"`{verb}` needs a person.", None
        if verb == "unplace":
            x = pad.sym(" ".join(args))
            if x is None:
                return (
                    f"No such person: {' '.join(args)!r}. People are: "
                    f"{', '.join(pad.theme.name(c) for c in case.characters)}."
                ), None
            pad.placed.pop(x, None)
            return f"{pad.theme.name(x)} is no longer placed.", None
        parsed = None
        for cut in range(len(args) - 1, 0, -1):
            maybe_x = pad.sym(" ".join(args[:cut]))
            maybe_cells = [parse_cell(case, a) for a in args[cut:]]
            if (
                maybe_x is not None
                and maybe_cells
                and all(c is not None for c in maybe_cells)
            ):
                parsed = maybe_x, maybe_cells
                break
        if parsed is None:
            return (
                f"Could not read a person and cell(s) from {' '.join(args)!r}. Use e.g. "
                f"'{pad.theme.name(case.characters[0])} c4', within "
                f"a1..{chr(ord('a')+case.scene.W-1)}{case.scene.H}."
            ), None
        x, cells = parsed
        if verb == "place":
            pad.placed[x] = cells[0]
            return f"{pad.theme.name(x)} placed at {cell_label(case, cells[0])}.", None
        ms = pad.marks.setdefault(x, set())
        if verb == "mark":
            ms |= set(cells)
        else:
            ms -= set(cells)
        return (
            f"{pad.theme.name(x)}: {len(ms)} candidate square(s) "
            f"[{' '.join(cell_label(case, c) for c in sorted(ms))}]."
        ), None
    return (
        f"Unknown action {verb!r}. Valid: mark, unmark, place, unplace, board, check, "
        f"answer."
    ), None
