from dataclasses import replace
import pytest
from murdoku_lab.core.theme import Theme
from murdoku_lab.setter.theme_quality import neutralize_setup, parse_review


def test_extra_setup_facts_removed_without_changing_labels():
    t = Theme(
        "x",
        "Example",
        {"A": "Alice"},
        blurb="Alice is beside the body",
        victim_note="alone",
    )
    clean = neutralize_setup(t)
    assert clean.blurb == "" and clean.victim_note == "was found dead"
    assert clean.names == t.names
    assert t.blurb == "Alice is beside the body"


@pytest.mark.parametrize(
    "value",
    [
        {"accept": "true", "issues": []},
        {"accept": True, "issues": ["bad prop"]},
        {"accept": False, "issues": []},
    ],
)
def test_malformed_or_inconsistent_review_does_not_accept(value):
    with pytest.raises(ValueError):
        parse_review(value)


def test_duplicate_labels_and_nonenglish_are_rejected():
    from types import SimpleNamespace
    from murdoku_lab.setter.theme_quality import quality_issues

    scene = SimpleNamespace(prop_by_id={}, n_areas=2, props=[])
    case = SimpleNamespace(characters=["A", "V"], scene=scene)
    theme = Theme("x", "Example", {"A": "Alice", "V": "Bob"}, areas=("Hall", " hall "))
    assert any("duplicate area" in s for s in quality_issues(case, theme))
    theme = replace(theme, areas=("Hall", "厨房"))
    assert any("non-English" in s for s in quality_issues(case, theme))


def test_complete_prop_retry_requires_exact_keys(monkeypatch):
    import json
    from types import SimpleNamespace
    import murdoku_lab.setter.llm_setter as setter

    prop = SimpleNamespace(pid="table", standable=False, landmark=False, cells={0})
    scene = SimpleNamespace(
        prop_of=("table",), props=[prop], prop_by_id={"table": prop}, n_areas=1
    )
    case = SimpleNamespace(characters=["A", "V"], victim="V", scene=scene)
    monkeypatch.setattr(setter, "verify_invariance", lambda c, t: None)
    good = {
        "theme_id": "test",
        "title": "Example",
        "names": {"A": "Alice", "V": "Bob"},
        "areas": ["Hall"],
        "objects": {"table": "workbench"},
        "victim_note": "was found dead",
    }
    bad = dict(good, objects={"p0": "workbench"})

    class Client:
        usage = SimpleNamespace(to_json=lambda: {})

        def __init__(self):
            self.calls = 0

        def available(self):
            return True

        def chat(self, messages, **kwargs):
            self.calls += 1
            if self.calls == 2:
                assert "EXACT prop IDs" in messages[-1]["content"]
            return json.dumps(bad if self.calls == 1 else good)

    client = Client()
    result = setter.llm_theme(
        case, style="workshop", client=client, require_complete_props=True
    )
    assert result.attempts == 2 and result.theme.objects == {"table": "workbench"}
