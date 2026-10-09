"""Validation of public action arguments and presentation notes."""

from murdoku_lab.core.render import parse_cell


class SessionError(ValueError):
    pass


def validate_note(note, pad):
    if note is None:
        return None
    if not isinstance(note, dict):
        raise SessionError("note must be an object")
    allowed = {"summary", "clue_ids", "focus_person", "focus_cells"}
    if set(note) - allowed:
        raise SessionError("unknown presentation note field")
    summary = note.get("summary", "")
    if not isinstance(summary, str) or len(summary) > 1200:
        raise SessionError("summary must be text, at most 1200 characters")
    clues = note.get("clue_ids", [])
    known = {f"clue-{i + 1}" for i in range(len(pad.case.clues))}
    if not isinstance(clues, list) or any(
        not isinstance(c, str) or c not in known for c in clues
    ):
        raise SessionError("clue_ids must name visible clues")
    cells = note.get("focus_cells", [])
    if (
        not isinstance(cells, list)
        or len(cells) > pad.case.scene.n_cells
        or any(not isinstance(c, str) or parse_cell(pad.case, c) is None for c in cells)
    ):
        raise SessionError("focus_cells must name squares on this board")
    person = note.get("focus_person")
    if person is not None and person not in pad.case.characters:
        raise SessionError("focus_person must be a canonical character symbol")
    return {
        "summary": summary,
        "clue_ids": list(dict.fromkeys(clues)),
        "focus_person": person,
        "focus_cells": [c.lower().strip() for c in dict.fromkeys(cells)],
    }


def validate_tool_action(args, pad):
    """Check syntax BEFORE mutation, while allowing the same mistaken claims as upstream.
    A blocked or conflicting placement is accepted; explicit check() reports base breaches.
    """
    if not isinstance(args, dict):
        raise SessionError("action arguments must be an object")
    action = args.get("action")
    allowed = {
        "board": {"action"},
        "check": {"action"},
        "place": {"action", "person", "cell"},
        "unplace": {"action", "person"},
        "mark": {"action", "person", "cell"},
        "unmark": {"action", "person", "cell"},
        "submit": {"action", "placements", "murderer", "answer"},
    }
    if action not in allowed or set(args) - allowed[action]:
        raise SessionError("unknown action or arguments")

    def person(value):
        if (
            not isinstance(value, str)
            or any(c in value for c in "\n\r")
            or pad.sym(value) is None
        ):
            raise SessionError("unknown person; use a cast symbol or name")

    def cell(value, multiple=False):
        if not isinstance(value, str) or any(c in value for c in "\n\r"):
            raise SessionError("cell must be a coordinate such as b1")
        parts = value.split()
        if (
            not parts
            or (len(parts) != 1 and not multiple)
            or any(parse_cell(pad.case, c) is None for c in parts)
        ):
            raise SessionError("coordinate is outside this board")

    if action in ("place", "unplace", "mark", "unmark"):
        person(args.get("person"))
        if action != "unplace":
            cell(args.get("cell"), multiple=action in ("mark", "unmark"))
    if action == "submit":
        placements = args.get("placements", {})
        if not isinstance(placements, dict):
            raise SessionError("placements must map people to coordinates")
        resolved = set()
        for who, where in placements.items():
            person(who)
            cell(where)
            canonical = pad.sym(who)
            if canonical in resolved:
                raise SessionError("a person appears twice through name aliases")
            resolved.add(canonical)
        answer = args.get("murderer", args.get("answer", ""))
        if not isinstance(answer, str) or any(c in answer for c in "\n\r"):
            raise SessionError("answer must be one line of text")
