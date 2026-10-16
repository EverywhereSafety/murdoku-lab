// Player gestures turned into engine actions. One gesture is one batch and one undo step.
// The engine accepts mistaken moves (two people on a square, a blocked square) exactly like the
// Python session; gestures are where the player app is kinder: tapping someone selects them,
// blocked squares are refused with a reason, and a drop onto someone swaps the two.

function occupantsAt(state, cell) {
  return Object.entries(state.placed)
    .filter(([, where]) => where === cell)
    .map(([who]) => who);
}

function propAt(game, cell) {
  const id = game.byLabel.get(cell)?.prop;
  return id ? game.props.find((p) => p.id === id) : null;
}

export function noteAt(state, who, cell) {
  if ((state.exclusions[who] || []).includes(cell)) return "excluded";
  if ((state.marks[who] || []).includes(cell)) return "candidate";
  return "none";
}

// The next person to place after `who`, in cast order, wrapping round.
export function nextUnplaced(game, state, who) {
  const ids = game.personIds;
  const start = Math.max(0, ids.indexOf(who));
  for (let step = 1; step <= ids.length; step += 1) {
    const candidate = ids[(start + step) % ids.length];
    if (!(candidate in state.placed)) return candidate;
  }
  return who;
}

const refuse = (game, cell) => {
  const prop = propAt(game, cell);
  return prop
    ? { key: "toast.blocked", vars: { thing: `the ${prop.name}` } }
    : { key: "toast.blockedSquare", vars: {} };
};

// A note tap cycles: nothing → maybe here → ruled out → nothing.
export function noteTap(game, state, who, cell) {
  if (!who) return { actions: [], toast: { key: "toast.pick", vars: {} } };
  if (!game.byLabel.get(cell)?.standable) return { actions: [], toast: refuse(game, cell), effect: "reject" };
  const name = game.person.get(who).name.split(" ")[0];
  const phase = noteAt(state, who, cell);
  if (phase === "none")
    return {
      actions: [{ action: "mark", person: who, cell }],
      toast: { key: "toast.candidate", vars: { name, cell } },
      effect: "note",
    };
  if (phase === "candidate")
    return {
      actions: [
        { action: "unmark", person: who, cell },
        { action: "exclude", person: who, cell },
      ],
      toast: { key: "toast.excluded", vars: { name, cell } },
      effect: "note",
    };
  return {
    actions: [{ action: "unexclude", person: who, cell }],
    toast: { key: "toast.cleared", vars: { cell } },
    effect: "note",
  };
}

export function placeTap(game, state, who, cell) {
  const here = occupantsAt(state, cell);
  const other = here.find((p) => p !== who);
  if (other) return { actions: [], select: other, effect: "select" };
  if (who && here.includes(who))
    return {
      actions: [{ action: "unplace", person: who }],
      toast: { key: "toast.pickedUp", vars: { name: game.person.get(who).name.split(" ")[0] } },
      effect: "pickup",
    };
  if (!who) return { actions: [], toast: { key: "toast.pick", vars: {} } };
  if (!game.byLabel.get(cell)?.standable) return { actions: [], toast: refuse(game, cell), effect: "reject" };
  const after = { ...state, placed: { ...state.placed, [who]: cell } };
  return {
    actions: [{ action: "place", person: who, cell }],
    select: nextUnplaced(game, after, who),
    effect: "place",
    placed: who,
  };
}

// Dragging a person onto a square: place, or swap with whoever stands there.
export function dropPerson(game, state, who, cell) {
  if (!game.byLabel.get(cell)?.standable) return { actions: [], toast: refuse(game, cell), effect: "reject" };
  const here = occupantsAt(state, cell).filter((p) => p !== who);
  const from = state.placed[who];
  const actions = [{ action: "place", person: who, cell }];
  for (const other of here) {
    actions.push(from ? { action: "place", person: other, cell: from } : { action: "unplace", person: other });
  }
  return { actions, select: who, effect: "place", placed: who };
}
