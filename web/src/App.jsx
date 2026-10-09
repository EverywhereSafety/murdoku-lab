import {
  HelpDialog,
  KeyDialog,
  CreditsDialog,
} from "./components/ReferenceDialogs.jsx";
import {
  CasesDialog,
  ToolsDialog,
  JournalDialog,
  NotesDialog,
  SubmitDialog,
  ResultDialog,
  RestartDialog,
} from "./components/SessionDialogs.jsx";
import { EvidencePanel } from "./components/EvidencePanel.jsx";
import { CastPanel } from "./components/CastPanel.jsx";
import { ScenePanel } from "./components/ScenePanel.jsx";
import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  BookOpen,
  Check,
  ChevronDown,
  CircleHelp,
  Flower2,
  Leaf,
  NotebookPen,
  Search,
  ShieldCheck,
  X,
} from "lucide-react";
import {
  appUrl,
  savedSession,
  sessionStorageKey,
  projectLinks,
} from "./urls.js";
import { api, fetchResource } from "./lib/api.js";
import { download, svgToPng } from "./lib/export.js";
import { IconButton } from "./components/Controls.jsx";
export default function App() {
  const [cases, setCases] = useState([]);
  const [live, setLive] = useState(null);
  const liveRef = useRef(null);
  const [review, setReview] = useState(null);
  const state = review || live;
  const [selected, setSelected] = useState("A");
  const [mode, setMode] = useState("mark");
  const [focusMode, setFocusMode] = useState(false);
  const [style, setStyle] = useState("art");
  const [zoom, setZoom] = useState(100);
  const [svg, setSvg] = useState("");
  const [busy, setBusy] = useState(false);
  const busyRef = useRef(false);
  const [toast, setToast] = useState(null);
  const [dialog, setDialog] = useState(null);
  const [hovered, setHovered] = useState(null);
  const [onlySelected, setOnlySelected] = useState(false);
  const [verdict, setVerdict] = useState("");
  const [trace, setTrace] = useState(null);
  const [noteDraft, setNoteDraft] = useState("");
  const [exportMenu, setExportMenu] = useState(false);
  const [stateText, setStateText] = useState("");
  const [loadError, setLoadError] = useState("");
  const [highlightedClues, setHighlightedClues] = useState([]);
  const sceneRef = useRef(null);
  const focusedCellRef = useRef(null);
  const toastTimer = useRef();
  const showMessage = useCallback(
    (message, type = "info", persistent = false) => {
      clearTimeout(toastTimer.current);
      setToast({
        message,
        type,
      });
      if (!persistent)
        toastTimer.current = setTimeout(() => setToast(null), 6000);
    },
    [],
  );
  const applyState = useCallback((data) => {
    if (liveRef.current?.session_id !== data.session_id) {
      setZoom(
        window.matchMedia("(max-width: 600px)").matches &&
          data.scene.width >= 12
          ? 200
          : 100,
      );
    }
    liveRef.current = data;
    setLive(data);
    localStorage.setItem(sessionStorageKey, data.session_id);
  }, []);
  const newSession = useCallback(
    async (caseId) => {
      busyRef.current = true;
      setBusy(true);
      try {
        const data = await api("/api/sessions", {
          case_id: caseId,
        });
        applyState(data);
        setReview(null);
        setSelected(data.people[0].id);
        setMode("mark");
        setVerdict("");
        setDialog(null);
        setHighlightedClues([]);
        setTrace(null);
        setHovered(null);
        setToast(null);
        setSvg("");
        return data;
      } finally {
        busyRef.current = false;
        setBusy(false);
      }
    },
    [applyState],
  );
  useEffect(() => {
    (async () => {
      const list = await api("/api/cases");
      setCases(list.cases);
      const params = new URLSearchParams(location.search);
      const wanted = params.get("case");
      const old = savedSession();
      if (!wanted && old) {
        try {
          const data = await api(`/api/sessions/${old}`);
          applyState(data);
          setSelected(data.people[0].id);
          return;
        } catch {}
      }
      await newSession(
        wanted && list.cases.some((c) => c.id === wanted)
          ? wanted
          : list.cases[0].id,
      );
    })().catch((e) => setLoadError(e.message));
    return () => clearTimeout(toastTimer.current);
  }, [applyState, newSession]);
  const continueAttempt = async () => {
    if (busyRef.current) return;
    busyRef.current = true;
    setBusy(true);
    try {
      const data = await api(
        `/api/sessions/${liveRef.current.session_id}/retry`,
        {},
      );
      applyState(data);
      setReview(null);
      setDialog(null);
      showMessage("Your board and notes are ready. Keep investigating.");
    } catch (error) {
      showMessage(error.message, "error", true);
    } finally {
      busyRef.current = false;
      setBusy(false);
    }
  };
  const act = useCallback(
    async (action, note = null, source = "human") => {
      if (busyRef.current)
        throw new Error(
          "An action is already in progress. Await it before the next tool call.",
        );
      const current = liveRef.current;
      if (!current) throw new Error("The case is still loading.");
      busyRef.current = true;
      setBusy(true);
      try {
        const result = await api(
          `/api/sessions/${current.session_id}/actions`,
          {
            action,
            note,
            source,
            expected_revision: current.revision,
          },
        );
        applyState(result.observation);
        setReview(null);
        if (note) setHighlightedClues(note.clue_ids || []);
        if (action.action === "check")
          showMessage(result.result.observations.join("\n"), "check", true);
        if (result.observation.done) setDialog("result");
        return result;
      } catch (error) {
        showMessage(error.message, "error", true);
        // A parallel tool client may have updated this session; refresh the live revision.
        try {
          applyState(await api(`/api/sessions/${current.session_id}`));
        } catch {}
        throw error;
      } finally {
        busyRef.current = false;
        setBusy(false);
      }
    },
    [applyState, showMessage],
  );
  const uiAct = (action, note) => act(action, note).catch(() => {});
  useEffect(() => {
    if (!focusMode) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previous;
    };
  }, [focusMode]);
  const fetchSvg = useCallback(
    async (scope = "full", renderStyle = style, frame = null) => {
      const current = liveRef.current;
      if (!current) throw new Error("No active session");
      const params = new URLSearchParams({
        style: renderStyle,
      });
      if (frame !== null) params.set("frame", frame);
      const response = await fetchResource(
        appUrl(
          `/api/sessions/${current.session_id}/${scope === "scene" ? "scene" : "observation"}.svg?${params}`,
        ),
      );
      if (!response.ok) throw new Error("Could not render the observation.");
      return response.text();
    },
    [style],
  );
  const exportImage = async (scope, format) => {
    setExportMenu(false);
    try {
      const vector = await fetchSvg(
        scope,
        style,
        review ? review.revision : null,
      );
      const name = `${state.case_id}-${scope}-r${state.revision}.${format}`;
      if (format === "svg") download(vector, name, "image/svg+xml");
      else
        download(
          (await svgToPng(vector, scope === "scene" ? 2 : 1.5)).blob,
          name,
          "image/png",
        );
      showMessage(
        `${scope === "full" ? "Full observation" : "Scene"} saved as ${format.toUpperCase()}.`,
      );
    } catch (error) {
      showMessage(error.message, "error");
    }
  };

  // A compact tool bridge for demos and harness clients. Models still call named tools;
  // nothing here requires pixel coordinates or synthetic mouse events.
  useEffect(() => {
    window.murdokuAgent = {
      observe: async () => api(`/api/sessions/${liveRef.current.session_id}`),
      act: (action, note) => act(action, note, "tool"),
      present: (note) =>
        act(
          {
            action: "present",
          },
          note,
          "tool",
        ),
      newSession,
      render: async ({
        scope = "full",
        format = "svg",
        style: targetStyle = "art",
      } = {}) => {
        const vector = await fetchSvg(scope, targetStyle);
        if (format === "svg") return vector;
        const raster = await svgToPng(vector);
        return {
          data_url: raster.dataUrl,
          width: raster.width,
          height: raster.height,
        };
      },
      trace: async () =>
        api(`/api/sessions/${liveRef.current.session_id}/trace`),
    };
    return () => {
      delete window.murdokuAgent;
    };
  }, [act, newSession, fetchSvg]);
  useEffect(() => {
    if (!state) return;
    const controller = new AbortController();
    const params = new URLSearchParams({
      style,
      revision: state.revision,
    });
    if (selected) params.set("selected", selected);
    if (review) params.set("frame", review.revision);
    const focus = state.last_event?.note?.focus_cells;
    if (review && focus?.length) params.set("focus", focus.join(","));
    fetchResource(
      appUrl(`/api/sessions/${state.session_id}/scene.svg?${params}`),
      {
        signal: controller.signal,
      },
    )
      .then((r) => {
        if (!r.ok) throw new Error("Scene render failed");
        return r.text();
      })
      .then((markup) => {
        focusedCellRef.current =
          document.activeElement?.closest?.("[data-cell]")?.dataset.cell ||
          null;
        setSvg(markup);
      })
      .catch((e) => {
        if (e.name !== "AbortError") showMessage(e.message, "error");
      });
    return () => controller.abort();
  }, [
    state?.session_id,
    state?.revision,
    style,
    selected,
    review?.revision,
    showMessage,
  ]);
  useEffect(() => {
    if (focusedCellRef.current) {
      sceneRef.current
        ?.querySelector(`[data-cell="${focusedCellRef.current}"]`)
        ?.focus({
          preventScroll: true,
        });
      focusedCellRef.current = null;
    }
  }, [svg]);
  useEffect(() => {
    const note = live?.last_event?.note;
    if (note && !review) {
      setHighlightedClues(note.clue_ids || []);
      if (note.focus_person) setSelected(note.focus_person);
    }
  }, [live?.revision, review]);

  // The page follows external tool calls when idle; visible state always comes from the server.
  useEffect(() => {
    if (!live?.session_id) return;
    const timer = setInterval(async () => {
      if (busyRef.current || document.hidden) return;
      try {
        const next = await api(`/api/sessions/${live.session_id}`);
        if (next.revision !== liveRef.current?.revision) applyState(next);
      } catch {}
    }, 1600);
    return () => clearInterval(timer);
  }, [live?.session_id, applyState]);
  const person = state?.people.find((p) => p.id === selected);
  const viewOnly = !!review || !!state?.done;
  const interactCell = useCallback(
    (cell, overridePerson = null) => {
      if (!state || viewOnly || busyRef.current) return;
      const who = overridePerson || selected;
      if (!who) {
        showMessage("Choose a person from the cast first.");
        return;
      }
      if (mode === "place" || overridePerson)
        act({
          action: "place",
          person: who,
          cell,
        }).catch(() => {});
      else if (mode === "mark")
        act({
          action: state.marks[who]?.includes(cell) ? "unmark" : "mark",
          person: who,
          cell,
        }).catch(() => {});
      else if (state.placements[who] === cell)
        act({
          action: "unplace",
          person: who,
        }).catch(() => {});
      else if (state.marks[who]?.includes(cell))
        act({
          action: "unmark",
          person: who,
          cell,
        }).catch(() => {});
      else
        showMessage(
          `No placement or pencil mark for ${state.people.find((p) => p.id === who)?.name} on ${cell}.`,
        );
    },
    [state, viewOnly, selected, mode, act, showMessage],
  );
  useEffect(() => {
    const handleKey = (e) => {
      if (
        !state ||
        dialog ||
        /INPUT|TEXTAREA|SELECT/.test(e.target.tagName) ||
        e.target.isContentEditable
      )
        return;
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z") {
        if (viewOnly) return;
        e.preventDefault();
        if (e.shiftKey && state.can_redo)
          act({
            action: "redo",
          }).catch(() => {});
        else if (!e.shiftKey && state.can_undo)
          act({
            action: "undo",
          }).catch(() => {});
        return;
      }
      if (e.key === "Escape") {
        if (focusMode) setFocusMode(false);
        else setSelected(null);
        return;
      }
      if (/^[1-9]$/.test(e.key)) {
        const p = state.people[Number(e.key) - 1];
        if (p) setSelected(p.id);
        return;
      }
      if (e.key.toLowerCase() === "p") setMode("place");
      if (e.key.toLowerCase() === "m") setMode("mark");
      if (e.key.toLowerCase() === "x") setMode("erase");
      if (
        (e.key === "Delete" || e.key === "Backspace") &&
        selected &&
        !viewOnly &&
        state.placements[selected]
      ) {
        e.preventDefault();
        act({
          action: "unplace",
          person: selected,
        }).catch(() => {});
      }
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [state, dialog, selected, viewOnly, act, focusMode]);
  const gridKey = (e) => {
    const hit = e.target.closest("[data-cell]");
    if (!hit || !state) return;
    const cell = state.scene.cells.find((c) => c.cell === hit.dataset.cell);
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      interactCell(cell.cell, e.key === " " ? selected : null);
      return;
    }
    const offsets = {
      ArrowUp: [-1, 0],
      ArrowDown: [1, 0],
      ArrowLeft: [0, -1],
      ArrowRight: [0, 1],
    };
    if (offsets[e.key]) {
      e.preventDefault();
      const [dr, dc] = offsets[e.key];
      const next = state.scene.cells.find(
        (c) => c.row === cell.row + dr && c.col === cell.col + dc,
      );
      if (next)
        sceneRef.current.querySelector(`[data-cell="${next.cell}"]`).focus();
    }
  };
  const openJournal = async () => {
    setDialog("journal");
    setTrace(await api(`/api/sessions/${live.session_id}/trace`));
  };
  const reviewFrame = async (index) => {
    const result = await api(
      `/api/sessions/${live.session_id}/frames?index=${index}`,
    );
    setReview(result.observation);
    setDialog(null);
    const note = result.observation.last_event?.note;
    setHighlightedClues(note?.clue_ids || []);
    if (note?.focus_person) setSelected(note.focus_person);
  };
  if (!state)
    return (
      <main className="opening">
        <div className="brand-mark">
          <Search />
        </div>
        <h1>
          {loadError ? "The casebook could not open." : "Opening the casebook…"}
        </h1>
        <p>{loadError || "A little patience, detective."}</p>
        {loadError && (
          <button className="primary" onClick={() => location.reload()}>
            Try again
          </button>
        )}
      </main>
    );
  const placedCount = Object.keys(state.placements).length;
  const allPlaced = placedCount === state.people.length;
  const clues = onlySelected
    ? state.clues.filter((c) => c.person === selected)
    : state.clues;
  const hoverInfo = state.scene.cells.find((c) => c.cell === hovered);
  const hoverProp =
    hoverInfo && state.scene.props.find((p) => p.id === hoverInfo.prop);
  const selectedPosition = selected && state.placements[selected];
  const note = state.last_event?.note;
  return (
    <>
      <div className="app-shell">
        <header className="header">
          <button
            className="brand"
            aria-label="Open the casebook"
            onClick={() => setDialog("cases")}
          >
            <span className="brand-mark">
              <img src={appUrl("favicon.svg")} width="38" height="38" alt="" />
            </span>
            <span className="brand-type">
              murdoku<span> lab.</span>
              <small>THE ILLUSTRATED CASEBOOK</small>
            </span>
          </button>
          <nav className="main-nav" aria-label="Casebook navigation">
            <button
              className="nav-link current"
              onClick={() => setDialog("cases")}
            >
              <BookOpen size={16} />
              The casebook
            </button>
            <button className="nav-link" onClick={openJournal}>
              <NotebookPen size={16} />
              Session journal<span className="nav-count">{live.revision}</span>
            </button>
          </nav>
          <div className="header-actions">
            <button
              className="text-button howto"
              onClick={() => setDialog("help")}
            >
              <CircleHelp size={17} />
              How to play
            </button>
          </div>
        </header>

        <section className="case-heading">
          <div>
            <div className="eyebrow">
              <span className="tiny-leaf">
                <Leaf size={14} />
              </span>
              {state.eyebrow}
            </div>
            <h1>
              {state.title}
              <span className="title-period">.</span>
            </h1>
            <p>
              {state.blurb ||
                "Every square has a story. Put the pieces together."}
            </p>
          </div>
          <button className="case-switch" onClick={() => setDialog("cases")}>
            <span className="mini-grid" aria-hidden="true">
              <i />
              <i />
              <i />
              <i />
            </span>
            <span>
              <strong>
                {state.scene.width} × {state.scene.height}
              </strong>
              <small>
                {state.people.length} people · {state.scene.areas.length} areas
              </small>
            </span>
            <ChevronDown size={16} />
          </button>
        </section>

        <main className={`workspace ${focusMode ? "play-focus" : ""}`}>
          <div className="left-column">
            <ScenePanel
              busy={busy}
              exportImage={exportImage}
              exportMenu={exportMenu}
              focusMode={focusMode}
              setFocusMode={setFocusMode}
              gridKey={gridKey}
              hoverInfo={hoverInfo}
              hoverProp={hoverProp}
              interactCell={interactCell}
              live={live}
              mode={mode}
              review={review}
              sceneRef={sceneRef}
              setDialog={setDialog}
              setExportMenu={setExportMenu}
              setHighlightedClues={setHighlightedClues}
              setHovered={setHovered}
              setMode={setMode}
              setReview={setReview}
              setSelected={setSelected}
              selected={selected}
              setStyle={setStyle}
              setZoom={setZoom}
              state={state}
              style={style}
              svg={svg}
              uiAct={uiAct}
              viewOnly={viewOnly}
              zoom={zoom}
            />

            <CastPanel
              mode={mode}
              person={person}
              review={review}
              selected={selected}
              selectedPosition={selectedPosition}
              setHighlightedClues={setHighlightedClues}
              setSelected={setSelected}
              state={state}
              uiAct={uiAct}
              viewOnly={viewOnly}
            />
            {note?.summary && (
              <section className="reason-note">
                <div>
                  <NotebookPen size={17} />
                  <span>Recorded explanation · step {state.revision}</span>
                </div>
                <p>{note.summary}</p>
                {note.clue_ids?.length > 0 && (
                  <small>References: {note.clue_ids.join(", ")}</small>
                )}
              </section>
            )}
          </div>

          <EvidencePanel
            allPlaced={allPlaced}
            busy={busy}
            clues={clues}
            highlightedClues={highlightedClues}
            onlySelected={onlySelected}
            person={person}
            placedCount={placedCount}
            selected={selected}
            setDialog={setDialog}
            setOnlySelected={setOnlySelected}
            setSelected={setSelected}
            setVerdict={setVerdict}
            state={state}
            uiAct={uiAct}
            verdict={verdict}
            viewOnly={viewOnly}
          />
        </main>

        <nav className="project-links" aria-label="Project resources">
          {projectLinks.map(([label, href]) => (
            <a key={label} href={href}>
              {label}
            </a>
          ))}
        </nav>
        <footer className="page-footer">
          <span>
            <Flower2 size={15} />A little observation. A little deduction.
          </span>
          <div>
            <button
              onClick={() => {
                setNoteDraft(live.notebook);
                setDialog("notes");
              }}
            >
              Case notes
            </button>
            <span>·</span>
            <button onClick={() => setDialog("tools")}>For developers</button>
            <span>·</span>
            <button onClick={() => setDialog("credits")}>
              About this edition
            </button>
            <span>·</span>
            <button onClick={() => setDialog("restart")}>Start over</button>
          </div>
        </footer>
      </div>

      {toast && (
        <div className={`toast ${toast.type}`} role="status" aria-live="polite">
          <span className="toast-icon">
            {toast.type === "error" ? (
              <CircleHelp size={18} />
            ) : toast.type === "check" ? (
              <ShieldCheck size={18} />
            ) : (
              <Check size={18} />
            )}
          </span>
          <p>{toast.message}</p>
          <IconButton label="Dismiss message" onClick={() => setToast(null)}>
            <X size={16} />
          </IconButton>
        </div>
      )}

      <CasesDialog
        busy={busy}
        cases={cases}
        dialog={dialog}
        live={live}
        newSession={newSession}
        setDialog={setDialog}
        showMessage={showMessage}
      />

      <HelpDialog dialog={dialog} setDialog={setDialog} state={state} />

      <ToolsDialog
        dialog={dialog}
        exportImage={exportImage}
        fetchSvg={fetchSvg}
        live={live}
        setDialog={setDialog}
        setStateText={setStateText}
        state={state}
        stateText={stateText}
      />

      <JournalDialog
        dialog={dialog}
        live={live}
        reviewFrame={reviewFrame}
        setDialog={setDialog}
        trace={trace}
      />

      <NotesDialog
        act={act}
        busy={busy}
        dialog={dialog}
        live={live}
        noteDraft={noteDraft}
        setDialog={setDialog}
        setNoteDraft={setNoteDraft}
        showMessage={showMessage}
      />

      <KeyDialog dialog={dialog} setDialog={setDialog} state={state} />

      <SubmitDialog
        busy={busy}
        dialog={dialog}
        setDialog={setDialog}
        state={state}
        uiAct={uiAct}
        verdict={verdict}
      />

      <ResultDialog
        continueAttempt={continueAttempt}
        busy={busy}
        dialog={dialog}
        live={live}
        newSession={newSession}
        openJournal={openJournal}
        setDialog={setDialog}
      />

      <RestartDialog
        dialog={dialog}
        live={live}
        newSession={newSession}
        setDialog={setDialog}
      />

      <CreditsDialog dialog={dialog} setDialog={setDialog} />
    </>
  );
}
