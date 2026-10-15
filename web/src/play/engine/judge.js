// The verdict, scored like murdoku_lab/environment/scoring.py: a case is solved only when the
// whole arrangement and the named answer are both right. Wrong verdicts get a precise, tiered
// outcome so the player knows what to look at next.
import { conflicts, isComplete } from "./rules.js";

// The classic rule: the murderer is the one other person in the victim's area.
export function impliedMurderer(game, placed) {
  if (!game.victim || !(game.victim in placed)) return null;
  const area = game.areaOf.get(placed[game.victim]);
  const others = Object.entries(placed).filter(
    ([who, cell]) => who !== game.victim && game.areaOf.get(cell) === area,
  );
  return others.length === 1 ? others[0][0] : null;
}

export function judge(game, placed, answer) {
  const secret = game.secret();
  const n = game.personIds.length;
  const misplaced = game.personIds.filter((p) => placed[p] !== secret.solution[p]);
  const correctCells = n - misplaced.length;
  const complete = isComplete(game, placed);
  const exact = complete && misplaced.length === 0;
  const broken = conflicts(game, placed);
  const violations = broken.rows.size + broken.cols.size + broken.blocked.size;
  const answerCorrect =
    secret.goal_type === "murderer" ? answer === secret.murderer : answer === secret.victim_cell;
  const solved = exact && answerCorrect;
  let outcome;
  if (solved) outcome = "solved";
  else if (exact) outcome = "correct_grid_wrong_verdict";
  else if (!complete) outcome = "incomplete_placement";
  else if (violations) outcome = "base_rule_violation";
  // Cases have one solution, so any other complete, rule-abiding board breaks a clue (Python's
  // clue_violation), whether or not the named suspect happens to be right.
  else outcome = "wrong_arrangement";
  return {
    solved,
    outcome,
    placement_exact: exact,
    placement_complete: complete,
    placement_cells_correct: correctCells,
    misplaced,
    answer,
    answer_correct: answerCorrect,
    implied_murderer: complete ? impliedMurderer(game, placed) : null,
    base_rule_violations: violations,
  };
}

// Stars depend on help and mistakes, never on speed.
export function stars({ wrongVerdicts = 0, hintLevels = [] } = {}) {
  const revealed = hintLevels.some((level) => level >= 3);
  if (wrongVerdicts === 0 && hintLevels.length === 0) return 3;
  if (!revealed && wrongVerdicts <= 1) return 2;
  return 1;
}
