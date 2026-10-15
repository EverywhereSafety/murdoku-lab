import React, { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import tokens from "../../generated/tokens.json";
import { colOf, rowOf } from "../engine/rules.js";
import { t } from "../i18n/index.js";
import { Token } from "./Token.jsx";

const { cell: CELL, pad: PAD } = tokens.geometry;
const LONG_PRESS = 420;
const DRAG_SLOP = 9;

const origin = (cell) => [PAD + colOf(cell) * CELL, PAD + rowOf(cell) * CELL];

function Cross({ x, y, size = 16, className, style }) {
  return (
    <path
      className={className}
      style={style}
      d={`M${x - size / 2} ${y - size / 2}l${size} ${size}m0 -${size}l-${size} ${size}`}
      stroke="currentColor"
      strokeWidth="3.4"
      strokeLinecap="round"
    />
  );
}

// The board: the static casebook scene once, and everything that changes on top of it.
export function Board({
  game,
  markup,
  state,
  selected,
  notes,
  highlight,
  clashes,
  crossed,
  ripple,
  reveal,
  frame,
  onTap,
  onDrop,
  onCursor,
}) {
  const width = 2 * PAD + game.width * CELL;
  const height = 2 * PAD + game.height * CELL;
  const svgRef = useRef(null);
  const boxRef = useRef(null);
  const press = useRef(null);
  const [scale, setScale] = useState(1);
  const [hover, setHover] = useState(null);
  const [cursor, setCursor] = useState(null);
  // The cursor ring is for keyboard play; a pointer tap moves it without drawing it.
  const [keyboard, setKeyboard] = useState(false);
  const [drag, setDrag] = useState(null);

  useLayoutEffect(() => {
    const box = boxRef.current;
    if (!box) return undefined;
    const update = () => setScale(box.getBoundingClientRect().width / width || 1);
    update();
    const observer = new ResizeObserver(update);
    observer.observe(box);
    return () => observer.disconnect();
  }, [width]);

  useEffect(() => onCursor?.(cursor), [cursor, onCursor]);

  const at = (event) => {
    const svg = svgRef.current;
    if (!svg) return null;
    const point = svg.createSVGPoint();
    point.x = event.clientX;
    point.y = event.clientY;
    const p = point.matrixTransform(svg.getScreenCTM().inverse());
    const col = Math.floor((p.x - PAD) / CELL);
    const row = Math.floor((p.y - PAD) / CELL);
    if (col < 0 || row < 0 || col >= game.width || row >= game.height) return { x: p.x, y: p.y, cell: null };
    return { x: p.x, y: p.y, cell: `${String.fromCharCode(97 + col)}${row + 1}` };
  };

  const placedAt = useMemo(() => {
    const map = new Map();
    for (const [who, cell] of Object.entries(state.placed)) {
      if (!map.has(cell)) map.set(cell, []);
      map.get(cell).push(who);
    }
    return map;
  }, [state.placed]);

  const down = (event) => {
    if (event.button !== undefined && event.button !== 0) return;
    const hit = at(event);
    if (!hit?.cell) return;
    const person = (placedAt.get(hit.cell) || [])[0] || null;
    press.current = { start: [event.clientX, event.clientY], cell: hit.cell, person, long: false, moved: false };
    press.current.timer = setTimeout(() => {
      if (press.current && !press.current.moved) {
        press.current.long = true;
        onTap(hit.cell, { long: true });
      }
    }, LONG_PRESS);
    svgRef.current?.setPointerCapture?.(event.pointerId);
  };

  const move = (event) => {
    const hit = at(event);
    setHover(hit?.cell ?? null);
    const p = press.current;
    if (!p) return;
    const distance = Math.hypot(event.clientX - p.start[0], event.clientY - p.start[1]);
    if (!p.moved && distance > DRAG_SLOP) {
      p.moved = true;
      clearTimeout(p.timer);
      if (p.person && !p.long) setDrag({ person: p.person, x: hit?.x, y: hit?.y });
    }
    if (p.moved && drag) setDrag({ person: drag.person, x: hit?.x, y: hit?.y });
  };

  const up = (event) => {
    const p = press.current;
    press.current = null;
    if (!p) return;
    clearTimeout(p.timer);
    const hit = at(event);
    if (drag) {
      setDrag(null);
      if (hit?.cell) onDrop(drag.person, hit.cell);
      return;
    }
    if (!p.long && !p.moved && hit?.cell) {
      setCursor(hit.cell);
      setKeyboard(false);
      onTap(hit.cell, { long: false });
    }
  };

  const cancel = () => {
    if (press.current) clearTimeout(press.current.timer);
    press.current = null;
    setDrag(null);
  };

  const key = (event) => {
    const moves = { ArrowUp: [0, -1], ArrowDown: [0, 1], ArrowLeft: [-1, 0], ArrowRight: [1, 0] };
    if (event.key in moves) {
      event.preventDefault();
      setKeyboard(true);
      const [dc, dr] = moves[event.key];
      const current = cursor || (selected && state.placed[selected]) || "a1";
      const col = Math.min(game.width - 1, Math.max(0, colOf(current) + dc));
      const row = Math.min(game.height - 1, Math.max(0, rowOf(current) + dr));
      setCursor(`${String.fromCharCode(97 + col)}${row + 1}`);
    } else if ((event.key === "Enter" || event.key === " ") && cursor) {
      event.preventDefault();
      onTap(cursor, { long: event.shiftKey });
    }
  };

  // Dropping a suspect card from the dossier onto the board.
  const dropCard = (event) => {
    const person = event.dataTransfer.getData("text/murdoku-person");
    const hit = at(event);
    if (person && hit?.cell) {
      event.preventDefault();
      onDrop(person, hit.cell);
    }
  };

  const fontSize = Math.min(21, Math.max(13, 12 / scale));
  const notesBy = useMemo(() => {
    const map = new Map();
    for (const [who, list] of Object.entries(state.marks)) {
      for (const cell of list) {
        if (!map.has(cell)) map.set(cell, []);
        map.get(cell).push(who);
      }
    }
    return map;
  }, [state.marks]);
  const excluded = new Set(selected ? state.exclusions[selected] || [] : []);
  const people = [...Object.entries(state.placed)].sort(([, a], [, b]) => rowOf(a) - rowOf(b) || colOf(a) - colOf(b));
  const highlightCells = highlight?.cells || [];

  return (
    <div className="pl-board" ref={boxRef} style={{ aspectRatio: `${width} / ${height}` }}>
      <div className="pl-scene" aria-hidden="true" dangerouslySetInnerHTML={{ __html: markup }} />
      <svg
        ref={svgRef}
        className={`pl-overlay${notes ? " is-notes" : ""}${drag ? " is-dragging" : ""}`}
        viewBox={`0 0 ${width} ${height}`}
        role="application"
        aria-label={t("board.label", { w: game.width, h: game.height })}
        tabIndex={0}
        onPointerDown={down}
        onPointerMove={move}
        onPointerUp={up}
        onPointerCancel={cancel}
        onPointerLeave={() => setHover(null)}
        onKeyDown={key}
        onDragOver={(event) => event.preventDefault()}
        onDrop={dropCard}
      >
        <defs>
          <clipPath id="pl-face-clip">
            <circle cx="50" cy="50" r="48" />
          </clipPath>
        </defs>
        {reveal && (
          <g className="pl-reveal-veil">
            {game.cells
              .filter((c) => c.area !== reveal.area)
              .map((c) => (
                <rect key={c.cell} x={PAD + c.col * CELL} y={PAD + c.row * CELL} width={CELL} height={CELL} />
              ))}
          </g>
        )}
        <g className="pl-highlight" style={{ color: highlight?.colour }}>
          {highlightCells.map((cell) => {
            const [x, y] = origin(cell);
            return <rect key={cell} x={x + 3} y={y + 3} width={CELL - 6} height={CELL - 6} rx="8" />;
          })}
        </g>
        {crossed && !reveal && (
          <g className="pl-crossed">
            {[...crossed].map((cell) => {
              if (!game.byLabel.get(cell)?.standable) return null;
              const [x, y] = origin(cell);
              return (
                <g key={cell}>
                  <rect x={x} y={y} width={CELL} height={CELL} />
                  <Cross x={x + 84} y={y + 16} size={11} />
                </g>
              );
            })}
          </g>
        )}
        <g className="pl-clash-band">
          {[...clashes.rows].map((row) => (
            <rect key={`r${row}`} x={PAD} y={PAD + row * CELL} width={game.width * CELL} height={CELL} />
          ))}
          {[...clashes.cols].map((col) => (
            <rect key={`c${col}`} x={PAD + col * CELL} y={PAD} width={CELL} height={game.height * CELL} />
          ))}
        </g>
        {ripple && (
          <g className="pl-ripple" key={ripple.key}>
            {ripple.cells.map(({ cell, delay }) => {
              const [x, y] = origin(cell);
              return <Cross key={cell} className="pl-ripple-cross" x={x + 50} y={y + 50} size={26} style={{ animationDelay: `${delay}ms` }} />;
            })}
          </g>
        )}
        <g className="pl-notes">
          {[...notesBy].map(([cell, who]) => {
            if (placedAt.has(cell)) return null;
            const [x, y] = origin(cell);
            const label = who.sort().join(" ");
            return (
              <g key={cell} className={selected && who.includes(selected) ? "is-mine" : ""}>
                <rect x={x + 8} y={y + 70} width={84} height={22} rx="11" />
                <text x={x + 50} y={y + 86} fontSize={Math.min(14, 150 / Math.max(1, label.length))} textAnchor="middle">
                  {label}
                </text>
              </g>
            );
          })}
          {[...excluded].map((cell) => {
            if (placedAt.has(cell)) return null;
            const [x, y] = origin(cell);
            return <Cross key={`x${cell}`} className="pl-excluded" x={x + 50} y={y + 46} size={30} />;
          })}
        </g>
        {hover && !drag && (
          <rect className="pl-hover" x={origin(hover)[0] + 3} y={origin(hover)[1] + 3} width={CELL - 6} height={CELL - 6} rx="8" />
        )}
        {cursor && keyboard && (
          <rect className="pl-cursor" x={origin(cursor)[0] + 4} y={origin(cursor)[1] + 4} width={CELL - 8} height={CELL - 8} rx="9" />
        )}
        <g className="pl-tokens">
          {people.map(([who, cell]) => {
            const [x, y] = origin(cell);
            const stack = placedAt.get(cell) || [];
            const offset = stack.length > 1 ? (stack.indexOf(who) - (stack.length - 1) / 2) * 22 : 0;
            return (
              <Token
                key={who}
                person={game.person.get(who)}
                x={x + offset}
                y={y}
                selected={who === selected}
                clash={clashes.people.has(who)}
                guilty={reveal?.murderer === who}
                stampShift={Math.min(Math.max(x + offset + 50, PAD + 46), width - PAD - 46) - (x + offset + 50)}
                lifted={drag?.person === who}
                dim={Boolean(reveal) && game.areaOf.get(cell) !== reveal.area}
              />
            );
          })}
        </g>
        {reveal?.line && (
          <path
            className="pl-reveal-line"
            d={`M${origin(reveal.line[0])[0] + 50} ${origin(reveal.line[0])[1] + 38}L${origin(reveal.line[1])[0] + 50} ${origin(reveal.line[1])[1] + 38}`}
          />
        )}
        <g className="pl-axes" fontSize={fontSize} fill={frame.axis} stroke={frame.halo} style={{ "--halo": `${Math.max(2.4, 3.2 / scale)}px` }}>
          {Array.from({ length: game.width }, (_, c) => (
            <g key={`col${c}`} className={hover && colOf(hover) === c ? "is-active" : ""}>
              <text x={PAD + c * CELL + 50} y={PAD / 2 + fontSize * 0.36} textAnchor="middle">
                {String.fromCharCode(65 + c)}
              </text>
              <text x={PAD + c * CELL + 50} y={height - PAD / 2 + fontSize * 0.36} textAnchor="middle">
                {String.fromCharCode(65 + c)}
              </text>
            </g>
          ))}
          {Array.from({ length: game.height }, (_, r) => (
            <g key={`row${r}`} className={hover && rowOf(hover) === r ? "is-active" : ""}>
              <text x={PAD / 2} y={PAD + r * CELL + 50 + fontSize * 0.36} textAnchor="middle">
                {r + 1}
              </text>
              <text x={width - PAD / 2} y={PAD + r * CELL + 50 + fontSize * 0.36} textAnchor="middle">
                {r + 1}
              </text>
            </g>
          ))}
        </g>
        {drag && drag.x != null && (
          <g className="pl-ghost" transform={`translate(${drag.x - 50} ${drag.y - 60})`}>
            <Token person={game.person.get(drag.person)} x={0} y={0} selected />
          </g>
        )}
      </svg>
    </div>
  );
}
