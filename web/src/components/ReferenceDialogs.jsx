import React from "react";
import { appUrl } from "../urls.js";
import { Dialog } from "./Controls.jsx";
export function HelpDialog({ dialog, setDialog, state }) {
  return (
    <Dialog
      open={dialog === "help"}
      onClose={() => setDialog(null)}
      title="A quick field guide"
    >
      <p className="dialog-description">
        Use the witness statements to reconstruct where everyone stood.
      </p>
      <ol className="guide-list">
        {state.rules.map((r, i) => (
          <li key={i}>
            <span>{String(i + 1).padStart(2, "0")}</span>
            <p>{r}</p>
          </li>
        ))}
      </ol>
      <div className="shortcut-grid">
        <span>
          <kbd>1–9</kbd> Choose person
        </span>
        <span>
          <kbd>P</kbd> Place
        </span>
        <span>
          <kbd>M</kbd> Pencil candidates
        </span>
        <span>
          <kbd>X</kbd> Erase
        </span>
        <span>
          <kbd>⌃ Z</kbd> Undo
        </span>
        <span>
          <kbd>← ↑ ↓ →</kbd> Move grid focus
        </span>
        <span>
          <kbd>Enter</kbd> Act on focused cell
        </span>
        <span>
          <kbd>Space</kbd> Confirm person
        </span>
        <span>Hold a square to confirm a candidate</span>
        <span>
          <kbd>Delete</kbd> Unplace person
        </span>
      </div>
      <p className="fine-print">
        “Check placements” checks only rows, columns and blocked squares.
        Ticking a statement is your own note. It does not certify a deduction.
      </p>
    </Dialog>
  );
}
export function KeyDialog({ dialog, setDialog, state }) {
  return (
    <Dialog
      open={dialog === "key"}
      onClose={() => setDialog(null)}
      title="Know the scene"
    >
      <p className="dialog-description">
        Match each illustration to the objects in the statements. A prop can
        occupy several squares.
      </p>
      <div className="object-key">
        {state.scene.props.map((p) => (
          <div key={p.id}>
            <img src={appUrl(`/api/art/prop/${p.art}.svg`)} alt="" />
            <span>
              <strong>{p.name}</strong>
              <small>
                {p.art === "generic" ? `${p.id} · ` : ""}
                {p.cells.join(", ")}
              </small>
            </span>
            <em className={p.standable ? "standable" : "blocked"}>
              {p.standable ? "Standable" : "Blocked"}
            </em>
          </div>
        ))}
      </div>
      <h3 className="small-heading">The ground underfoot</h3>
      <div className="terrain-key">
        {state.scene.terrains.map((t) => (
          <span key={t.id}>
            <b>{t.name}</b>
            {t.standable ? "Standable" : "Blocked"}
          </span>
        ))}
      </div>
      <p className="fine-print">
        The cross on a square is authoritative. A blocked terrain square stays
        blocked even if a standable prop covers it.
      </p>
    </Dialog>
  );
}
export function CreditsDialog({ dialog, setDialog }) {
  return (
    <Dialog
      open={dialog === "credits"}
      onClose={() => setDialog(null)}
      title="An illustrated edition"
    >
      <p>
        Original game:{" "}
        <a
          href="https://murdoku.com/play/?lang=en"
          target="_blank"
          rel="noreferrer"
        >
          Murdoku, by Manuel Garand
        </a>
        .
      </p>
      <p>
        This independent visual lab adds original vector art and an interactive
        casebook to the supplied Murdoku RL rules and tool harness. The included
        scenes are authored UI examples.
      </p>
      <p>
        Area numbers, furniture footprints, terrain, doors and character
        coordinates come from one public state. The illustrated map, diagram and
        image exports share that state.
      </p>
      <p className="fine-print">
        Progress is held by the local Python server and survives page refreshes.
        Restarting the server clears its in-memory sessions. No model inference
        is running in this viewer.
      </p>
    </Dialog>
  );
}
