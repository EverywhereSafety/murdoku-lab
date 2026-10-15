"""The legacy renderer is frozen: published datasets were drawn with it.

Every legacy style, scope and a few board states of the bundled demos must render byte for
byte as they did before the casebook art was introduced. Regenerate the fixture only when a
legacy change is intended:

    python tests/test_legacy_art.py --write
"""

import hashlib
import json
import sys
from pathlib import Path

from murdoku_lab.visual import art, demos
from murdoku_lab.visual.projection import ART_KINDS
from murdoku_lab.visual.session import VisualSession

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "legacy_art_digests.json"
LEGACY_STYLES = ("art", "classic", "diagram", "fluent")


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _states(entry):
    session = VisualSession(entry)
    first = session.observe()
    people = [p["id"] for p in first["people"]]
    cells = [c["cell"] for c in first["scene"]["cells"] if c["standable"]]
    yield "empty", first, None
    session.act({"action": "place", "person": people[0], "cell": cells[0]})
    yield "placed", session.observe(), people[0]
    session.act({"action": "mark", "person": people[1], "cell": " ".join(cells[1:4])})
    yield "marked", session.observe(), people[1]
    session.act({"action": "place", "person": people[2], "cell": cells[0]})
    yield "collision", session.observe(), None
    session.act({"action": "exclude", "person": people[1], "cell": cells[5]})
    yield "exclusion", session.observe(), people[1]


def compute():
    out = {}
    for entry in demos.catalogue().values():
        for state, obs, selected in _states(entry):
            for style in LEGACY_STYLES:
                key = f"{entry.slug}/{state}/{style}"
                out[f"{key}/scene"] = _sha(
                    art.scene_svg(obs, style=style, selected=selected)
                )
                out[f"{key}/board"] = _sha(art.board_svg(obs, style=style))
                out[f"{key}/full"] = _sha(
                    art.observation_svg(obs, style=style, selected=selected)
                )
    for i in range(24):
        out[f"portrait/{i}"] = _sha(art.portrait_svg(i))
    for kind in sorted(ART_KINDS | {"generic"}):
        out[f"prop/{kind}"] = _sha(art.prop_svg(kind))
    return out


def test_legacy_renderer_is_frozen():
    expected = json.loads(FIXTURE.read_text())
    actual = compute()
    changed = sorted(k for k in expected if actual.get(k) != expected[k])
    missing = sorted(set(expected) - set(actual))
    assert not missing, f"legacy outputs no longer produced: {missing[:10]}"
    assert not changed, f"legacy outputs changed: {changed[:10]}"


if __name__ == "__main__":
    if "--write" not in sys.argv:
        sys.exit("pass --write to regenerate the frozen legacy digests")
    FIXTURE.write_text(json.dumps(compute(), indent=1, sort_keys=True) + "\n")
    print(f"wrote {FIXTURE}")
