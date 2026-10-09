import React from "react";
import {
  ArrowRight,
  BookOpen,
  Check,
  CheckCheck,
  ChevronDown,
  Compass,
  ShieldCheck,
} from "lucide-react";
import { EmphasizedClue } from "./EmphasizedClue.jsx";
export function EvidencePanel({
  allPlaced,
  busy,
  clues,
  highlightedClues,
  onlySelected,
  person,
  placedCount,
  selected,
  setDialog,
  setOnlySelected,
  setSelected,
  setVerdict,
  state,
  uiAct,
  verdict,
  viewOnly,
}) {
  return (
    <aside className="evidence-column" aria-label="Clues and verdict">
      <div className="evidence-title">
        <div>
          <span className="eyebrow">FOLLOW THE THREAD</span>
          <h2>
            The evidence<span>.</span>
          </h2>
        </div>
        <BookOpen size={27} strokeWidth={1.3} />
      </div>
      <p className="evidence-intro">Everyone has a story. Where do they fit?</p>
      <div className="clue-tabs">
        <button
          className={!onlySelected ? "active" : ""}
          onClick={() => setOnlySelected(false)}
        >
          All statements <span>{state.clues.length}</span>
        </button>
        <button
          className={onlySelected ? "active" : ""}
          onClick={() => setOnlySelected(true)}
          disabled={!person}
        >
          About {person?.name || "selected"}
        </button>
      </div>
      <div className="clues-list">
        {clues.map((c) => (
          <article
            key={c.id}
            className={`clue-card ${c.person === selected ? "focused" : ""} ${c.reviewed ? "reviewed" : ""} ${highlightedClues.includes(c.id) ? "referenced" : ""}`}
            data-clue={c.id}
          >
            <span className="clue-number">
              {String(c.number).padStart(2, "0")}
            </span>
            <button
              className="clue-text"
              onClick={() => {
                if (state.people.some((p) => p.id === c.person))
                  setSelected(c.person);
              }}
              aria-label={`Focus statement ${c.number}: ${c.text}`}
            >
              <EmphasizedClue
                text={c.text}
                people={state.people}
                areas={state.scene.areas}
              />
            </button>
            <button
              className={`clue-check ${c.reviewed ? "checked" : ""}`}
              aria-label={`Mark clue ${c.number} ${c.reviewed ? "unreviewed" : "reviewed"}`}
              aria-pressed={c.reviewed}
              title="Your personal checklist; does not check the clue"
              disabled={viewOnly || busy}
              onClick={() =>
                uiAct({
                  action: "review_clue",
                  clue_id: c.id,
                  reviewed: !c.reviewed,
                })
              }
            >
              {c.reviewed && <Check size={12} />}
            </button>
          </article>
        ))}
        {!clues.length && (
          <div className="empty-clues">
            No direct statement about this person. Use the other clues and the
            rules.
          </div>
        )}
      </div>
      <div className="clue-help">
        <CheckCheck size={14} />
        <span>Tick statements as you work through them.</span>
      </div>
      <div className="remember-card">
        <div className="remember-icon">
          <Compass size={27} strokeWidth={1.3} />
        </div>
        <div>
          <h3>
            {state.goal_type === "murderer"
              ? "One last thing…"
              : "A different kind of case"}
          </h3>
          <p>
            {state.goal_type === "murderer" ? (
              <>
                The murderer was <strong>alone with the victim</strong> in the
                same area. No third person.
              </>
            ) : (
              <>
                Find the victim’s square. There is{" "}
                <strong>no alone-with rule</strong> in this case.
              </>
            )}
          </p>
        </div>
      </div>
      <section className="verdict-panel">
        <div className="placement-progress">
          <span>
            <b>{placedCount}</b> of {state.people.length} people placed
          </span>
          <div>
            {state.people.map((p) => (
              <i
                key={p.id}
                className={state.placements[p.id] ? "filled" : ""}
              />
            ))}
          </div>
        </div>
        <button
          className="check-button"
          onClick={() =>
            uiAct({
              action: "check",
            })
          }
          disabled={viewOnly || busy}
        >
          <ShieldCheck size={16} />
          Check placements
        </button>
        <label className="verdict-label" htmlFor="verdict">
          {state.goal_type === "murderer"
            ? "Who do you suspect?"
            : "Where was the victim?"}
        </label>
        <div className="select-wrap">
          <select
            id="verdict"
            aria-label={
              state.goal_type === "murderer"
                ? "Choose murderer"
                : "Choose victim square"
            }
            value={verdict}
            disabled={viewOnly}
            onChange={(e) => setVerdict(e.target.value)}
          >
            <option value="">
              {state.goal_type === "murderer"
                ? "Make your deduction…"
                : "Choose a square…"}
            </option>
            {state.goal_type === "murderer"
              ? state.people
                  .filter((p) => !p.victim)
                  .map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                    </option>
                  ))
              : state.scene.cells.map((c) => (
                  <option key={c.cell} value={c.cell}>
                    {c.cell}
                  </option>
                ))}
          </select>
          <ChevronDown size={15} />
        </div>
        <button
          className="primary submit-button"
          disabled={!allPlaced || !verdict || viewOnly || busy}
          onClick={() => setDialog("submit")}
        >
          Submit case
          <ArrowRight size={17} />
        </button>
        <p className="submit-hint">
          {state.done
            ? "Submission recorded. Open a new case to play again."
            : allPlaced
              ? "The full arrangement and your verdict will be checked."
              : "Place everyone before making your final accusation."}
        </p>
      </section>
    </aside>
  );
}
