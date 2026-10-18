import React, { useEffect, useState } from "react";
import { assetUrl } from "../data.js";
import { caseStatus } from "../engine/persist.js";
import { addDays, msToMidnight, stats, streaks } from "../engine/daily.js";
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
  return (
    <span className="pl-countdown">
      {t("daily.next", { time: span(left) })}
    </span>
  );
}

export function Flame({ size = 18 }) {
  return (
    <svg
      viewBox="0 0 24 24"
      width={size}
      height={size}
      aria-hidden="true"
      className="pl-flame"
    >
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

function dateLabel(
  date,
  options = { weekday: "short", month: "short", day: "numeric" },
) {
  return new Intl.DateTimeFormat("en", options).format(
    new Date(`${date}T12:00:00`),
  );
}

export function TodayCard({ entry, onOpen, day, locked = false }) {
  const status = caseStatus(entry);
  const isToday = !day || entry.date === day;
  const action = locked
    ? t("daily.opens", {
        date: dateLabel(entry.date, { month: "short", day: "numeric" }),
      })
    : status?.solved
      ? t(isToday ? "daily.solvedToday" : "daily.replay")
      : t(isToday ? "daily.play" : "daily.playCase");
  return (
    <button
      type="button"
      className={`pl-card is-daily${isToday ? " is-today" : ""}`}
      style={{ "--accent": entry.accent || "#0b7469" }}
      onClick={() => onOpen(entry.id)}
      disabled={locked}
    >
      <span className="pl-card-thumb">
        <img
          src={assetUrl(`daily/${entry.thumb}`)}
          alt=""
          width="320"
          height="320"
        />
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
          <span className={`pl-pill is-${entry.difficulty.band}`}>
            {entry.difficulty.label}
          </span>
          <span>{entry.size}</span>
          <span>{entry.setting.name}</span>
        </span>
        <span className="pl-today-cta">
          {action}
          {!locked && "\u00a0→"}
        </span>
      </span>
    </button>
  );
}

// Selecting a date only browses the season; it never changes the real unlock date.
export function DailyPicker({ manifest, day, unlock, onOpen }) {
  const [selectedId, setSelectedId] = useState(null);
  const days = manifest?.days || [];
  if (!days.length) return null;
  const todayIndex = days.findIndex((entry) => entry.date === day);
  const latest = days.findLastIndex((entry) => entry.date <= day);
  const chosen = days.findIndex((entry) => entry.id === selectedId);
  const index =
    chosen >= 0 ? chosen : todayIndex >= 0 ? todayIndex : Math.max(0, latest);
  const entry = days[index];
  const locked = entry.date > day && !unlock;
  const status = caseStatus(entry);
  const label = `${dateLabel(entry.date, { weekday: "long", month: "long", day: "numeric", year: "numeric" })} · #${entry.n} · ${t(locked ? "daily.lockedStatus" : status?.solved ? "daily.solvedStatus" : "daily.availableStatus")}`;
  const choose = (n) =>
    setSelectedId(days[n]?.date === day ? null : days[n]?.id || null);
  return (
    <section className="pl-daily-picker" aria-label={t("daily.picker")}>
      <header className="pl-picker-heading">
        <span className="pl-eyebrow">
          {t("daily.picker")} · #{entry.n}
        </span>
        <button
          type="button"
          className="pl-picker-today"
          onClick={() => setSelectedId(null)}
          disabled={todayIndex < 0 || entry.date === day}
        >
          {t("daily.todayButton")}
        </button>
      </header>
      <div className="pl-date-controls">
        <button
          type="button"
          aria-label={t("daily.previous")}
          onClick={() => choose(index - 1)}
          disabled={index === 0}
        >
          <span aria-hidden="true">‹</span>
        </button>
        <time dateTime={entry.date} aria-live="polite">
          {dateLabel(entry.date)}
        </time>
        <button
          type="button"
          aria-label={t("daily.forward")}
          onClick={() => choose(index + 1)}
          disabled={index === days.length - 1}
        >
          <span aria-hidden="true">›</span>
        </button>
      </div>
      <TodayCard entry={entry} day={day} locked={locked} onOpen={onOpen} />
      <div className="pl-date-slider">
        <input
          type="range"
          aria-label={t("daily.choose")}
          aria-valuetext={label}
          min="0"
          max={Math.max(0, days.length - 1)}
          step="1"
          value={index}
          disabled={days.length === 1}
          onChange={(event) => choose(Number(event.target.value))}
        />
        <div className="pl-date-endpoints">
          <span>
            {dateLabel(days[0].date, { month: "short", day: "numeric" })}
          </span>
          <span>
            {dateLabel(days.at(-1).date, { month: "short", day: "numeric" })}
          </span>
        </div>
      </div>
      {days.some((item) => item.date === addDays(day, 1)) && <Countdown />}
    </section>
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
          const state = status?.solved
            ? "is-solved"
            : future
              ? "is-future"
              : entry.date === day
                ? "is-today"
                : "is-missed";
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
              {status?.solved ? (
                <Stars count={status.stars} size={11} />
              ) : (
                <span className="pl-day-size">{entry.size}</span>
              )}
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
      <button
        type="button"
        className="pl-secondary"
        onClick={() => onOpen(null)}
      >
        {t("nav.back")}
      </button>
    </div>
  );
}
