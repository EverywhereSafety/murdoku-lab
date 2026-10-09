"""The compact solver view is small, readable, and carries every structural scene fact."""

from murdoku_lab.core.theme import Theme
from murdoku_lab.core.render import (
    cell_label,
    render_case,
    render_certificate,
    render_scene_compact,
)
from murdoku_lab.setter.pipeline import make_case


def _case():
    a = make_case(
        variant="classic", size=6, band="easy", seed=8000, attempts=30, time_limit_s=5.0
    )
    assert a.case is not None
    return a.case


def test_compact_view_names_every_area_prop_terrain_and_door():
    case = _case()
    th = Theme.load("manor")
    text = render_scene_compact(case, th)
    for area in range(case.scene.n_areas):
        assert f"A{area + 1} = {th.area(area)}" in text
    for i, prop in enumerate(sorted(case.scene.props, key=lambda p: p.pid), 1):
        assert f"P{i} " in text
        assert th.obj(prop.pid) in text
        for k in prop.cells:
            assert cell_label(case, k) in text
    for terrain in set(case.scene.terrain_of):
        assert th.obj(terrain) in text
    for door in case.scene.doors:
        u, v = sorted(door)
        assert f"{cell_label(case, u)} <-> {cell_label(case, v)}" in text


def test_compact_grid_contains_every_cell_once_per_layer():
    case = _case()
    text = render_scene_compact(case, Theme.load("manor"))
    area = text.split("AREA LEGEND", 1)[0]
    area_rows = [
        line.split()[1:] for line in area.splitlines() if line.lstrip()[:1].isdigit()
    ]
    assert len(area_rows) == case.scene.H
    assert all(len(row) == case.scene.W for row in area_rows)


def test_compact_case_uses_matching_rules_and_never_leaks_solution():
    case = _case()
    text = render_case(case, Theme.load("manor"), scene_format="compact")
    assert "AREA/FEATURE" in text and "PROP LEGEND" in text and "TERRAIN" in text
    assert "Squares marked (...)" not in text
    for x, k in case.solution.items():
        assert f"[{x}]" not in text


def test_unknown_scene_format_fails_loudly():
    case = _case()
    try:
        render_case(case, Theme.load("manor"), scene_format="painted")
    except ValueError as e:
        assert "unknown scene format" in str(e)
    else:
        raise AssertionError("an unknown view must not silently change the prompt")


def test_certificate_renderer_applies_theme_without_changing_certificate():
    from murdoku_lab.solver.logic import certify

    case = _case()
    th = Theme.load("manor")
    cert = certify(case)
    before = cert.to_json()
    text = render_certificate(case, cert, th)
    assert text.startswith(" 1. ")
    assert any(icon in text for icon in ("🔹", "🔸", "🧠", "✅"))
    assert any(th.name(x) in text for x in case.characters)
    assert cert.to_json() == before


from murdoku_lab.core.atoms import Atom
from murdoku_lab.core.instance import Clue
from murdoku_lab.core.theme import canonical_theme
from murdoku_lab.core.render import render_clue, render_atom


def test_existential_conjunction_preserves_each_atom_subject(base_case):
    case = base_case
    theme = canonical_theme(case)
    clue = Clue((Atom("other_beside", "V", ("bed",)), Atom("with", "V", ("C",))))
    text = render_clue(clue, case, theme)
    assert (
        text
        == "Someone else in V's area was beside a bed. V was in the same area as C."
    )
    for clue in case.clues:
        assert render_clue(clue, case, theme) == " ".join(
            render_atom(a, case, theme) for a in clue.atoms
        )
