"""The daily schedule: rhythm, rotation, reproducible seeds, locked content and the build."""

import json

import pytest

from murdoku_lab.setter import daily, export_queries
from murdoku_lab.visual.seal import unseal


@pytest.fixture(scope="module")
def spec():
    return daily.season("s01")


def test_plan_follows_the_weekly_rhythm(spec):
    days = daily.plan(spec, 28)
    assert [d["n"] for d in days] == list(range(1, 29))
    for d in days:
        assert [d["size"], d["band"]] == spec["rhythm"][d["weekday"]]
        assert d["seeds"] == [
            daily.seed_for(daily.dt.date.fromisoformat(d["date"]), j)
            for j in range(spec["candidates"])
        ]
    sundays = [d for d in days if d["weekday"] == "sunday"]
    assert all(d["special"] == "Sunday Special" for d in sundays)


def test_no_setting_repeats_within_a_week_or_on_consecutive_days(spec):
    days = daily.plan(spec)
    for start in range(0, len(days), 7):
        week = [d["setting"] for d in days[start : start + 7]]
        assert len(set(week)) == 7
    assert all(a["setting"] != b["setting"] for a, b in zip(days, days[1:]))


def test_case_numbers_count_days_from_the_epoch(spec):
    epoch = daily.dt.date.fromisoformat(spec["epoch"])
    assert daily.number(spec, epoch) == 1
    assert daily.number(spec, epoch + daily.dt.timedelta(days=30)) == 31


def test_locked_days_keep_the_variety_rules(spec):
    days = daily.locked_days(spec)
    if not days:
        pytest.skip("no locked daily cases in this checkout")
    by_setting = {}
    for record in days:
        title = record["murdoku_theme"]["title"]
        by_setting.setdefault(record["setting"], []).append(title)
    for setting_id, titles in by_setting.items():
        assert len(set(titles)) == len(titles)
        assert not set(titles) & set(daily.showcase_titles(setting_id))
    letters = [d["murderer"] for d in days]
    assert all(a != b for a, b in zip(letters, letters[1:]))
    victims = [d["victim"] for d in days]
    assert all(v not in victims[max(0, i - 5) : i] for i, v in enumerate(victims))
    dates = [daily.dt.date.fromisoformat(d["date"]) for d in days]
    assert all((b - a).days == 1 for a, b in zip(dates, dates[1:]))
    published = export_queries.daily_published()
    from murdoku_lab.core.instance import Case

    cases = [Case.from_json(d["murdoku_case"]) for d in days]
    assert len({daily._layout(c) for c in cases}) == len(cases)
    assert all(c.content_hash() in published for c in cases)


def test_build_writes_sealed_bundles_and_preview_pages(spec, tmp_path):
    days = daily.locked_days(spec)
    if not days:
        pytest.skip("no locked daily cases in this checkout")
    index = daily.build(spec, tmp_path, site_url="https://example.org/play/")
    first = index["days"][0]
    bundle = json.loads((tmp_path / "daily" / first["url"]).read_text())
    assert bundle["daily"]["n"] == first["n"]
    secret = unseal(bundle["secret"], bundle["id"], first["date"])
    assert set(secret["solution"]) == {p["id"] for p in bundle["public"]["people"]}
    with pytest.raises(Exception):
        unseal(bundle["secret"], bundle["id"], "1999-01-01")
    page = (tmp_path / "d" / str(first["n"]) / "index.html").read_text()
    assert f"https://example.org/play/og/{first['n']}.png" in page
    assert (tmp_path / "og" / f"{first['n']}.png").read_bytes().startswith(b"\x89PNG")


def test_lock_tops_up_an_empty_day_and_never_leaves_a_gap(spec, tmp_path, monkeypatch):
    days = daily.locked_days(spec)
    if len(days) < 3:
        pytest.skip("needs three locked daily cases")
    rows = [json.dumps({"murdoku_case": d["murdoku_case"]}) + "\n" for d in days[:3]]
    monkeypatch.setattr(daily, "ROOT", tmp_path)
    monkeypatch.delenv("MURDOKU_DAILY_DIR", raising=False)
    trial = {**spec, "season": "trial"}
    first, empty, third = (d["date"] for d in daily.plan(trial, 3))
    (daily.content_dir(trial) / "candidates").mkdir(parents=True)
    daily._candidates_path(trial, first).write_text(rows[0])
    daily._candidates_path(trial, empty).write_text("")
    daily._candidates_path(trial, third).write_text(rows[2])

    farmed = []
    monkeypatch.setattr(daily, "_farm", lambda day, seed, count, path, workers=6: None)
    assert list(daily.lock(trial, 3)) == [
        first
    ]  # the third day waits for the empty one

    def farm(day, seed, count, path, workers=6):
        farmed.append(day["date"])
        with path.open("a") as out:
            out.write(rows[1])

    monkeypatch.setattr(daily, "_farm", farm)
    assert sorted(daily.lock(trial, 3)) == [first, empty, third]
    assert farmed == [empty]


def test_seeds_stay_private_from_the_salted_date(spec, tmp_path, monkeypatch):
    monkeypatch.setenv("MURDOKU_DAILY_DIR", str(tmp_path))
    salted_from = daily.dt.date.fromisoformat(spec["salted_from"])
    total = daily.number(spec, salted_from)
    before, first = daily.plan(spec, total)[-2:]
    assert first["date"] == spec["salted_from"]
    assert before["seeds"][0] == daily.seed_for(
        daily.dt.date.fromisoformat(before["date"]), 0
    )
    assert first["seeds"] == []  # without the salt nobody can work them out
    with pytest.raises(SystemExit):
        daily.generate({**spec, "start": spec["salted_from"]}, 1)
    (tmp_path / spec["season"]).mkdir()
    (tmp_path / spec["season"] / daily.SALT_FILE).write_text("secret\n")
    salted = daily.plan(spec, total)[-1]["seeds"]
    public = [daily.seed_for(salted_from, j) for j in range(spec["candidates"])]
    assert len(salted) == spec["candidates"] and not set(salted) & set(public)


def test_every_day_gets_a_fresh_title_in_season(spec, tmp_path, monkeypatch):
    from collections import Counter

    from murdoku_lab.setter import settings

    monkeypatch.setenv("MURDOKU_DAILY_DIR", str(tmp_path))
    days = daily.plan(spec)
    schedule = daily.title_schedule(spec)
    assert set(schedule) == {d["date"] for d in days}
    uses = Counter()
    for day in days:
        title = schedule[day["date"]]
        pack = settings.load(day["setting"])
        assert title and settings.in_season(pack, title, day["date"]), day["date"]
        assert title not in daily.showcase_titles(day["setting"])
        uses[day["setting"], title] += 1
    assert set(uses.values()) == {1}


def test_calendar_days_get_their_setting_label_and_words(spec):
    from murdoku_lab.setter import settings

    days = {d["date"]: d for d in daily.plan(spec)}
    schedule = daily.title_schedule(spec)
    for date, entry in spec["calendar"].items():
        assert days[date]["setting"] == entry["setting"]
        pack = settings.load(entry["setting"])
        if "title" in entry:
            assert days[date]["special"] == entry["name"]
            if date in schedule:
                assert schedule[date] == entry["title"]
            dressed = {**pack, "objects": {**pack["objects"], **entry["objects"]}}
            assert not settings.leaks(dressed, entry["title"])
            assert not settings.leaks(dressed, entry["blurb"])
            nouns = list(dressed["objects"].values())
            assert len(set(nouns)) == len(nouns), date


def test_rhythm_can_change_from_a_date_and_ease_on_calendar_days(spec):
    days = {d["date"]: d for d in daily.plan(spec)}
    saturday = lambda date: [days[date]["size"], days[date]["band"]]
    assert saturday("2026-11-07") == spec["rhythm"]["saturday"]
    assert saturday("2026-11-14") == [8, "hard"]
    assert saturday("2027-02-06") == [8, "medium"]  # Lunar New Year eases off
    for date, entry in spec["calendar"].items():
        if "band" in entry:
            assert [days[date]["size"], days[date]["band"]] == [
                entry["size"],
                entry["band"],
            ]
        assert f"{days[date]['size']} {days[date]['band']}" in spec["target_cost"]


def test_lock_prefers_the_candidate_nearest_the_days_target(spec):
    from types import SimpleNamespace

    def candidate(cost, *kinds):
        props = [SimpleNamespace(pid=kind) for kind in kinds]
        return SimpleNamespace(
            certificate={"cost": cost}, scene=SimpleNamespace(props=props)
        )

    pool = [candidate(40.0), candidate(11.0), candidate(19.0)]
    day = {"size": 6, "band": "easy"}
    assert daily._by_target(spec, day, pool) == [1, 2, 0]
    assert daily._by_target({}, day, pool) == [0, 1, 2]
    # On a calendar day, showing the day's drawings comes before the difficulty target.
    holiday = {**day, "date": "2027-03-28"}
    pool = [candidate(12.0, "chair"), candidate(30.0, "statue", "barrel", "boulder")]
    assert daily._by_target(spec, holiday, pool) == [1, 0]


def test_fetch_downloads_only_the_days_due(spec, monkeypatch):
    calls = []
    monkeypatch.setattr(
        daily.subprocess, "run", lambda command, **_: calls.append(command)
    )
    daily.fetch(spec, "2026-10-14")
    command = calls[0]
    files = [arg for arg in command if arg.startswith("s01/days/")]
    assert files == [f"s01/days/2026-10-{d}.json" for d in (12, 13, 14)]
    assert spec["dataset"]["repo"] in command and "dataset" in command
    assert command[command.index("--revision") + 1] == spec["dataset"]["revision"]


def test_release_builds_through_two_days_ahead_and_says_what_is_left(
    spec, monkeypatch, capsys
):
    today = daily.dt.date(2027, 1, 10)
    fetched, built = [], []
    monkeypatch.setattr(daily, "_today", lambda: today)
    monkeypatch.setattr(daily, "fetch", lambda s, through: fetched.append(through))

    def build(s, out, url, through=None):
        built.append(through)
        return _built_days(s, through)

    monkeypatch.setattr(daily, "build", build)
    daily.release(spec, "site", "https://example.org/")
    assert fetched == built == ["2027-01-12"]
    assert "::warning::" not in capsys.readouterr().out


def _built_days(spec, through, without=()):
    return {
        "days": [
            {"date": day["date"], "n": day["n"]}
            for day in daily.plan(spec)
            if day["date"] <= through and day["date"] not in without
        ]
    }


def test_release_warns_when_cases_run_low_and_fails_before_they_run_out(
    spec, monkeypatch, capsys
):
    last = daily.dt.date.fromisoformat(daily.plan(spec)[-1]["date"])
    monkeypatch.setattr(daily, "fetch", lambda s, through: None)
    monkeypatch.setattr(
        daily, "build", lambda s, out, url, through=None: _built_days(s, through)
    )
    monkeypatch.setattr(daily, "_today", lambda: last - daily.dt.timedelta(days=5))
    daily.release(spec, "site", "https://example.org/")
    assert "::warning::only 5 days" in capsys.readouterr().out
    # The last case is still to come, so there is time to add more.
    monkeypatch.setattr(daily, "_today", lambda: last - daily.dt.timedelta(days=1))
    with pytest.raises(SystemExit, match=f"end on {last}"):
        daily.release(spec, "site", "https://example.org/")


def test_release_fails_when_the_dataset_lacks_a_day(spec, monkeypatch):
    monkeypatch.setattr(daily, "_today", lambda: daily.dt.date(2027, 1, 10))
    monkeypatch.setattr(daily, "fetch", lambda s, through: None)
    monkeypatch.setattr(
        daily,
        "build",
        lambda s, out, url, through=None: _built_days(s, through, {"2027-01-09"}),
    )
    with pytest.raises(SystemExit, match="2027-01-09"):
        daily.release(spec, "site", "https://example.org/")
    with pytest.raises(SystemExit, match="2027-01-09"):
        daily.release(spec, "site", "https://example.org/", through="2027-01-09")


def test_release_through_a_chosen_date_ignores_the_days_after_it(spec, monkeypatch):
    monkeypatch.setattr(daily, "_today", lambda: daily.dt.date(2027, 1, 10))
    monkeypatch.setattr(daily, "fetch", lambda s, through: None)
    monkeypatch.setattr(
        daily, "build", lambda s, out, url, through=None: _built_days(s, through)
    )
    index = daily.release(spec, "site", "https://example.org/", through="2026-11-07")
    assert index["days"][-1]["date"] == "2026-11-07"


def test_build_without_cases_stops_before_touching_the_site(
    spec, tmp_path, monkeypatch
):
    monkeypatch.setenv("MURDOKU_DAILY_DIR", str(tmp_path / "nothing"))
    site = tmp_path / "site"
    (site / "daily").mkdir(parents=True)
    (site / "daily" / "manifest.json").write_text("{}")
    with pytest.raises(SystemExit):
        daily.build(spec, site)
    assert (site / "daily" / "manifest.json").exists()


def test_build_can_stop_at_a_date(spec, tmp_path):
    days = daily.locked_days(spec)
    if len(days) < 3:
        pytest.skip("needs three locked daily cases")
    index = daily.build(spec, tmp_path, through=days[1]["date"])
    assert [d["date"] for d in index["days"]] == [d["date"] for d in days[:2]]
    assert not (tmp_path / "og" / f"{days[2]['n']}.png").exists()
