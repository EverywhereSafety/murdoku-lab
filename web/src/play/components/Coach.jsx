import React, { useState } from "react";
import { crossedFor } from "../engine/rules.js";
import { t } from "../i18n/index.js";
import { Mascot } from "./ui.jsx";

const first = (game, who) => game.person.get(who).name.split(" ")[0];

// The training case's guide. It reads the board and walks the deduction order: pick the next
// person, read their statement, see which squares are still open, place them; then the verdict.
export function useCoach(game, state, selected, finished) {
  const [stage, setStage] = useState("intro");
  if (game.bundle.kind !== "tutorial") return null;
  const secret = game.secret();
  const { order, candidates } = secret.hints;
  const solution = secret.solution;
  const victim = first(game, game.victim);
  if (finished) return { key: "coach.done", vars: {}, pose: "celebrating", focus: {}, reset: () => setStage("intro") };
  if (stage === "intro")
    return { key: "coach.intro", vars: {}, pose: "pointing", focus: {}, next: () => setStage("play") };
  const wrong = order.find((p) => state.placed[p] && state.placed[p] !== solution[p]);
  if (wrong)
    return {
      key: "coach.wrong",
      vars: { name: first(game, wrong), cell: state.placed[wrong].toUpperCase() },
      pose: "thinking",
      focus: { cells: [state.placed[wrong]], person: wrong },
    };
  const next = order.find((p) => !(p in state.placed));
  if (!next)
    return {
      key: game.goalType === "murderer" ? "coach.verdict" : "coach.close",
      vars: { victim },
      pose: "pointing",
      focus: { cells: game.cells.filter((c) => c.area === secret.victim_area).map((c) => c.cell) },
    };
  const name = first(game, next);
  const placedCount = Object.keys(state.placed).length;
  if (selected !== next)
    return { key: placedCount ? "coach.pickNext" : "coach.pick", vars: { name }, pose: "pointing", focus: { person: next } };
  const statement = game.clues.filter((c) => c.person === next).map((c) => c.text).join(" ");
  const crossed = crossedFor(game, state.placed, next);
  const open = (candidates[next] || []).filter((cell) => !crossed.has(cell));
  let key = placedCount === 0 ? "coach.first" : open.length === 1 ? "coach.single" : "coach.narrow";
  if (!statement) key = "coach.silent";
  return { key, vars: { name, statement }, pose: "thinking", focus: { cells: open.length ? open : [solution[next]], person: next } };
}

export function CoachCard({ coach, onLibrary, onAgain }) {
  if (!coach) return null;
  return (
    <div className="pl-hint pl-coach" role="status" aria-live="polite">
      <Mascot pose={coach.pose} size={64} />
      <div className="pl-hint-body">
        <p>{t(coach.key, coach.vars)}</p>
        {(coach.next || coach.key === "coach.done") && (
          <div className="pl-hint-buttons">
            {coach.next && (
              <button type="button" className="pl-primary" onClick={coach.next}>
                {t("coach.start")}
              </button>
            )}
            {coach.key === "coach.done" && (
              <button type="button" className="pl-primary" onClick={onLibrary}>
                {t("coach.cases")}
              </button>
            )}
            {coach.key === "coach.done" && onAgain && (
              <button type="button" className="pl-secondary" onClick={onAgain}>
                {t("coach.again")}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
