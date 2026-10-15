import React, {
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  ArrowDownToLine,
  ArrowRight,
  BookOpen,
  Download,
  Eraser,
  Grid2X2,
  House,
  Maximize,
  MousePointer2,
  Palette,
  Paintbrush,
  Pencil,
  Plus,
  Minus,
  Redo2,
  Undo2,
  Clock3,
  X,
} from "lucide-react";
import { useBoardNavigation, useBoardGuides } from "../lib/use-board-view.js";
import { assistMarkup } from "../lib/board-assist.js";
import { IconButton } from "./Controls.jsx";
const BoardArtwork = React.memo(function BoardArtwork({ markup }) {
  return <div dangerouslySetInnerHTML={{ __html: markup }} />;
});

export function ScenePanel({
  busy,
  exportImage,
  exportMenu,
  focusMode,
  setFocusMode,
  gridKey,
  hoverInfo,
  hoverProp,
  interactCell,
  live,
  mode,
  review,
  sceneRef,
  setDialog,
  setExportMenu,
  setHighlightedClues,
  setHovered,
  setMode,
  setReview,
  setSelected,
  selected,
  setStyle,
  setZoom,
  state,
  style,
  svg,
  uiAct,
  viewOnly,
  zoom,
}) {
  const [assist, setAssist] = useState(true);
  const [showUnderlay, setShowUnderlay] = useState(false);
  const { scrollRef, changeZoom, fitBoard } = useBoardNavigation({
    zoom,
    setZoom,
    sessionId: state.session_id,
    onPinch: () => {
      cancelPress();
      press.current.consumed = true;
    },
  });
  const boardMarkup = useMemo(
    () => assistMarkup(svg, state, selected, assist),
    [svg, state, selected, assist],
  );
  useBoardGuides({ sceneRef, hoverInfo, boardMarkup, state });
  const focusedCell = useRef(null);
  useLayoutEffect(() => {
    const active = document.activeElement;
    if (
      focusedCell.current &&
      (active === document.body || sceneRef.current?.contains(active))
    ) {
      sceneRef.current
        ?.querySelector(`[data-cell="${focusedCell.current}"]`)
        ?.focus({ preventScroll: true });
    }
  }, [boardMarkup, sceneRef]);
  const press = useRef({ timer: null, consumed: false });
  const cancelPress = () => {
    clearTimeout(press.current.timer);
    press.current.timer = null;
  };
  useEffect(() => {
    return cancelPress;
  }, [mode, selected, viewOnly, busy, state.session_id]);
  return (
    <section className="scene-panel" aria-label="Interactive crime scene">
      <div className="scene-heading">
        <div className="scene-title">
          <House size={18} />
          <span>{state.setting}</span>
          <span className="floor-label">FLOOR PLAN</span>
        </div>
        <div className="scene-heading-actions">
          <IconButton
            label={focusMode ? "Return to page (Esc)" : "Focus on the board"}
            active={focusMode}
            onClick={() => setFocusMode(!focusMode)}
          >
            <Maximize size={16} />
          </IconButton>
          <IconButton
            label="Open object and terrain key"
            onClick={() => setDialog("key")}
          >
            <BookOpen size={16} />
          </IconButton>
          <div className="segmented view-switch" aria-label="Map style">
            <button
              aria-pressed={style === "casebook"}
              className={style === "casebook" ? "active" : ""}
              onClick={() => setStyle("casebook")}
            >
              <House size={14} />
              <span>Casebook</span>
            </button>
            <button
              aria-pressed={style === "art"}
              className={style === "art" ? "active" : ""}
              onClick={() => setStyle("art")}
            >
              <Palette size={14} />
              <span>Illustrated</span>
            </button>
            <button
              aria-pressed={style === "diagram"}
              className={style === "diagram" ? "active" : ""}
              onClick={() => setStyle("diagram")}
            >
              <Grid2X2 size={14} />
              <span>Diagram</span>
            </button>
            <button
              title="Classic skin"
              aria-label="Classic"
              aria-pressed={style === "classic"}
              className={style === "classic" ? "active" : ""}
              onClick={() => setStyle("classic")}
            >
              <Paintbrush size={14} />
              <span>Classic</span>
            </button>
          </div>
          <div className="export-anchor">
            <IconButton
              label="Export image"
              active={exportMenu}
              onClick={() => setExportMenu((v) => !v)}
            >
              <Download size={16} />
            </IconButton>
            {exportMenu && (
              <div className="export-menu">
                <span className="menu-label">SAVE AN OBSERVATION</span>
                <button onClick={() => exportImage("full", "png")}>
                  Full case · PNG
                  <ArrowDownToLine size={14} />
                </button>
                <button onClick={() => exportImage("scene", "png")}>
                  Scene only · PNG
                  <ArrowDownToLine size={14} />
                </button>
                <button onClick={() => exportImage("full", "svg")}>
                  Full case · SVG
                  <ArrowDownToLine size={14} />
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
      <label className="board-assist-toggle">
        <input
          type="checkbox"
          checked={assist}
          onChange={(e) => setAssist(e.target.checked)}
        />
        Show row and column exclusions
        <span>× marks rows and columns occupied by placed people</span>
      </label>
      {review && (
        <div className="review-banner">
          <Clock3 size={15} />
          <span>
            Reviewing step {review.revision} of {live.revision}
          </span>
          <button
            onClick={() => {
              setReview(null);
              setHighlightedClues([]);
            }}
          >
            Return to live case
            <ArrowRight size={14} />
          </button>
        </div>
      )}
      <label className="board-assist-toggle">
        <input
          type="checkbox"
          checked={showUnderlay}
          onChange={(event) => setShowUnderlay(event.target.checked)}
        />
        View underlying objects
        <span>Temporarily hide people and notes · placements are kept</span>
      </label>
      <div className="board-location" aria-live="polite">
        <strong>{hoverInfo?.cell.toUpperCase() || "Explore the board"}</strong>
        <span>
          {hoverInfo
            ? state.scene.areas.find((area) => area.id === hoverInfo.area)?.name
            : "Ctrl + scroll to zoom · Shift + drag to pan"}
        </span>
        <span className="manual-exclusion-key">
          × Your exclusions for{" "}
          {state.people.find((p) => p.id === selected)?.name ||
            "selected person"}
        </span>
      </div>
      <div className="map-layout">
        <div className="tool-rail" aria-label="Placement tools">
          <IconButton
            label="Place person (P)"
            active={mode === "place"}
            disabled={viewOnly}
            onClick={() => setMode("place")}
          >
            <MousePointer2 size={19} />
          </IconButton>
          <IconButton
            label="Pencil candidates (M)"
            active={mode === "mark"}
            disabled={viewOnly}
            onClick={() => setMode("mark")}
          >
            <Pencil size={18} />
          </IconButton>
          <IconButton
            label="Exclude square for selected person (E)"
            active={mode === "exclude"}
            disabled={viewOnly}
            onClick={() => setMode("exclude")}
          >
            <X size={18} />
          </IconButton>
          <IconButton
            label="Erase selected person's mark or placement (X)"
            active={mode === "erase"}
            disabled={viewOnly}
            onClick={() => setMode("erase")}
          >
            <Eraser size={19} />
          </IconButton>
          <span className="rail-divider" />
          <IconButton
            label="Undo (Ctrl+Z)"
            disabled={!state.can_undo || busy || viewOnly}
            onClick={() =>
              uiAct({
                action: "undo",
              })
            }
          >
            <Undo2 size={18} />
          </IconButton>
          <IconButton
            label="Redo (Ctrl+Shift+Z)"
            disabled={!state.can_redo || busy || viewOnly}
            onClick={() =>
              uiAct({
                action: "redo",
              })
            }
          >
            <Redo2 size={18} />
          </IconButton>
        </div>
        <div
          className="board-scroll"
          data-testid="board-scroll"
          ref={scrollRef}
        >
          <div
            className={`board-frame ${showUnderlay ? "show-underlay" : ""}`}
            style={{
              width: `${zoom}%`,
            }}
            aria-busy={busy}
            ref={sceneRef}
            onFocusCapture={(e) => {
              focusedCell.current =
                e.target.closest("[data-cell]")?.dataset.cell || null;
              if (focusedCell.current) setHovered(focusedCell.current);
            }}
            onClick={(e) => {
              if (showUnderlay) return;
              if (press.current.consumed) {
                press.current.consumed = false;
                return;
              }
              const hit = e.target.closest("[data-cell]");
              if (hit) interactCell(hit.dataset.cell);
            }}
            onPointerDown={(e) => {
              cancelPress();
              press.current.consumed = false;
              if (e.shiftKey && e.button === 0) {
                press.current.pan = {
                  x: e.clientX,
                  y: e.clientY,
                  left: scrollRef.current.scrollLeft,
                  top: scrollRef.current.scrollTop,
                };
                press.current.consumed = true;
                e.currentTarget.setPointerCapture(e.pointerId);
                e.preventDefault();
                return;
              }
              const hit = e.target.closest("[data-cell]");
              if (
                e.button !== 0 ||
                !hit ||
                mode !== "mark" ||
                viewOnly ||
                showUnderlay ||
                busy ||
                !selected
              )
                return;
              const cell = hit.dataset.cell;
              press.current.x = e.clientX;
              press.current.y = e.clientY;
              press.current.timer = setTimeout(() => {
                press.current.consumed = true;
                interactCell(cell, selected);
              }, 450);
            }}
            onPointerMove={(e) => {
              if (press.current.pan) {
                scrollRef.current.scrollLeft =
                  press.current.pan.left - (e.clientX - press.current.pan.x);
                scrollRef.current.scrollTop =
                  press.current.pan.top - (e.clientY - press.current.pan.y);
                return;
              }
              if (
                press.current.timer &&
                Math.hypot(
                  e.clientX - press.current.x,
                  e.clientY - press.current.y,
                ) > 10
              ) {
                press.current.consumed = true;
                cancelPress();
              }
            }}
            onPointerUp={() => {
              press.current.pan = null;
              cancelPress();
            }}
            onPointerCancel={() => {
              press.current.pan = null;
              cancelPress();
            }}
            onPointerLeave={cancelPress}
            onContextMenu={(e) => {
              if (mode === "mark") e.preventDefault();
            }}
            onMouseOver={(e) => {
              const hit = e.target.closest("[data-cell]");
              if (hit) setHovered(hit.dataset.cell);
            }}
            onMouseLeave={() => setHovered(null)}
            onKeyDown={(event) => {
              if (!showUnderlay) gridKey(event);
            }}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              if (showUnderlay) return;
              const hit = e.target.closest("[data-cell]");
              const who = e.dataTransfer.getData("application/murdoku-person");
              if (hit && state.people.some((p) => p.id === who)) {
                interactCell(hit.dataset.cell, who);
                setSelected(who);
              }
            }}
          >
            <BoardArtwork markup={boardMarkup} />
          </div>
        </div>
      </div>
      <div className="map-legend" aria-label="Area legend">
        {state.scene.areas.map((a) => (
          <span key={a.id}>
            <i
              style={{
                background: a.color,
              }}
            />
            <b>{String(a.number).padStart(2, "0")}</b>
            {a.name}
          </span>
        ))}
      </div>
      <div className="map-footer">
        <span className="cell-info">
          {hoverInfo ? (
            <>
              <b>{hoverInfo.cell}</b>
              <span>
                {state.scene.areas.find((a) => a.id === hoverInfo.area)?.name}
              </span>
              <span>{hoverProp?.name || hoverInfo.terrain}</span>
              <strong
                className={
                  hoverInfo.standable ? "open-square" : "blocked-square"
                }
              >
                {hoverInfo.standable ? "Standable" : "Blocked"}
              </strong>
            </>
          ) : (
            <>
              <span className="blocked-key">×</span>
              <span>Small cross = obstacle</span>
              <span className="footer-dot">·</span>
              <span>Other squares are standable</span>
            </>
          )}
        </span>
        <div className="zoom-controls">
          <IconButton
            label="Zoom out"
            disabled={zoom <= 75}
            onClick={() => changeZoom(zoom - 25)}
          >
            <Minus size={13} />
          </IconButton>
          <span>{zoom}%</span>
          <IconButton
            label="Zoom in"
            disabled={zoom >= 250}
            onClick={() => changeZoom(zoom + 25)}
          >
            <Plus size={13} />
          </IconButton>
          <IconButton label="Fit the board" onClick={fitBoard}>
            <Maximize size={13} />
          </IconButton>
        </div>
      </div>
    </section>
  );
}
