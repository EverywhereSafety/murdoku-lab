import React, { useCallback, useEffect, useMemo, useRef, useState, useSyncExternalStore } from "react";
import tokens from "../../generated/tokens.json";
import { useBoardNavigation } from "../../lib/use-board-view.js";
import { Board } from "../board/Board.jsx";
import { loadCase, loadLibrary, loadScene } from "../data.js";
import { ActionError } from "../engine/reducer.js";
import { nextHint } from "../engine/hints.js";
import { dropPerson, noteTap, placeTap } from "../engine/intents.js";
import { colOf, conflicts, crossedFor, rowOf } from "../engine/rules.js";
import { createStore } from "../engine/store.js";
import { t } from "../i18n/index.js";
import { feedback, reducedMotion } from "../lib/fx.js";
import { funnel } from "../lib/funnel.js";
import { shareSquares, streaks } from "../engine/daily.js";
import { CoachCard, useCoach } from "./Coach.jsx";
import { Countdown, Flame } from "./Daily.jsx";
import { Dossier } from "./Dossier.jsx";
import { Dialog, Face, Mascot, Stars, Toast, formatTime } from "./ui.jsx";

const MANOR = tokens.settings.manor.frame;

function useNarrow() {
  const query = "(max-width: 899px)";
  const [narrow, setNarrow] = useState(() => globalThis.matchMedia?.(query).matches ?? false);
  useEffect(() => {
    const list = globalThis.matchMedia?.(query);
    if (!list) return undefined;
    const change = () => setNarrow(list.matches);
    list.addEventListener("change", change);
    return () => list.removeEventListener("change", change);
  }, []);
  return narrow;
}

function highlightCells(game, state, ref) {
  if (!ref) return null;
  if (ref.kind === "area")
    return { cells: game.cells.filter((c) => c.area === ref.id).map((c) => c.cell), colour: "#0b7469" };
  if (ref.kind === "prop")
    return { cells: game.props.find((p) => p.id === ref.id)?.cells || [], colour: "#b98a3e" };
  if (ref.kind === "terrain")
    return { cells: game.cells.filter((c) => c.terrain === ref.id).map((c) => c.cell), colour: "#397eb8" };
  const person = game.person.get(ref.id);
  const cells = state.placed[ref.id] ? [state.placed[ref.id]] : state.marks[ref.id] || [];
  return { cells, colour: person?.accent || "#0b7469" };
}

function dailyShare(game, finished, progress, url) {
  const d = game.bundle.daily;
  const verdict = progress.wrong_verdicts ? `⚖️🔁${progress.wrong_verdicts}` : "⚖️✅";
  const stars = "★".repeat(finished.stars) + "☆".repeat(3 - finished.stars);
  const hints = progress.hints.length;
  return [
    `Murdoku Daily #${d.n} · ${t(`weekday.${d.weekday}`).slice(0, 3)} · ${game.meta.size} ${game.meta.difficulty.label}`,
    `${shareSquares(game, progress.hints)} ${verdict}`,
    `${stars} · ${hints ? t("reveal.hints", { n: hints }) : t("reveal.noHints")}`,
    url,
  ].join("\n");
}

function shareText(game, finished, hints, url) {
  const stars = "★".repeat(finished.stars) + "☆".repeat(3 - finished.stars);
  const help = hints ? t("reveal.hints", { n: hints }) : t("reveal.noHints");
  const lines = [
    `Murdoku Lab · ${game.meta.title}`,
    `${game.meta.setting.name} · ${game.meta.size} · ${game.meta.difficulty.label}`,
    `${stars} · ${help} · ${formatTime(finished.elapsed_ms)}`,
    url,
  ];
  return lines.join("\n");
}

function ActionBar({ snapshot, notes, onNotes, onUndo, onRedo, onHint, accuse, onAccuse, onClues, narrow, finished, onSummary }) {
  return (
    <div className="pl-actions" role="toolbar" aria-label="Board actions">
      <button type="button" className="pl-tool" onClick={onUndo} disabled={!snapshot.state.undo.length || finished}>
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 7 4 12l5 5M4 12h11a5 5 0 0 1 0 10h-2" /></svg>
        <span>{t("action.undo")}</span>
      </button>
      <button type="button" className="pl-tool" onClick={onRedo} disabled={!snapshot.state.redo.length || finished}>
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m15 7 5 5-5 5M20 12H9a5 5 0 0 0 0 10h2" /></svg>
        <span>{t("action.redo")}</span>
      </button>
      <button
        type="button"
        className={`pl-tool${notes ? " is-on" : ""}`}
        aria-pressed={notes}
        onClick={onNotes}
        disabled={finished}
      >
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 20h4L19 9l-4-4L4 16v4ZM13 7l4 4" /></svg>
        <span>{notes ? t("action.notesOn") : t("action.notes")}</span>
      </button>
      {narrow && (
        <button type="button" className="pl-tool" onClick={onClues}>
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 4h11l3 3v13H5zM8 10h8M8 14h8M8 18h5" /></svg>
          <span>{t("action.clues")}</span>
        </button>
      )}
      <button type="button" className="pl-tool" onClick={onHint} disabled={finished}>
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.6 10.8c.6.5 1 1.2 1 2V16h5.2v-.2c0-.8.4-1.5 1-2A6 6 0 0 0 12 3Z" /></svg>
        <span>{t("action.hint")}</span>
      </button>
      <span className="pl-actions-spacer" />
      {finished ? (
        <button type="button" className="pl-accuse is-ready" onClick={onSummary}>
          {t("reveal.closed")}
        </button>
      ) : (
        <button
          type="button"
          className={`pl-accuse${accuse.ready ? " is-ready" : ""}`}
          onClick={onAccuse}
          disabled={!accuse.ready}
        >
          {accuse.label}
        </button>
      )}
    </div>
  );
}

// Narrow screens: the selected suspect's statement, or the hint or coach card in its place, so
// the board, the card and the suspects all fit on one screen.
function SuspectTray({ game, state, selected, clashes, onSelect, coached, guide }) {
  const person = selected ? game.person.get(selected) : null;
  const statement = selected ? game.clues.filter((c) => c.person === selected) : [];
  return (
    <div className="pl-tray">
      {guide ||
        (person && statement.length > 0 && (
          <p className="pl-tray-bubble" style={{ "--accent": person.accent }}>
            <strong>{person.name.split(" ")[0]}:</strong> {statement.map((c) => c.text).join(" ")}
          </p>
        ))}
      <div className="pl-tray-row" role="listbox" aria-label={t("case.suspects")}>
        {game.people.map((p) => (
          <button
            key={p.id}
            type="button"
            role="option"
            aria-selected={p.id === selected}
            className={`pl-chip${p.id === selected ? " is-selected" : ""}${state.placed[p.id] ? " is-placed" : ""}${clashes.people.has(p.id) ? " is-clash" : ""}${coached === p.id && p.id !== selected ? " is-coached" : ""}`}
            style={{ "--accent": p.accent }}
            onClick={() => onSelect(p.id)}
          >
            <Face person={p} size={40} />
            <span>{p.name.split(" ")[0]}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

function VerdictDialog({ open, game, state, onClose, onAnswer, compact }) {
  const victim = game.people.find((p) => p.victim);
  const first = victim?.name.split(" ")[0] ?? "the victim";
  return (
    <Dialog open={open} onClose={onClose} labelledBy="pl-verdict-title" className="pl-verdict">
      <Mascot pose="thinking" size={88} className="pl-dialog-mascot" />
      <h2 id="pl-verdict-title">{t(`verdict.title.${game.goalType}`, { victim: first })}</h2>
      {game.goalType === "murderer" ? (
        <>
          <p>{t("verdict.body.murderer", { victim: first })}</p>
          <div className="pl-lineup">
            {game.people
              .filter((p) => !p.victim)
              .map((p) => (
                <button
                  key={p.id}
                  type="button"
                  className="pl-lineup-card"
                  style={{ "--accent": p.accent }}
                  onClick={() => onAnswer(p.id)}
                  aria-label={t("verdict.accuse", { name: p.name })}
                >
                  <Face person={p} size={compact ? 48 : 72} />
                  <span>{compact ? p.name.split(" ")[0] : p.name}</span>
                  {!compact && <small>{t("verdict.accuse", { name: p.name.split(" ")[0] })}</small>}
                </button>
              ))}
          </div>
        </>
      ) : (
        <>
          <p>{t("verdict.body.victim_cell", { victim: first, cell: (state.placed[victim?.id] || "?").toUpperCase() })}</p>
          <div className="pl-dialog-buttons">
            <button type="button" className="pl-primary" onClick={() => onAnswer(state.placed[victim?.id])}>
              {t("verdict.close")}
            </button>
          </div>
        </>
      )}
      <div className="pl-dialog-buttons">
        <button type="button" className="pl-secondary" onClick={onClose}>
          {t("verdict.cancel")}
        </button>
      </div>
    </Dialog>
  );
}

function OutcomeDialog({ result, game, onClose }) {
  const victim = game.people.find((p) => p.victim)?.name.split(" ")[0] ?? "the victim";
  const key = result ? `outcome.${result.outcome}` : "";
  return (
    <Dialog open={Boolean(result)} onClose={onClose} labelledBy="pl-outcome-title" className="pl-outcome">
      <Mascot pose="pointing" size={84} className="pl-dialog-mascot" />
      <h2 id="pl-outcome-title">{t(key, { victim })}</h2>
      {result && t(`${key}.more`, { victim }) !== `${key}.more` && <p>{t(`${key}.more`, { victim })}</p>}
      <div className="pl-dialog-buttons">
        <button type="button" className="pl-primary" onClick={onClose}>
          {t("outcome.continue")}
        </button>
      </div>
    </Dialog>
  );
}

// Hint and coach cards sit beside the board (below it on narrow screens), never over it, so
// they cannot hide anyone standing on the board.
function HintCard({ hint, game, onMore, onFix, onClose }) {
  if (!hint) return null;
  const canMore = !hint.reveal;
  return (
    <div className="pl-hint" role="status" aria-live="polite">
      <Mascot pose={hint.reveal ? "pointing" : "thinking"} size={64} />
      <div className="pl-hint-body">
        <p>{t(hint.key, hint.vars)}</p>
        <div className="pl-hint-buttons">
          {hint.fix && (
            <button type="button" className="pl-primary" onClick={onFix}>
              {t("hint.place", { name: game.person.get(hint.fix.person).name.split(" ")[0] })}
            </button>
          )}
          {canMore && (
            <button type="button" className="pl-secondary" onClick={onMore}>
              {t("hint.more")}
            </button>
          )}
          <button type="button" className="pl-link" onClick={onClose}>
            {t("hint.close")}
          </button>
        </div>
      </div>
    </div>
  );
}

function RevealDialog({ open, game, finished, hints, progress, streak, onClose, onNext, onLibrary }) {
  const [copied, setCopied] = useState(false);
  if (!finished) return null;
  const secret = game.secret();
  const murderer = secret.murderer ? game.person.get(secret.murderer) : null;
  const victim = game.people.find((p) => p.victim);
  const room = game.areas.find((a) => a.id === secret.victim_area)?.name ?? "";
  const daily = game.bundle.daily;
  const url = daily && game.bundle.share?.url ? new URL(game.bundle.share.url, window.location.href).href : window.location.href;
  const share = async () => {
    const text = daily ? dailyShare(game, finished, progress, url) : shareText(game, finished, hints, url);
    try {
      if (navigator.share && matchMedia("(pointer: coarse)").matches) await navigator.share({ text });
      else await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2400);
    } catch {
      // The share sheet was dismissed.
    }
  };
  return (
    <Dialog open={open} onClose={onClose} labelledBy="pl-reveal-title" className="pl-reveal">
      <div className="pl-stamp" aria-hidden="true">
        {t("reveal.closed")}
      </div>
      <Mascot pose="celebrating" size={104} className="pl-dialog-mascot" />
      <p className="pl-eyebrow">{game.meta.setting.name}</p>
      <h2 id="pl-reveal-title">{game.meta.title}</h2>
      {murderer ? (
        <div className="pl-culprit" style={{ "--accent": murderer.accent }}>
          <Face person={murderer} size={64} />
          <div>
            <strong>{t("reveal.murderer", { name: murderer.name })}</strong>
            <span>{t("reveal.where", { victim: victim?.name ?? "", room })}</span>
          </div>
        </div>
      ) : (
        <p className="pl-culprit-plain">{t("reveal.where", { victim: victim?.name ?? "", room })}</p>
      )}
      {secret.epilogue && <p className="pl-epilogue">{secret.epilogue}</p>}
      <div className="pl-score">
        <Stars count={finished.stars} size={28} />
        <span>{hints ? t("reveal.hints", { n: hints }) : t("reveal.noHints")}</span>
        <span>{t("reveal.time", { time: formatTime(finished.elapsed_ms) })}</span>
      </div>
      {daily && (
        <div className="pl-score pl-daily-score">
          {streak > 0 && (
            <span className="pl-streak">
              <Flame /> {t("daily.streak", { n: streak })}
            </span>
          )}
          <Countdown />
        </div>
      )}
      <div className="pl-dialog-buttons">
        <button type="button" className="pl-primary" onClick={share}>
          {copied ? t("reveal.copied") : t("reveal.share")}
        </button>
        {onNext && (
          <button type="button" className="pl-secondary" onClick={onNext}>
            {t("reveal.next")}
          </button>
        )}
        <button type="button" className="pl-secondary" onClick={onLibrary}>
          {t("reveal.library")}
        </button>
        <button type="button" className="pl-link" onClick={onClose}>
          {t("reveal.board")}
        </button>
      </div>
      <aside className="pl-funnel">
        <strong>{t("funnel.title")}</strong>
        <p>{t("funnel.body")}</p>
        <a href={funnel("blog", "reveal")} target="_blank" rel="noopener">
          {t("funnel.cta")} →
        </a>
      </aside>
    </Dialog>
  );
}

function Playing({ game, markup, settings, onOpen, onSolved, profile, day }) {
  const store = useMemo(() => createStore(game), [game]);
  const snapshot = useSyncExternalStore(store.subscribe, store.getSnapshot);
  const { state, progress } = snapshot;
  const narrow = useNarrow();
  const finished = progress.finished;
  const firstOpen = () => game.personIds.find((p) => !(p in state.placed)) || game.personIds[0];
  const [selected, setSelected] = useState(firstOpen);
  const [notes, setNotes] = useState(false);
  const [ref, setRef] = useState(null);
  const [pinned, setPinned] = useState(null);
  const [ripple, setRipple] = useState(null);
  const [toast, setToast] = useState(null);
  const [verdictOpen, setVerdictOpen] = useState(false);
  const [outcome, setOutcome] = useState(null);
  const [revealOpen, setRevealOpen] = useState(false);
  const [sheet, setSheet] = useState(false);
  const [hint, setHint] = useState(null);
  const coach = useCoach(game, state, selected, finished);
  const [next, setNext] = useState(null);
  const [zoom, setZoom] = useState(100);
  const { scrollRef, changeZoom, fitBoard } = useBoardNavigation({ zoom, setZoom, sessionId: game.id });
  // Up to 8×8 a phone-wide board keeps squares at least 44px, so zoom is only offered above.
  const zoomable = game.width > (narrow ? 8 : 9);
  const toastTimer = useRef(null);

  const say = useCallback((text, tone) => {
    clearTimeout(toastTimer.current);
    setToast({ id: Date.now(), text, tone });
    toastTimer.current = setTimeout(() => setToast(null), 2200);
  }, []);

  useEffect(() => {
    loadLibrary()
      .then((index) => {
        const ids = index.cases.map((c) => c.id);
        const i = ids.indexOf(game.id);
        setNext(i >= 0 && i + 1 < ids.length ? ids[i + 1] : null);
      })
      .catch(() => setNext(null));
  }, [game.id]);

  // Time counts only while the page is visible and the case is open.
  useEffect(() => {
    if (finished) return undefined;
    let last = performance.now();
    const timer = setInterval(() => {
      const now = performance.now();
      if (document.visibilityState === "visible") store.tick(now - last);
      last = now;
    }, 1000);
    return () => clearInterval(timer);
  }, [store, finished]);

  const clashes = useMemo(() => conflicts(game, state.placed), [game, state.placed]);
  const crossed = useMemo(
    () => (selected && !finished ? crossedFor(game, state.placed, selected) : null),
    [game, state.placed, selected, finished],
  );
  const placedCount = game.personIds.filter((p) => p in state.placed).length;
  const ready = placedCount === game.personIds.length && clashes.people.size === 0;
  const accuse = {
    ready,
    label:
      placedCount < game.personIds.length
        ? t("action.accuse.count", { placed: placedCount, total: game.personIds.length })
        : clashes.people.size
          ? t("action.accuse.conflicts")
          : t(`action.accuse.${game.goalType}`),
  };

  const run = (intent) => {
    if (intent.toast) say(t(intent.toast.key, intent.toast.vars), intent.effect === "reject" ? "is-warn" : "");
    if (intent.select !== undefined && intent.select !== null) setSelected(intent.select);
    if (intent.effect) feedback(intent.effect === "select" ? "note" : intent.effect, settings);
    if (!intent.actions.length) return;
    try {
      store.dispatch(intent.actions);
    } catch (error) {
      if (!(error instanceof ActionError)) throw error;
      say(error.message, "is-warn");
      return;
    }
    if (intent.effect === "place" && intent.placed && !reducedMotion()) {
      const at = intent.actions[0].cell;
      const cells = game.cells
        .filter((c) => c.cell !== at && (c.row === rowOf(at) || c.col === colOf(at)) && c.standable)
        .map((c) => ({ cell: c.cell, delay: 40 * (Math.abs(c.row - rowOf(at)) + Math.abs(c.col - colOf(at))) }));
      setRipple({ key: Date.now(), cells });
    }
  };

  const tap = (cell, { long }) => {
    if (finished) return;
    // A long press does the opposite of a tap; the Notes toggle (or the old-habit setting) swaps them.
    const noteMode = settings.notesFirst ? notes === long : notes !== long;
    run(noteMode ? noteTap(game, state, selected, cell) : placeTap(game, state, selected, cell));
  };

  const drop = (person, cell) => {
    if (finished) return;
    run(dropPerson(game, state, person, cell));
  };

  const history = (action) => {
    try {
      store.dispatch([{ action }]);
      say(t(action === "undo" ? "toast.undo" : "toast.redo"));
    } catch (error) {
      if (!(error instanceof ActionError)) throw error;
    }
  };

  useEffect(() => {
    const keys = (event) => {
      if (verdictOpen || outcome || revealOpen || event.target.closest?.("input, textarea, dialog")) return;
      const k = event.key.toLowerCase();
      if ((event.metaKey || event.ctrlKey) && k === "z") {
        event.preventDefault();
        history(event.shiftKey ? "redo" : "undo");
      } else if (event.metaKey || event.ctrlKey || event.altKey) {
        return;
      } else if (k === "n") setNotes((v) => !v);
      else if (k === "escape") setSelected(null);
      else {
        const id = game.personIds.find((p) => p.toLowerCase() === k);
        if (id) setSelected(id);
      }
    };
    window.addEventListener("keydown", keys);
    return () => window.removeEventListener("keydown", keys);
  });

  const answer = (value) => {
    setVerdictOpen(false);
    const result = store.submit(value);
    if (result.solved) {
      const after = store.getSnapshot().progress;
      onSolved?.(game, after.finished, after);
      feedback("solved", settings);
      setTimeout(() => setRevealOpen(true), reducedMotion() ? 0 : 900);
    } else {
      feedback("wrong", settings);
      setOutcome(result);
    }
  };

  const showHint = () => {
    if (finished) return;
    const given = nextHint(game, state, progress.hints);
    store.hint(given);
    setHint(given);
    if (given.focus.person) setSelected(given.focus.person);
    feedback("note", settings);
  };

  const fixHint = () => {
    if (!hint?.fix) return;
    run(dropPerson(game, state, hint.fix.person, hint.fix.cell));
    setHint(null);
  };

  const review = (clueId, reviewed) => {
    try {
      store.dispatch([{ action: "review_clue", clue_id: clueId, reviewed }]);
    } catch (error) {
      if (!(error instanceof ActionError)) throw error;
    }
  };

  const onRef = (value, pin) => {
    if (pin) setPinned((current) => (current && value && current.id === value.id && current.kind === value.kind ? null : value));
    else setRef(value);
  };

  const secret = finished ? game.secret() : null;
  const reveal = secret
    ? {
        murderer: secret.murderer,
        area: secret.victim_area,
        line: secret.murderer ? [state.placed[secret.murderer], state.placed[game.victim]] : null,
      }
    : null;
  const frame = tokens.settings[game.meta.setting.id]?.frame || MANOR;
  const dossier = (compact) => (
    <Dossier
      game={game}
      state={state}
      selected={selected}
      clashes={clashes}
      onSelect={(id) => {
        setSelected(id);
        if (compact) setSheet(false);
      }}
      onRef={onRef}
      onReview={review}
      hinted={hint?.focus?.clue}
      coached={coach?.focus?.person}
      compact={compact}
    />
  );

  const guide = coach ? (
    <CoachCard coach={coach} onLibrary={() => onOpen(null)} />
  ) : (
    <HintCard hint={finished ? null : hint} game={game} onMore={showHint} onFix={fixHint} onClose={() => setHint(null)} />
  );

  // The verdict panel leaves the board in view; on narrow screens the board scrolls up above it.
  const openVerdict = () => {
    const top = scrollRef.current?.getBoundingClientRect().top;
    if (narrow && top != null) window.scrollBy({ top: top - 64, behavior: reducedMotion() ? "auto" : "smooth" });
    setVerdictOpen(true);
  };

  return (
    <div className="pl-case" data-setting={game.meta.setting.id || "manor"}>
      {narrow && (
        <header className="pl-case-head">
          <p className="pl-eyebrow">{game.meta.setting.name}</p>
          <h1>{game.meta.title}</h1>
        </header>
      )}
      <div className="pl-case-grid">
        <section className="pl-stage" aria-label={game.meta.title}>
          <div className={`pl-board-frame${zoom > 100 ? " is-zoomed" : ""}`} ref={scrollRef}>
            <div className="pl-board-zoom" style={{ width: `${zoom}%` }}>
            <Board
              game={game}
              markup={markup}
              state={state}
              selected={finished ? null : selected}
              notes={notes}
              highlight={
                coach?.focus?.cells
                  ? { cells: coach.focus.cells, colour: "#d8a93f" }
                  : hint?.focus?.cells
                  ? { cells: hint.focus.cells, colour: hint.reveal ? "#d7654f" : "#d8a93f" }
                  : highlightCells(game, state, pinned || ref)
              }
              clashes={clashes}
              crossed={crossed}
              ripple={ripple}
              reveal={reveal}
              frame={frame}
              onTap={tap}
              onDrop={drop}
            />
            </div>
          </div>
          {zoomable && (
            <div className="pl-zoom" role="group" aria-label="Zoom">
              <button type="button" onClick={() => changeZoom(zoom - 25)} aria-label={t("action.zoomOut")} disabled={zoom <= 100}>
                −
              </button>
              <button type="button" onClick={fitBoard} aria-label={t("action.fit")} disabled={zoom === 100}>
                {zoom}%
              </button>
              <button type="button" onClick={() => changeZoom(zoom + 25)} aria-label={t("action.zoomIn")} disabled={zoom >= 250}>
                +
              </button>
            </div>
          )}
          {narrow && (
            <SuspectTray
              game={game}
              state={state}
              selected={selected}
              clashes={clashes}
              onSelect={setSelected}
              coached={coach?.focus?.person}
              guide={coach || (hint && !finished) ? guide : null}
            />
          )}
          <ActionBar
            snapshot={snapshot}
            notes={notes}
            onNotes={() => setNotes((v) => !v)}
            onUndo={() => history("undo")}
            onRedo={() => history("redo")}
            onHint={showHint}
            accuse={accuse}
            onAccuse={openVerdict}
            onClues={() => setSheet(true)}
            narrow={narrow}
            finished={Boolean(finished)}
            onSummary={() => setRevealOpen(true)}
          />
          {settings.timer && !finished && <p className="pl-timer">{formatTime(progress.elapsed_ms)}</p>}
        </section>
        {!narrow && (
          <aside className="pl-side">
            {guide}
            {dossier(false)}
          </aside>
        )}
      </div>
      {narrow && (
        <Dialog open={sheet} onClose={() => setSheet(false)} labelledBy="pl-sheet-title" className="pl-sheet">
          <h2 id="pl-sheet-title" className="pl-sheet-title">
            {t("action.clues")}
          </h2>
          {dossier(true)}
        </Dialog>
      )}
      <VerdictDialog open={verdictOpen} game={game} state={state} onClose={() => setVerdictOpen(false)} onAnswer={answer} compact={narrow} />
      <OutcomeDialog result={outcome} game={game} onClose={() => setOutcome(null)} />
      <RevealDialog
        open={revealOpen}
        game={game}
        finished={finished}
        hints={progress.hints.length}
        progress={progress}
        streak={game.bundle.daily ? streaks(profile?.daily || {}, day).current : 0}
        onClose={() => setRevealOpen(false)}
        onNext={next ? () => onOpen(next) : null}
        onLibrary={() => onOpen(null)}
      />
      <Toast toast={toast} />
    </div>
  );
}

export function CaseView({ id, settings, onOpen, onSolved, profile, day }) {
  const [loaded, setLoaded] = useState(null);
  const [error, setError] = useState(null);
  useEffect(() => {
    let live = true;
    setLoaded(null);
    setError(null);
    loadCase(id)
      .then(async (game) => {
        const markup = await loadScene(game, settings.night ? "night" : "day");
        if (live) setLoaded({ game, markup });
      })
      .catch((e) => live && setError(e));
    return () => {
      live = false;
    };
  }, [id, settings.night]);
  if (error)
    return (
      <div className="pl-empty">
        <Mascot pose="thinking" size={120} />
        <p>{t("case.error")}</p>
        <button type="button" className="pl-secondary" onClick={() => onOpen(null)}>
          {t("nav.back")}
        </button>
      </div>
    );
  if (!loaded)
    return (
      <div className="pl-empty" aria-busy="true">
        <Mascot pose="idle" size={110} className="pl-bob" />
        <p>{t("case.loading")}</p>
      </div>
    );
  return (
    <Playing
      key={loaded.game.id}
      game={loaded.game}
      markup={loaded.markup}
      settings={settings}
      onOpen={onOpen}
      onSolved={onSolved}
      profile={profile}
      day={day}
    />
  );
}
