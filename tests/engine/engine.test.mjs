// Replays recorded Python sessions (scripts/make_engine_fixtures.py) against the player's JS
// engine: same accepted and rejected moves, same board after every step, same undo history,
// same verdicts. Run with `npm run test:engine`.
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import { makeCase } from "../../web/src/play/engine/case.js";
import { act, ActionError, initialState, view } from "../../web/src/play/engine/reducer.js";
import { judge, stars } from "../../web/src/play/engine/judge.js";
import { conflicts, crossedFor } from "../../web/src/play/engine/rules.js";
import { seal, unseal } from "../../web/src/play/engine/seal.js";
import { caseKey, nextCase, write } from "../../web/src/play/engine/persist.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const fixtures = path.join(here, "..", "fixtures");
const read = (name) => JSON.parse(fs.readFileSync(path.join(fixtures, name), "utf8"));

function gameFrom(fixture) {
  const secret = {
    goal_type: fixture.goal_type,
    solution: fixture.verdicts.solution,
    murderer: fixture.goal_type === "murderer" ? fixture.verdicts.right : null,
    victim_cell: fixture.goal_type === "victim_cell" ? fixture.verdicts.right : null,
  };
  const bundle = {
    id: fixture.case,
    secret: seal(secret, fixture.case),
    public: {
      goal_type: fixture.goal_type,
      scene: { width: fixture.width, height: fixture.height, cells: fixture.cells, areas: [], props: [] },
      people: fixture.people,
      clues: fixture.clues.map((id) => ({ id })),
    },
  };
  return makeCase(bundle);
}

const cases = ["glasshouse", "lily-pond", "last-place"].map((name) => read(`engine/${name}.json`));

for (const fixture of cases) {
  test(`${fixture.case}: every recorded action matches the Python session`, () => {
    const game = gameFrom(fixture);
    let state = initialState();
    assert.deepEqual(view(state), fixture.initial);
    fixture.steps.forEach((step, i) => {
      let accepted = true;
      try {
        state = act(game, state, step.action);
      } catch (error) {
        if (!(error instanceof ActionError)) throw error;
        accepted = false;
      }
      assert.equal(accepted, step.ok, `step ${i} ${JSON.stringify(step.action)}`);
      if (step.ok) assert.deepEqual(view(state), step.state, `state after step ${i}`);
    });
  });

  test(`${fixture.case}: verdicts score like scoring.py`, () => {
    const game = gameFrom(fixture);
    for (const s of fixture.verdicts.scenarios) {
      const result = judge(game, s.placed, s.answer);
      assert.equal(result.solved, s.solved);
      assert.equal(result.outcome, s.outcome, JSON.stringify(s));
      assert.equal(result.placement_cells_correct, s.cells_correct);
      if (fixture.goal_type === "murderer" && result.placement_complete)
        assert.equal(result.implied_murderer, s.implied);
    }
  });
}

test("seal vectors match Python byte for byte", () => {
  for (const v of read("seal_vectors.json")) {
    assert.deepEqual(seal(v.value, v.id, v.salt), v.sealed);
    assert.deepEqual(unseal(v.sealed, v.id, v.salt), v.value);
  }
  assert.throws(() => unseal({ alg: "other", data: "" }, "x"));
});

test("base rules flag rows, columns, stacked and blocked squares", () => {
  const game = gameFrom(cases[0]);
  const blocked = game.cells.find((c) => !c.standable);
  const open = game.cells.filter((c) => c.standable);
  const [a, b] = game.personIds;
  const sameRow = open.filter((c) => c.row === open[0].row);
  const placed = { [a]: sameRow[0].cell, [b]: sameRow[1].cell };
  const broken = conflicts(game, placed);
  assert.ok(broken.people.has(a) && broken.people.has(b) && broken.rows.size === 1);
  if (blocked) assert.ok(conflicts(game, { [a]: blocked.cell }).blocked.has(a));
  const crossed = crossedFor(game, { [a]: open[0].cell }, b);
  assert.ok(game.cells.filter((c) => c.row === open[0].row).every((c) => crossed.has(c.cell)));
  assert.ok(!crossedFor(game, { [a]: open[0].cell }, a).has(open[0].cell));
});

test("stars count help and mistakes, never time", () => {
  assert.equal(stars({}), 3);
  assert.equal(stars({ wrongVerdicts: 1 }), 2);
  assert.equal(stars({ hints: [{ reveal: false }, { reveal: false }] }), 2);
  assert.equal(stars({ hints: [{ reveal: true }] }), 1);
  assert.equal(stars({ wrongVerdicts: 2 }), 1);
});

test("gestures: select, place, pick up, refuse, note cycle and swap", async () => {
  const { placeTap, noteTap, dropPerson } = await import("../../web/src/play/engine/intents.js");
  const { applyBatch } = await import("../../web/src/play/engine/store.js");
  const fixture = cases[0];
  const game = gameFrom(fixture);
  const open = game.cells.filter((c) => c.standable);
  const blocked = game.cells.find((c) => !c.standable);
  const [a, b] = game.personIds;
  let state = initialState();
  const run = (intent) => {
    state = applyBatch(game, state, intent.actions);
    return intent;
  };
  let intent = run(placeTap(game, state, a, open[0].cell));
  assert.equal(state.placed[a], open[0].cell);
  assert.equal(intent.select, b);
  intent = placeTap(game, state, b, open[0].cell);
  assert.deepEqual(intent.actions, []);
  assert.equal(intent.select, a);
  if (blocked) assert.equal(placeTap(game, state, b, blocked.cell).effect, "reject");
  run(placeTap(game, state, a, open[0].cell));
  assert.ok(!(a in state.placed));
  const undoBefore = state.undo.length;
  run(noteTap(game, state, a, open[1].cell));
  run(noteTap(game, state, a, open[1].cell));
  assert.deepEqual(state.exclusions[a], [open[1].cell]);
  assert.deepEqual(state.marks[a], []);
  assert.equal(state.undo.length, undoBefore + 2);
  run(noteTap(game, state, a, open[1].cell));
  assert.deepEqual(state.exclusions[a], []);
  run(placeTap(game, state, a, open[2].cell));
  run(placeTap(game, state, b, open[3].cell));
  run(dropPerson(game, state, a, open[3].cell));
  assert.equal(state.placed[a], open[3].cell);
  assert.equal(state.placed[b], open[2].cell);
});

test("hints escalate: next suspect, misplaced suspect, then the verdict", async () => {
  const { nextHint } = await import("../../web/src/play/engine/hints.js");
  const fixture = cases[0];
  const order = [...fixture.people.map((p) => p.id)];
  const solution = fixture.verdicts.solution;
  const game = gameFrom({ ...fixture });
  // gameFrom seals no hint data; add a minimal table like play_export's.
  const secret = game.secret();
  secret.hints = { order, candidates: Object.fromEntries(order.map((p) => [p, [solution[p]]])), forbid: {} };
  secret.victim_area = game.areaOf.get(solution[game.victim]);
  const state = initialState();
  const used = [];
  for (const level of [1, 2, 3]) {
    const hint = nextHint(game, state, used);
    assert.equal(hint.target, `next:${order[0]}`);
    assert.equal(hint.level, level);
    used.push(hint);
  }
  assert.ok(used[2].reveal && used[2].fix.cell === solution[order[0]]);
  const wrongCell = fixture.cells.find((c) => c.standable && c.cell !== solution[order[1]]).cell;
  const wrong = { ...state, placed: { [order[1]]: wrongCell } };
  assert.equal(nextHint(game, wrong, []).key, "hint.misplaced.1");
  const done = { ...state, placed: { ...solution } };
  const verdict = nextHint(game, done, []);
  assert.equal(verdict.target, "verdict");
});

test("daily days: local calendar, streaks across DST and catch-up plays", async () => {
  const daily = await import("../../web/src/play/engine/daily.js");
  assert.equal(daily.caseNumber("2026-10-12", "2026-10-15"), 4);
  // across the US and EU daylight-saving changes, day numbers stay consecutive
  assert.equal(daily.caseNumber("2026-10-12", "2026-11-02"), 22);
  assert.equal(daily.addDays("2026-10-31", 2), "2026-11-02");
  assert.equal(daily.addDays("2027-03-27", 2), "2027-03-29");
  assert.equal(daily.today(new URLSearchParams("date=2026-10-20")), "2026-10-20");
  assert.equal(daily.today(new URLSearchParams("date=bad"), new Date(2026, 9, 15, 23, 30)), "2026-10-15");
  const record = {
    1: { date: "2026-10-12", solved_on: "2026-10-12", stars: 3 },
    2: { date: "2026-10-13", solved_on: "2026-10-13", stars: 2 },
    3: { date: "2026-10-14", solved_on: "2026-10-15", stars: 3 },
    4: { date: "2026-10-15", solved_on: "2026-10-15", stars: 1, hints: 2 },
  };
  assert.deepEqual(daily.streaks(record, "2026-10-15"), { current: 1, best: 2 });
  assert.deepEqual(daily.streaks({ ...record, 3: { ...record[3], solved_on: "2026-10-14" } }, "2026-10-16"), { current: 4, best: 4 });
  assert.equal(daily.stats(record).perfect, 2);
  const manifest = { days: [{ date: "2026-10-14" }, { date: "2026-10-15" }, { date: "2026-10-16" }] };
  assert.equal(daily.openDays(manifest, "2026-10-15").length, 2);
  assert.equal(daily.openDays(manifest, "2026-10-15", true).length, 3);
});


test("timer publishes a fresh snapshot without changing board history", async () => {
  const { createStore } = await import("../../web/src/play/engine/store.js");
  const store = createStore(gameFrom(cases[0]), { persist: false });
  const before = store.getSnapshot();
  let calls = 0;
  const unsubscribe = store.subscribe(() => calls++);
  store.tick(5000);
  assert.equal(calls, 1);
  assert.equal(store.getSnapshot().progress.elapsed_ms, 5000);
  assert.equal(before.progress.elapsed_ms, 0);
  assert.equal(store.getSnapshot().state, before.state);
  store.tick(0);
  assert.equal(calls, 1);
  unsubscribe();
  store.tick(1000);
  assert.equal(calls, 1);
  assert.equal(store.getSnapshot().progress.elapsed_ms, 6000);
});

function withSavedCases(run) {
  const previous = Object.getOwnPropertyDescriptor(globalThis, "localStorage");
  const records = new Map();
  Object.defineProperty(globalThis, "localStorage", {
    configurable: true,
    value: { getItem: (key) => records.get(key) ?? null, setItem: (key, value) => records.set(key, value) },
  });
  try {
    run((entry, finished = false) => write(caseKey(entry.id), {
      content_hash: entry.content_hash,
      events: [{ action: "place", person: "A", cell: "a1" }],
      finished: finished ? { stars: 3 } : null,
    }));
  } finally {
    if (previous) Object.defineProperty(globalThis, "localStorage", previous);
    else delete globalThis.localStorage;
  }
}

const libraryEntry = (id, setting, hash = id, kind = "themed") => ({ id, kind, content_hash: hash, setting: { id: setting } });

test("next case prefers a new setting and skips the current puzzle's reskins", () => {
  withSavedCases(() => {
    const current = libraryEntry("current", "manor", "same-puzzle");
    const sameSetting = libraryEntry("another-manor", "manor");
    const reskin = libraryEntry("current-train", "train", "same-puzzle");
    const different = libraryEntry("new-theatre", "theatre");
    const entries = [current, sameSetting, reskin, different];
    assert.equal(nextCase(entries, current.id), different);
    const daily = { ...current, id: "daily-2" };
    assert.equal(nextCase(entries.slice(1), daily), different, "daily cases also avoid their theme and reskins");
    assert.equal(nextCase([reskin], daily), null, "a reskinned daily puzzle is not a new case");
    assert.deepEqual(entries.map((entry) => entry.id), [current.id, sameSetting.id, reskin.id, different.id]);
  });
});

test("next case skips solved puzzles and their reskins, and wraps past the last entry", () => {
  withSavedCases((save) => {
    const solved = libraryEntry("solved", "train", "solved-hash");
    const reskin = libraryEntry("solved-liner", "liner", "solved-hash");
    const unseen = libraryEntry("unseen", "library");
    const current = libraryEntry("last", "manor");
    save(solved, true);
    assert.equal(nextCase([solved, reskin, unseen, current], current.id), unseen);
  });
});

test("home resumes a generated puzzle before unseen cases and ignores obsolete saves", () => {
  withSavedCases((save) => {
    const unseen = libraryEntry("unseen", "manor");
    const started = libraryEntry("started", "train");
    const classic = libraryEntry("classic", "museum", "classic", "classic");
    save(started);
    save(classic);
    assert.equal(nextCase([classic, unseen, started]), started);
    save({ ...unseen, content_hash: "old-revision" }, true);
    save(started, true);
    assert.equal(nextCase([classic, unseen, started]), unseen);
  });
});

test("next case falls back to classics and returns null when no distinct unsolved puzzle remains", () => {
  withSavedCases((save) => {
    const tutorial = libraryEntry("tutorial", "manor", "tutorial", "tutorial");
    const generated = libraryEntry("generated", "train");
    const classic = libraryEntry("classic", "museum", "classic", "classic");
    save(generated, true);
    assert.equal(nextCase([tutorial, generated, classic]), classic);
    assert.equal(nextCase([tutorial, generated, classic], generated.id), classic);
    assert.equal(nextCase([classic], classic.id), null);
    save(classic, true);
    assert.equal(nextCase([tutorial, generated, classic]), null);
    assert.equal(nextCase([]), null);
  });
});
