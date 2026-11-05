"""The daily case: plan a season, generate candidates, pick, lock and build.

    python -m murdoku_lab.setter.daily plan --days 14
    python -m murdoku_lab.setter.daily generate --days 14 --workers 8
    python -m murdoku_lab.setter.daily review 2026-10-15      # candidates side by side
    python -m murdoku_lab.setter.daily pick 2026-10-15 2      # optional: override the auto pick
    python -m murdoku_lab.setter.daily lock --days 14
    python -m murdoku_lab.setter.daily status
    python -m murdoku_lab.setter.daily build                  # → web/public/daily, og, d/<n>
    python -m murdoku_lab.setter.daily release --out site/murdoku/play --site-url https://…/

`release` is what the website's daily job runs. It downloads only the days now due from the private
dataset, two days ahead so that a missed run leaves no gap, and builds them.

A season (config/daily/season-<id>.json) fixes the weekly rhythm of board sizes and bands, the
epoch that numbers cases (#1 is the epoch's day), and the setting rotation: no setting repeats
within a week. Cases stay out of the repository, in data/daily/<season>/ (MURDOKU_DAILY_DIR replaces
data/daily), a local copy of a private dataset. Each day gets a few candidates from the
constraint-first farm with seeds derived from sha256("murdoku/daily/v1/<date>/<j>"), prefixed from
the season's `salted_from` date with the private salt in <season>/seed_salt.txt, so a day can always
be regenerated but the public code cannot reveal upcoming cases. Locking picks a candidate
in which every living suspect has a statement (the reviewer's pick, or the one nearest the day's target difficulty that keeps the variety rules: a new room layout and
a murderer letter unlike the days beside it, farming a few more candidates when none does), dresses it in the
day's setting (with a title in season for the date that neither an earlier daily case nor the
frozen showcase uses for the setting, and preferably a victim not seen within five days) and
records the candidate, seed, git revision and solver version. The season's `calendar` gives
chosen dates such as holidays their own setting, label, title, blurb, size and band. Locking stops at the
first day it cannot fill, so locked days never leave a gap. Locked cases are listed in
content/daily/published.json so dataset exports can leave them out.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from murdoku_lab.core.instance import Case
from murdoku_lab.core.theme import Theme
from murdoku_lab.paths import PROJECT_ROOT

ROOT = PROJECT_ROOT
SALT_FILE = "seed_salt.txt"
RELEASE_AHEAD = 2  # days a case is published early, so a missed daily run leaves no gap
LOW_RUNWAY = 30  # warn when fewer days of cases than this are left
WEEKDAYS = (
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
)


def season(season_id="s01"):
    return json.loads(
        (ROOT / "config" / "daily" / f"season-{season_id}.json").read_text()
    )


def content_dir(spec):
    base = os.environ.get("MURDOKU_DAILY_DIR")
    return (Path(base) if base else ROOT / "data" / "daily") / spec["season"]


def number(spec, date):
    return (date - dt.date.fromisoformat(spec["epoch"])).days + 1


def seed_for(date, j, salt=""):
    digest = hashlib.sha256(
        f"{salt}murdoku/daily/v1/{date.isoformat()}/{j}".encode()
    ).hexdigest()
    return int(digest[:8], 16)


def _salt(spec, date):
    """The private salt for `date`: "" while its seeds are public, None when it is not here."""
    salted_from = spec.get("salted_from")
    if not salted_from or date < dt.date.fromisoformat(salted_from):
        return ""
    path = content_dir(spec) / SALT_FILE
    return path.read_text().strip() if path.is_file() else None


def _require_seeds(spec, day):
    if not day["seeds"]:
        raise SystemExit(
            f"{day['date']} needs the private salt in {content_dir(spec) / SALT_FILE}"
        )


def _rotation(spec, week):
    """The settings for one week: a seeded shuffle, so no setting repeats within the week and
    consecutive weeks differ."""
    order = list(spec["settings"])
    key = hashlib.sha256(
        f"murdoku/daily/v1/{spec['season']}/week/{week}".encode()
    ).digest()
    for i in range(len(order) - 1, 0, -1):
        j = key[i % len(key)] % (i + 1)
        order[i], order[j] = order[j], order[i]
    return order


def _with_calendar(spec, rotation, first_day):
    """The week's rotation with each calendar day's setting swapped onto its weekday."""
    calendar = spec.get("calendar", {})
    rotation = list(rotation)
    for offset in range(7):
        day = first_day + dt.timedelta(days=offset)
        setting = calendar.get(day.isoformat(), {}).get("setting")
        if setting:
            i, j = rotation.index(setting), day.weekday() % len(rotation)
            rotation[i], rotation[j] = rotation[j], rotation[i]
    return rotation


def _rhythm(spec, date, weekday):
    """Board size and band for a date: the weekly rhythm, any later change to it, then the calendar."""
    size, band = spec["rhythm"][weekday]
    for start, changes in sorted(spec.get("rhythm_from", {}).items()):
        if date.isoformat() >= start and weekday in changes:
            size, band = changes[weekday]
    entry = spec.get("calendar", {}).get(date.isoformat(), {})
    return entry.get("size", size), entry.get("band", band)


def _by_target(spec, day, pool):
    """Candidate indices: on a calendar day those showing most of its drawings first, then closest
    to the difficulty this kind of day aims for."""
    target = spec.get("target_cost", {}).get(f"{day['size']} {day['band']}")
    entry = spec.get("calendar", {}).get(day.get("date"), {})

    def rank(i):
        kinds = {p.pid for p in pool[i].scene.props}
        missing = len(set(entry.get("skins", ())) - kinds)
        distance = 0 if target is None else abs(pool[i].certificate["cost"] - target)
        return missing, distance

    return sorted(range(len(pool)), key=rank)


def plan(spec, days=None):
    start = dt.date.fromisoformat(spec["start"])
    total = days or spec["weeks"] * 7
    out = []
    for i in range(total):
        date = start + dt.timedelta(days=i)
        weekday = WEEKDAYS[date.weekday()]
        size, band = _rhythm(spec, date, weekday)
        week = i // 7
        rotation = _rotation(spec, week)
        if (
            week > 0
            and rotation[0] == _rotation(spec, week - 1)[(7 - 1) % len(rotation)]
        ):
            rotation = rotation[1:] + rotation[:1]
        rotation = _with_calendar(spec, rotation, start + dt.timedelta(days=week * 7))
        entry = spec.get("calendar", {}).get(date.isoformat(), {})
        salt = _salt(spec, date)
        out.append(
            {
                "date": date.isoformat(),
                "n": number(spec, date),
                "weekday": weekday,
                "size": size,
                "band": band,
                "setting": rotation[date.weekday() % len(rotation)],
                "special": entry.get("name") or spec.get("special", {}).get(weekday),
                "seeds": (
                    []
                    if salt is None
                    else [seed_for(date, j, salt) for j in range(spec["candidates"])]
                ),
            }
        )
    return out


def _candidates_path(spec, date):
    return content_dir(spec) / "candidates" / f"{date}.jsonl"


def _farm(day, seed, count, path, workers=6):
    """Farm `count` candidates for one day with `seed`, appending to `path`."""
    scratch = path.with_suffix(f".{seed}.part.jsonl")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "murdoku_lab.setter.farm",
            "--strategy",
            "constraint-first",
            "--variant",
            "classic",
            "--size",
            str(day["size"]),
            "--bands",
            day["band"],
            "--n",
            str(count),
            "--shots",
            "8",
            "--workers",
            str(workers),
            "--seed",
            str(seed),
            "--rhythm-policy",
            str(ROOT / "config" / "rhythm" / "player.json"),
            "--scene-spec",
            str(ROOT / "config" / "scene_specs" / "cozy.json"),
            "--out",
            str(scratch),
        ],
        check=False,
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if scratch.exists():
        # A seed farmed twice yields the same cases, so keep only the new ones.
        known = {case.content_hash() for case in _read_cases(path)}
        with path.open("a") as out:
            for line in scratch.read_text().splitlines():
                row = json.loads(line)
                case = Case.from_json(row.get("murdoku_case", row))
                if case.content_hash() not in known:
                    known.add(case.content_hash())
                    out.write(line + "\n")
        scratch.unlink()
    for stats in path.parent.glob(f"{scratch.stem}*.farm_stats.json"):
        stats.unlink()


def generate(spec, days=None, workers=6):
    """Farm candidates for every planned day that has none yet."""
    out = []
    for day in plan(spec, days):
        path = _candidates_path(spec, day["date"])
        if path.exists() and path.read_text().strip():
            continue
        _require_seeds(spec, day)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
        started = time.time()
        _farm(day, day["seeds"][0], len(day["seeds"]), path, workers)
        took = round(time.time() - started, 1)
        count = len(path.read_text().splitlines())
        out.append({"date": day["date"], "candidates": count, "seconds": took})
        print(
            f"{day['date']} {day['size']}×{day['size']} {day['band']}: {count} candidate(s) in {took}s",
            flush=True,
        )
    return out


def _read_cases(path):
    if not path.exists():
        return []
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    return [Case.from_json(row.get("murdoku_case", row)) for row in rows]


def candidates(spec, date):
    return _read_cases(_candidates_path(spec, date))


def everyone_speaks(case):
    """Every living suspect has a statement, as in the original game. The setter drops any clue the
    solution does not need, which can leave a suspect with none, so locking has to choose for this.
    """
    spoken = {clue.holder for clue in case.clues}
    return all(p in spoken for p in case.characters if p != case.victim)


def _picks_path(spec):
    return content_dir(spec) / "picks.json"


def pick(spec, date, j):
    picks = _read(_picks_path(spec), {})
    picks[date] = int(j)
    _write(_picks_path(spec), picks)


def _read(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=1, ensure_ascii=False) + "\n")


def _layout(case):
    return hashlib.sha256(json.dumps(case.scene.area_of).encode()).hexdigest()[:16]


SHOWCASE = ROOT / "content" / "showcase" / "player-bundles.jsonl"


def showcase_titles(setting_id):
    """Titles the frozen player showcase uses for one setting."""
    if not SHOWCASE.is_file():
        return []
    rows = (json.loads(line) for line in SHOWCASE.read_text().splitlines() if line)
    return [
        r["meta"]["title"] for r in rows if r["meta"]["setting"]["id"] == setting_id
    ]


def _days_left(pack, title, date):
    """How long `title` stays in season after an ISO `date`; 366 if it has no season."""
    window = pack.get("seasons", {}).get(title)
    if not window:
        return 366
    today = dt.date.fromisoformat(date)
    month, day = map(int, window[1].split("-"))
    return (dt.date(today.year, month, day) - today).days % 365


def title_schedule(spec, days=None):
    """A title for each day still to lock, or None when none is left. A calendar day keeps its own;
    any other day takes the in-season title whose season ends soonest, so dated titles land on
    fitting days and timeless ones are kept for when nothing else suits."""
    from murdoku_lab.setter import settings

    calendar = spec.get("calendar", {})
    reserved = {entry["title"] for entry in calendar.values() if entry.get("title")}
    used = {s: set(showcase_titles(s)) | reserved for s in spec["settings"]}
    locked = {}
    for record in locked_days(spec):
        locked[record["date"]] = record
        used[record["setting"]].add(record["murdoku_theme"]["title"])
    schedule = {}
    for day in plan(spec, days):
        date, setting = day["date"], day["setting"]
        if date in locked:
            continue
        if calendar.get(date, {}).get("title"):
            schedule[date] = calendar[date]["title"]
            continue
        pack = settings.load(setting)
        pool = [
            title
            for title in pack["titles"]
            if title not in used[setting] and settings.in_season(pack, title, date)
        ]
        schedule[date] = min(
            pool,
            key=lambda title: (
                _days_left(pack, title, date),
                hashlib.sha256(f"{date}|{title}".encode()).hexdigest(),
            ),
            default=None,
        )
        used[setting].add(schedule[date])
    return schedule


def _locked_near(history, date, reach):
    """What is locked within `reach` days of an ISO `date`, on both sides: a day relocked between
    locked days has to suit the days after it as well."""
    when = dt.date.fromisoformat(date)
    around = (when + dt.timedelta(days=k) for k in range(-reach, reach + 1) if k)
    return [history[d.isoformat()] for d in around if d.isoformat() in history]


def lock(spec, days=None):
    """Pick, dress and lock every planned day with candidates; earlier locks stay as they are."""
    from murdoku_lab.setter import settings

    try:
        import ortools

        solver = ortools.__version__
    except Exception:  # noqa: BLE001
        solver = "unknown"
    git = subprocess.run(
        ["git", "describe", "--always", "--dirty"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    ).stdout.strip()
    picks = _read(_picks_path(spec), {})
    lock_path = content_dir(spec) / "lock.json"
    locks = _read(lock_path, {})
    published = _read(ROOT / "content" / "daily" / "published.json", {})
    days_dir = content_dir(spec) / "days"
    history = {}
    for date in sorted(locks):
        record = json.loads((days_dir / f"{date}.json").read_text())
        history[date] = (
            _layout(Case.from_json(record["murdoku_case"])),
            record["murderer"],
            record["victim"],
        )
    titles = title_schedule(spec, days)
    for day in plan(spec, days):
        date = day["date"]
        if date in locks:
            continue
        # Lock an unbroken run of days: stop at the first day that has not been generated.
        if not _candidates_path(spec, date).exists():
            break
        if not day["seeds"]:
            print(f"{date} needs the private salt; stopping here")
            break
        if not titles.get(date):
            print(
                f"no {day['setting']} title left for {date}; add one before locking it"
            )
            break
        pool = candidates(spec, date)
        layouts = {h[0] for h in history.values()}
        beside = {h[1] for h in _locked_near(history, date, 1)}

        def fits(case):
            return (
                everyone_speaks(case)
                and _layout(case) not in layouts
                and case.murderer not in beside
            )

        # Top a day up from further seeds when it has no candidate that keeps the variety rules.
        for extra in range(1, 4):
            if any(fits(c) for c in pool) or date in picks:
                break
            when = dt.date.fromisoformat(date)
            _farm(
                day,
                seed_for(when, len(day["seeds"]) + extra, _salt(spec, when)),
                2,
                _candidates_path(spec, date),
            )
            pool = candidates(spec, date)
        order = [i for i in _by_target(spec, day, pool) if everyone_speaks(pool[i])]
        if not order:
            print(
                f"no candidate for {date} gives every suspect a statement after "
                "top-ups; farm more before locking it"
            )
            break
        if picks.get(date) in order:
            order = [picks[date]] + [i for i in order if i != picks[date]]
        j = next((i for i in order if fits(pool[i])), order[0])
        case = pool[j]
        if not fits(case):
            print(
                f"warning: {date} repeats a layout or the murderer letter of a day beside it; "
                "pick another candidate here or on that day"
            )
        # Six Vanes take turns as victims, so "no repeat within five days" is always possible.
        victims = {h[2] for h in _locked_near(history, date, 5)}
        # The title is settled; only one Vane in six may be fresh, so try salts for the victim.
        entry = spec.get("calendar", {}).get(date, {})
        dressings = []
        for attempt in range(200):
            salt = date if attempt == 0 else f"{date}#{attempt}"
            theme = settings.dress(
                case,
                day["setting"],
                salt=salt,
                title=titles[date],
                blurb=entry.get("blurb"),
                date=date,
                objects=entry.get("objects"),
                skins=entry.get("skins"),
            )
            dressings.append((salt, theme))
            if theme.name(case.victim) not in victims:
                break
        best = [d for d in dressings if d[1].name(case.victim) not in victims]
        salt, theme = (best or dressings)[0]
        record = {
            "schema": "murdoku.daily_case/1",
            "date": date,
            "n": day["n"],
            "weekday": day["weekday"],
            "size": day["size"],
            "band": day["band"],
            "special": day["special"],
            "setting": day["setting"],
            "murderer": case.murderer,
            "victim": theme.name(case.victim),
            "murdoku_case": case.to_json(),
            "murdoku_theme": theme.to_json(),
            "epilogue": settings.epilogue(
                theme,
                case,
                case.murderer,
                case.scene.area_of[case.solution[case.victim]],
                motive=entry.get("motive"),
            ),
        }
        _write(days_dir / f"{date}.json", record)
        locks[date] = {
            "candidate": j,
            "seed": day["seeds"][0],
            "salt": salt,
            "content_hash": case.content_hash(),
            "git": git,
            "ortools": solver,
            "locked_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        }
        published[case.content_hash()] = f"{spec['season']}/{date}"
        history[date] = (_layout(case), case.murderer, theme.name(case.victim))
        print(f"locked {date} #{day['n']} {day['setting']}: {theme.title}")
    _write(lock_path, locks)
    _write(ROOT / "content" / "daily" / "published.json", published)
    return locks


def status(spec, days=None):
    locks = _read(content_dir(spec) / "lock.json", {})
    rows = []
    for day in plan(spec, days):
        pool = candidates(spec, day["date"])
        title = ""
        if day["date"] in locks:
            record = json.loads(
                (content_dir(spec) / "days" / f"{day['date']}.json").read_text()
            )
            title = Theme.from_json(record["murdoku_theme"]).title
        rows.append(
            f"#{day['n']:<4} {day['date']} {day['weekday'][:3]} {day['size']}×{day['size']} "
            f"{day['band']:<6} {day['setting']:<10} candidates={len(pool)} "
            f"{'locked: ' + title if title else 'open'}"
        )
    return rows


def locked_days(spec, through=None):
    """Locked days in date order; with an ISO `through`, only those up to that date."""
    days_dir = content_dir(spec) / "days"
    return [
        json.loads(p.read_text())
        for p in sorted(days_dir.glob("*.json"))
        if not through or p.stem <= through
    ]


def build(spec, out=None, site_url="", through=None):
    """Write the locked days up to `through` for the player: bundles sealed with their date, scenes,
    thumbs, share images and a link-preview page per day. With no days to write it stops before
    touching `out`, so a missing dataset cannot wipe a site."""
    from murdoku_lab.environment.state import Scratchpad
    from murdoku_lab.setter import settings
    from murdoku_lab.visual.art import STATIC_LAYERS, casebook, thumbnail_svg
    from murdoku_lab.visual.art.cards import card_for, share_card_svg
    from murdoku_lab.visual.play_export import bundle
    from murdoku_lab.visual.projection import public_observation
    from murdoku_lab.visual.raster import bundled_profile, png_from_svg

    records = locked_days(spec, through)
    if not records:
        raise SystemExit(
            f"no locked daily cases in {content_dir(spec)}; fetch them first"
        )
    out = Path(out or ROOT / "web" / "public")
    daily_dir = out / "daily"
    for directory in (daily_dir, out / "og", out / "d"):
        if directory.exists():
            shutil.rmtree(directory)
    daily_dir.mkdir(parents=True)
    (out / "og").mkdir()
    manifest = []
    for record in records:
        case = Case.from_json(record["murdoku_case"])
        theme = Theme.from_json(record["murdoku_theme"])
        pack = settings.load(theme.setting_id)
        n = record["n"]
        case_id = f"daily-{n}"
        data = bundle(
            case,
            theme,
            case_id=case_id,
            kind="daily",
            setting=pack["name"],
            eyebrow=f"Daily case #{n}",
            salt=record["date"],
            epilogue=record.get("epilogue"),
        )
        data["daily"] = {
            "n": n,
            "date": record["date"],
            "weekday": record["weekday"],
            "season": spec["season"],
            "special": record["special"],
        }
        data["share"] = {"url": f"{site_url}d/{n}/", "og_image": f"og/{n}.png"}
        data["scene"] = {"day": f"{case_id}.day.svg", "night": f"{case_id}.night.svg"}
        data["thumb"] = f"{case_id}.thumb.svg"
        (daily_dir / f"{case_id}.json").write_text(
            json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        )
        obs = public_observation(Scratchpad(case, theme))
        for mode in ("day", "night"):
            (daily_dir / f"{case_id}.{mode}.svg").write_text(
                casebook.scene_svg(
                    obs,
                    theme=mode,
                    layers=STATIC_LAYERS,
                    cell_labels="none",
                    backdrop=False,
                )
            )
        (daily_dir / f"{case_id}.thumb.svg").write_text(thumbnail_svg(obs, px=320))
        weekday = record["weekday"].title()
        date = dt.date.fromisoformat(record["date"])
        label = f"{weekday[:3]} {date.day} {date.strftime('%b')}"
        card = card_for(
            case,
            theme,
            state="unsolved",
            number=n,
            date=label,
            difficulty=record["band"].title(),
            url=data["share"]["url"].replace("https://", "").replace("http://", ""),
        )
        (out / "og" / f"{n}.png").write_bytes(
            png_from_svg(share_card_svg(card, "og"), profile=bundled_profile())
        )
        _og_page(out / "d" / str(n), n, theme, pack, record, site_url)
        manifest.append(
            {
                "n": n,
                "id": case_id,
                "date": record["date"],
                "weekday": record["weekday"],
                "special": record["special"],
                "title": theme.title,
                "blurb": theme.blurb,
                "setting": {"id": theme.setting_id, "name": pack["name"]},
                "size": f"{case.scene.W}×{case.scene.H}",
                "difficulty": data["meta"]["difficulty"],
                "accent": data["meta"]["accent"],
                "content_hash": data["content_hash"],
                "thumb": data["thumb"],
                "url": f"{case_id}.json",
            }
        )
    index = {
        "schema": "murdoku.daily_manifest/1",
        "season": spec["season"],
        "epoch": spec["epoch"],
        "days": manifest,
    }
    (daily_dir / "manifest.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=1) + "\n"
    )
    return index


def _through_date(through):
    try:
        return dt.date.fromisoformat(through).isoformat()
    except (TypeError, ValueError):
        raise SystemExit(f"invalid release date {through!r}; use YYYY-MM-DD") from None


def fetch(spec, through):
    """Download the locked days due by ISO `through` from the private dataset, and nothing later.
    Uses the `hf` command, which logs in by itself on GitHub Actions (see the daily guide).
    """
    through = _through_date(through)
    source = spec["dataset"]
    files = [
        f"{spec['season']}/days/{day['date']}.json"
        for day in plan(spec)
        if day["date"] <= through
    ]
    if not files:
        # With no filenames, `hf download` would fetch the entire private dataset.
        raise SystemExit(
            f"no daily cases due by {through}; season starts on {spec['start']}"
        )
    subprocess.run(
        [
            str(Path(sys.executable).with_name("hf")),
            "download",
            source["repo"],
            *files,
            "--repo-type",
            "dataset",
            "--revision",
            source["revision"],
            "--local-dir",
            str(content_dir(spec).parent),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
    )


def _today():
    return dt.datetime.now(dt.timezone.utc).date()


def release(spec, out, site_url, through=None, ahead=RELEASE_AHEAD, download=True):
    """Fetch and build the days now due, and say how many days of cases are left. It fails if a day
    is missing or the cases end before `through`. `hf download` skips files the dataset lacks, so
    this check is what notices them, while the site still has days it released earlier.
    """
    today = _today()
    chosen = through
    through = through or (today + dt.timedelta(days=ahead)).isoformat()
    if download:
        fetch(spec, through)
    index = build(spec, out, site_url, through=through)
    released = {day["date"] for day in index["days"]}
    missing = [
        day["date"]
        for day in plan(spec)
        if day["date"] <= through and day["date"] not in released
    ]
    if missing:
        raise SystemExit(f"no daily case for {', '.join(missing)}; upload it")
    latest = index["days"][-1]
    if not chosen and latest["date"] < through:
        raise SystemExit(f"daily cases end on {latest['date']}; lock the next batch")
    left = (dt.date.fromisoformat(plan(spec)[-1]["date"]) - today).days
    if left < LOW_RUNWAY:
        print(f"::warning::only {left} days of daily cases left; lock the next batch")
    print(
        f"released through {latest['date']} (#{latest['n']}); {left} days of cases left"
    )
    return index


def _og_page(directory, n, theme, pack, record, site_url):
    """A tiny page per case for link previews; people who open it land on the case."""
    from html import escape

    directory.mkdir(parents=True, exist_ok=True)
    title = f"Murdoku Daily #{n} · {theme.title}"
    description = f"{pack['name']} · {record['size']}×{record['size']} {record['band']} · {theme.blurb}"
    image = f"{site_url}og/{n}.png" if site_url else f"../../og/{n}.png"
    canonical = (
        f'<link rel="canonical" href="{escape(site_url)}d/{n}/">'
        f'<meta property="og:url" content="{escape(site_url)}d/{n}/">'
        if site_url
        else ""
    )
    (directory / "index.html").write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        f"<title>{escape(title)}</title>"
        f'<meta name="description" content="{escape(description)}">'
        f"{canonical}"
        f'<meta property="og:title" content="{escape(title)}">'
        f'<meta property="og:description" content="{escape(description)}">'
        f'<meta property="og:image" content="{escape(image)}">'
        '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
        '<meta name="twitter:card" content="summary_large_image">'
        '<script>const target=new URL("../../",location.href);'
        'target.search=location.search;target.searchParams.delete("case");'
        f'target.searchParams.set("d","{n}");'
        "target.hash=location.hash;location.replace(target.href);</script>"
        f'<noscript><meta http-equiv="refresh" content="0; url=../../?d={n}"></noscript>'
        f'</head><body><a href="../../?d={n}">{escape(title)}</a></body></html>\n'
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--season", default="s01")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("plan", "generate", "lock", "status"):
        p = sub.add_parser(name)
        p.add_argument("--days", type=int, default=None)
        if name == "generate":
            p.add_argument("--workers", type=int, default=6)
    p = sub.add_parser("pick")
    p.add_argument("date")
    p.add_argument("candidate", type=int)
    p = sub.add_parser("review")
    p.add_argument("date")
    p = sub.add_parser("build")
    p.add_argument("--out", default=None)
    p.add_argument("--site-url", default="")
    p.add_argument("--through", default=None, help="last date to build, YYYY-MM-DD")
    p = sub.add_parser("fetch")
    p.add_argument("--through", required=True, help="last date to download, YYYY-MM-DD")
    p = sub.add_parser("release")
    p.add_argument("--out", required=True)
    p.add_argument("--site-url", required=True)
    p.add_argument("--through", default=None, help="last date to release, YYYY-MM-DD")
    p.add_argument("--ahead", type=int, default=RELEASE_AHEAD)
    p.add_argument("--no-fetch", action="store_true", help="use the days already here")
    args = parser.parse_args(argv)
    spec = season(args.season)
    if args.command == "plan":
        for day in plan(spec, args.days):
            print(
                f"#{day['n']:<4} {day['date']} {day['weekday'][:3]} {day['size']}×{day['size']} {day['band']:<6} {day['setting']}"
            )
    elif args.command == "generate":
        generate(spec, args.days, args.workers)
    elif args.command == "pick":
        pick(spec, args.date, args.candidate)
        print(f"picked candidate {args.candidate} for {args.date}")
    elif args.command == "review":
        from murdoku_lab.solver.logic import certify

        for j, case in enumerate(candidates(spec, args.date)):
            cert = certify(case)
            print(
                f"[{j}] murderer {case.murderer} · {len(case.clues)} clues · cost {cert.cost} · depth {cert.depth}"
            )
            for clue_no, clue in enumerate(case.clues, start=1):
                print(f"     {clue_no}. {clue.holder}: {[a.kind for a in clue.atoms]}")
    elif args.command == "lock":
        lock(spec, args.days)
    elif args.command == "status":
        print("\n".join(status(spec, args.days)))
    elif args.command == "build":
        index = build(spec, args.out, args.site_url, through=args.through)
        print(f"built {len(index['days'])} daily cases")
    elif args.command == "fetch":
        fetch(spec, args.through)
    elif args.command == "release":
        release(
            spec,
            args.out,
            args.site_url,
            through=args.through,
            ahead=args.ahead,
            download=not args.no_fetch,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
