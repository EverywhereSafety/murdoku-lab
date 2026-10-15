// One case being played: board state, saved progress and the verdict, as an external store
// for React's useSyncExternalStore. A player gesture may be several actions (rule a square out
// and drop its pencil mark); they apply together and undo as one step.
import { judge, stars } from "./judge.js";
import { freshProgress, loadProgress, saveProgress } from "./persist.js";
import { act, initialState, snapshot } from "./reducer.js";

const HISTORY = new Set(["undo", "redo"]);

export function applyBatch(game, state, actions) {
  let next = state;
  for (const action of actions) next = act(game, next, action);
  if (actions.length > 1 && !actions.some((a) => HISTORY.has(a.action))) {
    const changed = snapshot(next) !== snapshot(state);
    next = {
      ...next,
      undo: changed ? [...state.undo, snapshot(state)] : state.undo,
      redo: changed ? [] : state.redo,
    };
  }
  return next;
}

function replay(game, events) {
  let state = initialState();
  for (const batch of events) {
    try {
      state = applyBatch(game, state, batch);
    } catch {
      // A move that no longer applies (an edited case) is skipped, not fatal.
    }
  }
  return state;
}

export function createStore(game, { persist = true } = {}) {
  let progress = persist ? loadProgress(game) : freshProgress(game);
  let state = replay(game, progress.events);
  let lastResult = null;
  let snap = { state, progress, lastResult };
  const listeners = new Set();
  const emit = () => {
    snap = { state, progress, lastResult };
    for (const listener of listeners) listener();
  };
  const save = () => {
    if (persist) saveProgress(game, progress);
  };
  return {
    game,
    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    getSnapshot: () => snap,
    // Returns true when the board changed; throws ActionError for an invalid move.
    dispatch(actions) {
      const list = Array.isArray(actions) ? actions : [actions];
      if (progress.finished) return false;
      const next = applyBatch(game, state, list);
      const changed = snapshot(next) !== snapshot(state) || HISTORY.has(list[0]?.action);
      state = next;
      if (changed) {
        progress = { ...progress, events: [...progress.events, list] };
        save();
      }
      emit();
      return changed;
    },
    submit(answer) {
      const result = judge(game, state.placed, answer);
      if (result.solved) {
        const earned = stars({ wrongVerdicts: progress.wrong_verdicts, hints: progress.hints });
        progress = {
          ...progress,
          finished: { at: Date.now(), stars: earned, answer, elapsed_ms: progress.elapsed_ms },
        };
      } else if (result.placement_complete && !result.base_rule_violations) {
        progress = { ...progress, wrong_verdicts: progress.wrong_verdicts + 1 };
      }
      lastResult = result;
      save();
      emit();
      return result;
    },
    // Record a hint shown to the player; stars count them.
    hint(given) {
      if (progress.finished) return;
      const { target, level, reveal } = given;
      progress = { ...progress, hints: [...progress.hints, { target, level, reveal }] };
      save();
      emit();
    },
    tick(ms) {
      if (progress.finished || ms <= 0) return;
      progress = { ...progress, elapsed_ms: progress.elapsed_ms + ms };
      save();
    },
    restart() {
      progress = freshProgress(game);
      state = initialState();
      lastResult = null;
      save();
      emit();
    },
  };
}
