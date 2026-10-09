import React from "react";
import {
  ArrowRight,
  BookOpen,
  Check,
  CheckCheck,
  Download,
  FileJson,
  House,
  Leaf,
  NotebookPen,
  RotateCcw,
  Search,
  Clock3,
} from "lucide-react";
import { appUrl } from "../urls.js";
import { api } from "../lib/api.js";
import { download } from "../lib/export.js";
import { Dialog } from "./Controls.jsx";
export function CasesDialog({
  busy,
  cases,
  dialog,
  live,
  newSession,
  setDialog,
  showMessage,
}) {
  return (
    <Dialog
      open={dialog === "cases"}
      onClose={() => setDialog(null)}
      title="The casebook"
      wide
    >
      <p className="dialog-description">
        A few scenes to explore. Each is an authored, solvable example.
      </p>
      <div className="case-cards">
        {cases.map((c, i) => (
          <button
            className={`case-card ${c.id === live.case_id ? "current" : ""}`}
            key={c.id}
            onClick={() => {
              if (c.id === live.case_id) setDialog(null);
              else
                newSession(c.id).catch((e) => showMessage(e.message, "error"));
            }}
            disabled={busy}
          >
            <div className={`case-art case-art-${i % 3}`}>
              <span>
                {i === 1 ? (
                  <Leaf size={45} strokeWidth={1} />
                ) : i === 2 ? (
                  <BookOpen size={45} strokeWidth={1} />
                ) : (
                  <House size={45} strokeWidth={1} />
                )}
              </span>
              <small>{String(i + 1).padStart(2, "0")}</small>
            </div>
            <div>
              <span className="eyebrow">
                {c.size} × {c.size} · {c.variant}
              </span>
              <h3>{c.title}</h3>
              <p>{c.description}</p>
              <span className="case-open">
                {c.id === live.case_id ? "Return to case" : "Open case"}
                <ArrowRight size={16} />
              </span>
            </div>
          </button>
        ))}
      </div>
    </Dialog>
  );
}
export function ToolsDialog({
  dialog,
  exportImage,
  fetchSvg,
  live,
  setDialog,
  setStateText,
  state,
  stateText,
}) {
  return (
    <Dialog
      open={dialog === "tools"}
      onClose={() => setDialog(null)}
      title="A scene your agent can use"
    >
      <div className="agent-label">
        <span className="status-dot" />
        Tool harness ready<span>No model connected</span>
      </div>
      <p>
        <a href={appUrl("review/index.html")}>Review generated samples</a>
      </p>
      <p className="dialog-description">
        Keep the existing Murdoku function tools. Images provide an optional
        observation of the same state.
      </p>
      <pre className="code-sample">
        {
          'murdoku(action="board")\nmurdoku(action="mark", person="A", cell="c3 d4")\nmurdoku(action="place", person="A", cell="c3")\nmurdoku(action="check")'
        }
      </pre>
      <h3 className="small-heading">Leave a note for the later demo</h3>
      <p className="fine-print">
        A short, public explanation can travel with an action. The journal keeps
        its clue references and focus cells.
      </p>
      <pre className="code-sample">
        {
          'case_note(\n  summary="I want to test this candidate.",\n  clue_ids=["clue-1"],\n  focus_person="A", focus_cells=["c3"]\n)'
        }
      </pre>
      <div className="tool-downloads">
        <button
          className="secondary"
          onClick={() => exportImage("full", "png")}
        >
          <Download size={16} />
          Observation PNG
        </button>
        <button
          className="secondary"
          onClick={() =>
            fetchSvg("full").then((v) =>
              download(v, `${state.case_id}-observation.svg`, "image/svg+xml"),
            )
          }
        >
          <Download size={16} />
          Observation SVG
        </button>
        <button
          className="secondary"
          onClick={async () => {
            const data = await api(`/api/sessions/${live.session_id}`);
            download(
              JSON.stringify(data, null, 2),
              `${state.case_id}-public-state.json`,
            );
          }}
        >
          <FileJson size={16} />
          Public state
        </button>
        <button
          className="secondary"
          onClick={async () =>
            download(
              JSON.stringify(
                await api(`/api/sessions/${live.session_id}/trace`),
                null,
                2,
              ),
              `${state.case_id}-trace.json`,
            )
          }
        >
          <NotebookPen size={16} />
          Session trace
        </button>
      </div>
      <details
        className="state-details"
        onToggle={async (e) => {
          if (e.currentTarget.open)
            setStateText(
              JSON.stringify(
                await api(`/api/sessions/${live.session_id}`),
                null,
                2,
              ),
            );
        }}
      >
        <summary>Inspect the public observation</summary>
        <pre>{stateText}</pre>
      </details>
      <p className="fine-print">
        Session <code>{live.session_id.slice(0, 12)}…</code> · revision{" "}
        {live.revision}. The Python adapter and API examples are in{" "}
        <code>docs/guides/play.md</code>.
      </p>
    </Dialog>
  );
}
export function JournalDialog({ dialog, live, reviewFrame, setDialog, trace }) {
  return (
    <Dialog
      open={dialog === "journal"}
      onClose={() => setDialog(null)}
      title="Your investigation, step by step"
    >
      <p className="dialog-description">
        Recorded operations from this session. Open a step to review its board
        without changing the live case.
      </p>
      <div className="journal-provenance">
        <Clock3 size={15} />
        Local tool history · human and API actions
      </div>
      <div className="journal-list">
        <button className="journal-row" onClick={() => reviewFrame(0)}>
          <span className="step-number">00</span>
          <span>
            <strong>An unopened case</strong>
            <small>The starting board</small>
          </span>
          <ArrowRight size={15} />
        </button>
        {trace?.steps.map((step) => (
          <button
            className="journal-row"
            key={step.index}
            onClick={() => reviewFrame(step.index)}
          >
            <span className="step-number">
              {String(step.index).padStart(2, "0")}
            </span>
            <span>
              <strong>
                {step.action.action}
                {step.action.person ? ` · ${step.action.person}` : ""}
                {step.action.cell ? ` → ${step.action.cell}` : ""}
              </strong>
              <small>
                {step.note?.summary || step.message || "Tool call recorded"}
              </small>
              {!!step.note?.clue_ids?.length && (
                <em>{step.note.clue_ids.join(" · ")}</em>
              )}
            </span>
            <ArrowRight size={15} />
          </button>
        ))}
      </div>
      <button
        className="secondary full-width"
        onClick={() =>
          download(JSON.stringify(trace, null, 2), `${live.case_id}-trace.json`)
        }
      >
        <Download size={16} />
        Save session trace
      </button>
    </Dialog>
  );
}
export function NotesDialog({
  act,
  busy,
  dialog,
  live,
  noteDraft,
  setDialog,
  setNoteDraft,
  showMessage,
}) {
  return (
    <Dialog
      open={dialog === "notes"}
      onClose={() => setDialog(null)}
      title="Notes in the margin"
    >
      <p className="dialog-description">
        Keep your own deductions here. These notes stay with this running
        session.
      </p>
      <textarea
        className="notebook"
        aria-label="Case notes"
        maxLength={8192}
        value={noteDraft}
        onChange={(e) => setNoteDraft(e.target.value)}
        placeholder="What have you noticed?"
      />
      <button
        className="primary full-width"
        disabled={busy || live.done}
        onClick={async () => {
          try {
            await act({
              action: "note",
              text: noteDraft,
            });
            setDialog(null);
            showMessage("Your note has been saved.");
          } catch {}
        }}
      >
        <Check size={16} />
        Save note
      </button>
    </Dialog>
  );
}
export function SubmitDialog({
  busy,
  dialog,
  setDialog,
  state,
  uiAct,
  verdict,
}) {
  return (
    <Dialog
      open={dialog === "submit"}
      onClose={() => setDialog(null)}
      title="Ready to close the case?"
    >
      <p className="dialog-description">
        You have placed all {state.people.length} people. Your verdict is{" "}
        <strong>
          {state.goal_type === "murderer"
            ? state.people.find((p) => p.id === verdict)?.name
            : verdict}
        </strong>
        .
      </p>
      <p>
        The full arrangement and your verdict will be checked together. If you
        need another try, you can keep your board and continue investigating.
      </p>
      <div className="dialog-buttons">
        <button className="secondary" onClick={() => setDialog(null)}>
          Keep investigating
        </button>
        <button
          className="primary"
          disabled={busy}
          onClick={() =>
            uiAct({
              action: "submit",
              ...(state.goal_type === "murderer"
                ? {
                    murderer: verdict,
                  }
                : {
                    answer: verdict,
                  }),
            })
          }
        >
          Submit case
          <ArrowRight size={16} />
        </button>
      </div>
    </Dialog>
  );
}
export function ResultDialog({
  continueAttempt,
  busy,
  dialog,
  live,
  newSession,
  openJournal,
  setDialog,
}) {
  return (
    <Dialog
      open={dialog === "result"}
      onClose={() => setDialog(null)}
      title={
        live.terminal?.score?.solved
          ? "Case closed. Nicely deduced."
          : "There is more to this story."
      }
    >
      <div
        className={`result-seal ${live.terminal?.score?.solved ? "solved" : ""}`}
      >
        {live.terminal?.score?.solved ? (
          <CheckCheck size={44} />
        ) : (
          <Search size={44} />
        )}
      </div>
      <p className="dialog-description">
        {live.terminal?.score?.solved
          ? "Every placement and your verdict agree with the case. The mystery is resolved."
          : `Your board is saved. ${live.terminal?.score?.placement_cells_correct ?? 0} of ${live.people.length} placements were correct; the complete arrangement and verdict are needed to solve the case.`}
      </p>
      <div className="dialog-buttons">
        <button className="secondary" onClick={openJournal}>
          Review the journal
        </button>
        {!live.terminal?.score?.solved && (
          <button className="primary" disabled={busy} onClick={continueAttempt}>
            Keep investigating
            <ArrowRight size={16} />
          </button>
        )}
        <button
          className={live.terminal?.score?.solved ? "primary" : "secondary"}
          onClick={() => newSession(live.case_id)}
        >
          New attempt
          <ArrowRight size={16} />
        </button>
      </div>
    </Dialog>
  );
}
export function RestartDialog({ dialog, live, newSession, setDialog }) {
  return (
    <Dialog
      open={dialog === "restart"}
      onClose={() => setDialog(null)}
      title="Open a fresh page?"
    >
      <p className="dialog-description">
        Start a new attempt at this case. You can save the current session trace
        first.
      </p>
      <div className="dialog-buttons">
        <button
          className="secondary"
          onClick={async () =>
            download(
              JSON.stringify(
                await api(`/api/sessions/${live.session_id}/trace`),
                null,
                2,
              ),
              `${live.case_id}-trace.json`,
            )
          }
        >
          Save trace
        </button>
        <button className="primary" onClick={() => newSession(live.case_id)}>
          Start over
          <RotateCcw size={16} />
        </button>
      </div>
    </Dialog>
  );
}
