import React, { useEffect, useState } from "react";
import { assetUrl } from "../data.js";
import { caseStatus } from "../engine/persist.js";
import { msToMidnight, stats, streaks } from "../engine/daily.js";
import { t } from "../i18n/index.js";
import { Mascot, Stars } from "./ui.jsx";

function span(ms) {
  const minutes = Math.max(0, Math.round(ms / 60000));
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return h ? `${h}h ${String(m).padStart(2, "0")}m` : `${m}m`;
}

export function Countdown() {
  const [left, setLeft] = useState(msToMidnight);
  useEffect(() => {
    const timer = setInterval(() => setLeft(msToMidnight()), 30000);
    return () => clearInterval(timer);
  }, []);
  return <span className="pl-countdown">{t("daily.next", { time: span(left) })}</span>;
}

export function Flame({ size = 18 }) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} aria-hidden="true" className="pl-flame">
      <path d="M12 2c1 4 6 6 6 12a6 6 0 0 1-12 0c0-3 2-5 3-6 0 2 1 3 2 3 0-3-1-6 1-9Z" />
    </svg>
  );
}

export function StatsRow({ record, day }) {
  const streak = streaks(record, day);
  const s = stats(record);
  return (
    <div className="pl-stats">
      <span className="pl-streak">
        <Flame /> {t("daily.streak", { n: streak.current })}
      </span>
      <span>
        <b>{s.solved}</b> {t("stats.solved")}
      </span>
      <span>
        <b>{s.perfect}</b> {t("stats.perfect")}
      </span>
      <span>
        <b>{streak.best}</b> {t("stats.best")}
      </span>
    </div>
  );
}

export function TodayCard({ entry, onOpen }) {
  const status = caseStatus(entry);
  return (
    <button type="button" className="pl-card is-big is-today" style={{ "--accent": entry.accent || "#0b7469" }} onClick={() => onOpen(entry.id)}>
      <span className="pl-card-thumb">
        <img src={assetUrl(`daily/${entry.thumb}`)} alt="" width="320" height="320" />
        {status?.solved && (
          <span className="pl-card-stamp">
            <Stars count={status.stars} size={16} />
          </span>
        )}
      </span>
      <span className="pl-card-body">
        <span className="pl-card-setting">
          #{entry.n} · {t(`weekday.${entry.weekday}`)}
          {entry.special ? ` · ${entry.special}` : ""}
        </span>
        <strong>{entry.title}</strong>
        <span className="pl-card-blurb">{entry.blurb}</span>
        <span className="pl-card-meta">
          <span className={`pl-pill is-${entry.difficulty.band}`}>{entry.difficulty.label}</span>
          <span>{entry.size}</span>
          <span>{entry.setting.name}</span>
        </span>
        <span className="pl-today-cta">{status?.solved ? t("daily.solvedToday") : t("daily.play")} →</span>
      </span>
    </button>
  );
}

// The season as a calendar: solved days carry their stars, missed days are marked, future
// days stay locked unless the preview unlocks them.
export function Archive({ manifest, day, unlock, onOpen }) {
  const first = new Date(`${manifest.days[0].date}T12:00:00Z`).getUTCDay();
  const lead = (first + 6) % 7;
  return (
    <section className="pl-archive" aria-label={t("daily.archive")}>
      <header>
        <h2>{t("daily.archive")}</h2>
      </header>
      <div className="pl-calendar">
        {["M", "T", "W", "T", "F", "S", "S"].map((d, i) => (
          <span key={i} className="pl-calendar-head">
            {d}
          </span>
        ))}
        {Array.from({ length: lead }, (_, i) => (
          <span key={`lead${i}`} />
        ))}
        {manifest.days.map((entry) => {
          const status = caseStatus(entry);
          const future = entry.date > day;
          const open = !future || unlock;
          const state = status?.solved ? "is-solved" : future ? "is-future" : entry.date === day ? "is-today" : "is-missed";
          return (
            <button
              key={entry.n}
              type="button"
              className={`pl-day ${state}`}
              disabled={!open}
              onClick={() => onOpen(entry.id)}
              title={`#${entry.n} · ${entry.date} · ${entry.title}`}
              style={{ "--accent": entry.accent || "#0b7469" }}
            >
              <span className="pl-day-n">#{entry.n}</span>
              <span className="pl-day-date">{Number(entry.date.slice(8))}</span>
              {status?.solved ? <Stars count={status.stars} size={11} /> : <span className="pl-day-size">{entry.size}</span>}
            </button>
          );
        })}
      </div>
    </section>
  );
}

export function Locked({ entry, onOpen }) {
  return (
    <div className="pl-empty">
      <Mascot pose="thinking" size={120} />
      <h2>{t("daily.locked", { n: entry.n, date: entry.date })}</h2>
      <p>{t("daily.lockedBody")}</p>
      <Countdown />
      <button type="button" className="pl-secondary" onClick={() => onOpen(null)}>
        {t("nav.back")}
      </button>
    </div>
  );
}
