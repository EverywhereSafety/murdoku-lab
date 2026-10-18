import React from "react";
import tokens from "../../generated/tokens.json";

const T = tokens.token;

// A standee, drawn with the same geometry as murdoku_lab/visual/art/tokens.py.
export function Token({ person, x, y, selected, clash, guilty, lifted, dim, stampShift = 0 }) {
  const cx = x + T.cx;
  const cy = y + T.cy;
  const b = T.base;
  const pr = T.portrait_r;
  const ring = selected ? "#d8a93f" : person.accent;
  return (
    <g
      className={`pl-token${selected ? " is-selected" : ""}${lifted ? " is-lifted" : ""}${dim ? " is-dim" : ""}`}
      data-person={person.id}
      style={{ transformOrigin: `${cx}px ${y + b.cy}px` }}
    >
      <ellipse cx={cx + 3} cy={y + b.cy + 5} rx={b.rx + 4} ry={b.ry} fill="#1b130e" opacity=".32" />
      <ellipse cx={cx} cy={y + b.cy + 3} rx={b.rx} ry={b.ry} fill="#5a3826" stroke="#2a221d" strokeWidth="1.8" />
      <ellipse cx={cx} cy={y + b.cy} rx={b.rx} ry={b.ry} fill="#9a6847" stroke="#2a221d" strokeWidth="1.8" />
      <rect x={cx - 3} y={cy + T.r - 2} width="6" height={y + b.cy - cy - T.r + 2} fill="#c9a24f" stroke="#2a221d" strokeWidth="1.4" />
      {selected && <circle cx={cx} cy={cy} r={T.r + 7} className="pl-token-glow" />}
      <circle cx={cx} cy={cy} r={T.r} fill="#fbf7ee" stroke={ring} strokeWidth={T.ring} />
      <g
        transform={`translate(${cx - pr} ${cy - pr}) scale(${(2 * pr) / 100})`}
        clipPath="url(#pl-face-clip)"
        dangerouslySetInnerHTML={{ __html: person.face }}
      />
      <circle cx={cx} cy={cy} r={T.r} fill="none" stroke="#2a221d" strokeWidth="1.6" />
      {person.victim && (
        <circle cx={cx} cy={cy} r={T.r + 4.5} fill="none" stroke="#102725" strokeOpacity=".6" strokeWidth="1.8" strokeDasharray="4 4" />
      )}
      <rect x={x + T.badge.x} y={y + T.badge.y} width={T.badge.size} height={T.badge.size} rx={T.badge.rx} fill={person.accent} stroke="#fbf7ee" strokeWidth="2" />
      <text
        x={x + T.badge.x + T.badge.size / 2}
        y={y + T.badge.y + T.badge.size / 2 + 4.6}
        fontSize={T.badge.font}
        fill="#fff"
        textAnchor="middle"
        fontWeight="700"
        fontFamily="var(--mk-font-sans)"
      >
        {person.id}
      </text>
      {clash && (
        <g className="pl-clash">
          <circle cx={cx} cy={cy} r={T.r + 8} fill="none" stroke="#d7654f" strokeWidth="3.4" strokeDasharray="7 5" />
          <circle cx={cx - T.r + 2} cy={cy - T.r + 4} r="11" fill="#d7654f" stroke="#fbf7ee" strokeWidth="2.4" />
          <text x={cx - T.r + 2} y={cy - T.r + 9} fontSize="15" fontWeight="800" fill="#fff" textAnchor="middle">
            !
          </text>
        </g>
      )}
      {guilty && (
        <g className="pl-guilty" transform={`translate(${stampShift} 0) rotate(-14 ${cx} ${cy})`}>
          <rect x={cx - 40} y={cy - 13} width="80" height="26" rx="4" fill="#fbf7ee" fillOpacity=".9" stroke="#d7654f" strokeWidth="3" />
          <text x={cx} y={cy + 6.5} fontSize="16" fontWeight="700" letterSpacing="2" fill="#b14a37" textAnchor="middle" fontFamily="var(--mk-font-mono)">
            GUILTY
          </text>
        </g>
      )}
    </g>
  );
}
