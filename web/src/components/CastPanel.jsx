import React from "react";
import { Check, Eraser, MousePointer2, Pencil, X } from "lucide-react";
import { appUrl } from "../urls.js";
export function CastPanel({
  mode,
  person,
  review,
  selected,
  selectedPosition,
  setHighlightedClues,
  setSelected,
  state,
  uiAct,
  viewOnly,
}) {
  return (
    <section className="cast-panel" aria-label="People in this case">
      <div className="cast-heading">
        <span className="eyebrow">
          THE PEOPLE
          <span className="count-inline">{state.people.length}</span>
        </span>
        <span>
          Tap a square to note a candidate. Hold to confirm.
          <span className="drag-hint"> Dragging works, too.</span>
        </span>
      </div>
      <div
        className="cast-grid"
        style={{
          "--cast-count": Math.min(state.people.length, 8),
        }}
      >
        {state.people.map((p, i) => (
          <div
            className={`person-container ${selected === p.id ? "selected" : ""} ${p.victim ? "victim" : ""}`}
            key={p.id}
          >
            <button
              className="person-card"
              aria-label={`Select ${p.name}${p.victim ? ", the victim" : ""}`}
              aria-pressed={selected === p.id}
              draggable={!viewOnly}
              onDragStart={(e) => {
                e.dataTransfer.setData("application/murdoku-person", p.id);
                e.dataTransfer.effectAllowed = "move";
                // Keep the SVG drop target stable throughout the drag. Selecting
                // here would fetch and replace its DOM before the drop arrives.
              }}
              onClick={() => {
                setSelected(p.id);
                setHighlightedClues([]);
              }}
            >
              <span className="portrait-wrap">
                <img
                  src={appUrl(`/api/art/portrait/${p.portrait}.svg`)}
                  alt=""
                />
                <span
                  className="person-symbol"
                  style={{
                    background: p.color,
                  }}
                >
                  {p.id}
                </span>
                {state.placements[p.id] && (
                  <span className="placed-check">
                    <Check size={10} />
                  </span>
                )}
              </span>
              <strong>{p.name}</strong>
              <span className="person-caption">
                {state.placements[p.id] ? (
                  <b>{state.placements[p.id]}</b>
                ) : p.victim ? (
                  "THE VICTIM"
                ) : (
                  "SUSPECT"
                )}
              </span>
              {!!p.tags.length && (
                <span className="person-tags">{p.tags.join(", ")}</span>
              )}
            </button>
            {state.placements[p.id] && !viewOnly && (
              <button
                className="remove-person"
                title={`Unplace ${p.name}`}
                aria-label={`Unplace ${p.name}`}
                onClick={() =>
                  uiAct({
                    action: "unplace",
                    person: p.id,
                  })
                }
              >
                <X size={11} />
              </button>
            )}
          </div>
        ))}
      </div>
      <div className="selection-note">
        <span className="selection-icon">
          {mode === "mark" ? (
            <Pencil size={15} />
          ) : mode === "erase" ? (
            <Eraser size={15} />
          ) : (
            <MousePointer2 size={15} />
          )}
        </span>
        <span>
          {review ? (
            "You are viewing a recorded step."
          ) : state.done ? (
            "This case has been submitted."
          ) : person ? (
            <>
              <strong>{person.name}</strong> selected.{" "}
              {mode === "mark" ? (
                "Tap to add or remove candidates. Hold a square or press Space to confirm."
              ) : mode === "erase" ? (
                "Tap their placement or pencil mark to erase it."
              ) : selectedPosition ? (
                <>
                  Currently at <b>{selectedPosition}</b>. Choose a square to
                  move.
                </>
              ) : (
                "Choose a square to place them."
              )}
            </>
          ) : (
            "Select someone from the cast to begin."
          )}
        </span>
        <span className="keyboard-hint">
          <kbd>1–{Math.min(state.people.length, 9)}</kbd> select
        </span>
      </div>
    </section>
  );
}
