// A loaded case: the public bundle indexed for play, and its sealed answers opened on demand.
import { unseal } from "./seal.js";

export function makeCase(bundle, { salt = "" } = {}) {
  const pub = bundle.public;
  const cells = pub.scene.cells;
  const byLabel = new Map(cells.map((c) => [c.cell, c]));
  const people = pub.people;
  const areaOf = new Map(cells.map((c) => [c.cell, c.area]));
  let secret = null;
  return {
    id: bundle.id,
    bundle,
    meta: bundle.meta,
    public: pub,
    width: pub.scene.width,
    height: pub.scene.height,
    cells,
    byLabel,
    areaOf,
    areas: pub.scene.areas,
    props: pub.scene.props,
    people,
    personIds: people.map((p) => p.id),
    person: new Map(people.map((p) => [p.id, p])),
    victim: people.find((p) => p.victim)?.id ?? null,
    clues: pub.clues,
    clueIds: new Set(pub.clues.map((c) => c.id)),
    goalType: pub.goal_type,
    secret() {
      if (!secret) secret = unseal(bundle.secret, bundle.id, salt);
      return secret;
    },
  };
}

export function cellLabel(row, col) {
  return `${String.fromCharCode(97 + col)}${row + 1}`;
}

// Mirrors murdoku_lab.core.render.parse_cell: a column letter and a 1-based row number.
export function parseCell(game, text) {
  if (typeof text !== "string") return null;
  const s = text.trim().toLowerCase();
  if (s.length < 2 || !/^[a-z]/.test(s[0])) return null;
  const digits = s.slice(1);
  if (!/^\s*[+-]?\d+(?:_\d+)*\s*$/.test(digits)) return null;
  const row = Number.parseInt(digits.replace(/_/g, "").trim(), 10) - 1;
  const col = s.charCodeAt(0) - 97;
  if (!(col >= 0 && col < game.width && row >= 0 && row < game.height)) return null;
  return cellLabel(row, col);
}

// Mirrors Scratchpad.sym: a symbol, full name, first name, or a 3+ letter prefix of a name.
export function resolvePerson(game, value) {
  if (typeof value !== "string") return null;
  const n = value.trim().toLowerCase().replace(/[.,!]+$/, "");
  for (const p of game.people) {
    const full = p.name.toLowerCase();
    if (n === p.id.toLowerCase() || n === full || n === full.split(" ")[0]) return p.id;
  }
  if (n.length >= 3) {
    for (const p of game.people) if (p.name.toLowerCase().startsWith(n)) return p.id;
  }
  return null;
}
