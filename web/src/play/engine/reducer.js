// Board edits, mirroring murdoku_lab/visual/session.py VisualSession.act action for action:
// the same validation, the same mistaken-but-legal moves (two people on one square, a person on
// a blocked square), and the same undo history. tests/engine replays recorded sessions.
import { parseCell, resolvePerson } from "./case.js";

export class ActionError extends Error {}

export function initialState() {
  return { placed: {}, marks: {}, exclusions: {}, reviewed: [], undo: [], redo: [], revision: 0 };
}

const EDIT_KEYS = {
  board: ["action"],
  check: ["action"],
  place: ["action", "person", "cell"],
  unplace: ["action", "person"],
  mark: ["action", "person", "cell"],
  unmark: ["action", "person", "cell"],
};
const NO_HISTORY = new Set(["undo", "redo", "board", "check", "present", "submit"]);

function sameKeys(args, keys) {
  const own = Object.keys(args);
  return own.length === keys.length && keys.every((k) => own.includes(k));
}

function subsetKeys(args, keys) {
  return Object.keys(args).every((k) => keys.includes(k));
}

function fail(message) {
  throw new ActionError(message);
}

// The board state that undo restores and that decides whether an edit changed anything.
export function snapshot(state) {
  const sets = (record) =>
    Object.fromEntries(
      Object.keys(record)
        .sort()
        .map((k) => [k, [...record[k]].sort()]),
    );
  return JSON.stringify({
    placed: Object.fromEntries(Object.keys(state.placed).sort().map((k) => [k, state.placed[k]])),
    marks: sets(state.marks),
    exclusions: sets(state.exclusions),
    reviewed: [...state.reviewed].sort(),
  });
}

function restore(state, snap) {
  const value = JSON.parse(snap);
  return { ...state, placed: value.placed, marks: value.marks, exclusions: value.exclusions, reviewed: value.reviewed };
}

function person(game, value) {
  if (typeof value !== "string" || /[\n\r]/.test(value)) fail("Unknown person.");
  const id = resolvePerson(game, value);
  if (!id) fail("Unknown person.");
  return id;
}

function cells(game, value, multiple) {
  if (typeof value !== "string" || /[\n\r]/.test(value)) fail("A square looks like b1.");
  const parts = value.trim().split(/\s+/).filter(Boolean);
  if (!parts.length || (parts.length !== 1 && !multiple)) fail("A square looks like b1.");
  const out = parts.map((p) => parseCell(game, p));
  if (out.some((c) => c === null)) fail("That square is outside this board.");
  return out;
}

export function act(game, state, args) {
  if (!args || typeof args !== "object" || Array.isArray(args)) fail("An action must be an object.");
  const action = args.action;
  const previous = snapshot(state);
  let next = state;
  if (action === "undo" || action === "redo") {
    if (!sameKeys(args, ["action"])) fail("Undo and redo take no arguments.");
    const [src, dst] = action === "undo" ? ["undo", "redo"] : ["redo", "undo"];
    if (!state[src].length) fail(`Nothing to ${action}.`);
    const stack = [...state[src]];
    const snap = stack.pop();
    next = restore({ ...state, [src]: stack, [dst]: [...state[dst], previous] }, snap);
  } else if (action === "exclude" || action === "unexclude") {
    if (!sameKeys(args, ["action", "person", "cell"])) fail("An exclusion needs a person and one square.");
    const who = person(game, args.person);
    const [cell] = cells(game, args.cell, false);
    const own = new Set(state.exclusions[who] || []);
    if (action === "exclude") own.add(cell);
    else own.delete(cell);
    next = { ...state, exclusions: { ...state.exclusions, [who]: [...own] } };
  } else if (action === "review_clue") {
    if (!sameKeys(args, ["action", "clue_id", "reviewed"]) || typeof args.reviewed !== "boolean")
      fail("review_clue needs clue_id and a boolean reviewed.");
    if (!game.clueIds.has(args.clue_id)) fail("Unknown clue.");
    const reviewed = new Set(state.reviewed);
    if (args.reviewed) reviewed.add(args.clue_id);
    else reviewed.delete(args.clue_id);
    next = { ...state, reviewed: [...reviewed] };
  } else {
    if (!(action in EDIT_KEYS) || !subsetKeys(args, EDIT_KEYS[action])) fail("Unknown action.");
    if (action !== "board" && action !== "check") {
      const who = person(game, args.person);
      if (action === "unplace") {
        const placed = { ...state.placed };
        delete placed[who];
        next = { ...state, placed };
      } else {
        const where = cells(game, args.cell, action === "mark" || action === "unmark");
        if (action === "place") {
          next = { ...state, placed: { ...state.placed, [who]: where[0] } };
        } else {
          const own = new Set(state.marks[who] || []);
          for (const c of where) {
            if (action === "mark") own.add(c);
            else own.delete(c);
          }
          next = { ...state, marks: { ...state.marks, [who]: [...own] } };
        }
      }
    }
  }
  if (!NO_HISTORY.has(action) && snapshot(next) !== previous) {
    next = { ...next, undo: [...state.undo, previous], redo: [] };
  }
  return { ...next, revision: state.revision + 1 };
}

// The public view of a state, shaped like the Python observation's fields.
export function view(state) {
  // As in Python: marks list cells in board order (sorted indices), exclusions alphabetically
  // (sorted labels), and people without exclusions are left out.
  const lists = (record, dropEmpty, order) =>
    Object.fromEntries(
      Object.keys(record)
        .sort()
        .filter((k) => !dropEmpty || record[k].length)
        .map((k) => [k, [...record[k]].sort(order)]),
    );
  return {
    placements: Object.fromEntries(Object.keys(state.placed).sort().map((k) => [k, state.placed[k]])),
    marks: lists(state.marks, false, byCell),
    exclusions: lists(state.exclusions, true, undefined),
    reviewed: [...state.reviewed].sort(),
    can_undo: state.undo.length > 0,
    can_redo: state.redo.length > 0,
  };
}

// Board order (row-major), the order Python sorts cell indices in.
export function byCell(a, b) {
  const ka = [Number(a.slice(1)), a.charCodeAt(0)];
  const kb = [Number(b.slice(1)), b.charCodeAt(0)];
  return ka[0] - kb[0] || ka[1] - kb[1];
}
