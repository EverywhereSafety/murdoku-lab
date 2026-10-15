import React, { useEffect, useMemo, useState } from "react";
import tokens from "../../generated/tokens.json";
import { assetUrl, loadLibrary } from "../data.js";
import { caseStatus } from "../engine/persist.js";
import { t } from "../i18n/index.js";
import { todaysCase } from "../engine/daily.js";
import { Archive, Countdown, StatsRow, TodayCard } from "./Daily.jsx";
import { Mascot, Stars } from "./ui.jsx";

function CaseCard({ entry, onOpen, big = false }) {
  const status = caseStatus(entry);
  const [lo, hi] = entry.difficulty.minutes;
  return (
    <button
      type="button"
      className={`pl-card${big ? " is-big" : ""}${status?.solved ? " is-solved" : ""}`}
      style={{ "--accent": entry.accent || "#0b7469" }}
      onClick={() => onOpen(entry.id)}
    >
      <span className="pl-card-thumb">
        <img src={assetUrl(`cases/${entry.thumb}`)} alt="" loading="lazy" width="320" height="320" />
        {status?.solved && (
          <span className="pl-card-stamp">
            <Stars count={status.stars} size={16} />
          </span>
        )}
        {status && !status.solved && <span className="pl-card-flag">{t("library.inProgress")}</span>}
      </span>
      <span className="pl-card-body">
        <span className="pl-card-setting">{entry.setting.name}</span>
        <strong>{entry.title}</strong>
        {big && <span className="pl-card-blurb">{entry.blurb}</span>}
        <span className="pl-card-meta">
          <span className={`pl-pill is-${entry.difficulty.band || "classic"}`}>{entry.difficulty.label}</span>
          <span>{entry.size}</span>
          <span>{t("library.minutes", { lo, hi })}</span>
        </span>
      </span>
    </button>
  );
}

export function Library({ onOpen, manifest, day, unlock, profile }) {
  const [index, setIndex] = useState(null);
  const [error, setError] = useState(null);
  useEffect(() => {
    loadLibrary().then(setIndex, setError);
  }, []);
  const groups = useMemo(() => {
    if (!index) return [];
    const bySetting = new Map();
    for (const entry of index.cases) {
      if (entry.kind === "tutorial") continue;
      const key = entry.kind === "classic" ? "classic" : entry.setting.id;
      if (!bySetting.has(key)) bySetting.set(key, []);
      bySetting.get(key).push(entry);
    }
    return [...bySetting].sort(([a], [b]) => (a === "classic") - (b === "classic"));
  }, [index]);
  if (error)
    return (
      <div className="pl-empty">
        <Mascot pose="thinking" size={120} />
        <p>{t("library.empty")}</p>
      </div>
    );
  if (!index) return <div className="pl-empty" aria-busy="true" />;
  const solved = index.cases.filter((c) => caseStatus(c)?.solved).length;
  const training = index.cases.find((c) => c.kind === "tutorial");
  const fresh = training && !caseStatus(training)?.solved;
  const featured = fresh
    ? training
    : index.cases.find((c) => c.kind === "themed" && !caseStatus(c)?.solved) || index.cases[0];
  const todays = manifest ? todaysCase(manifest, day) : null;
  return (
    <div className="pl-library">
      <section className="pl-hero">
        <div className="pl-hero-copy">
          <Mascot pose="pointing" size={132} className="pl-hero-mascot" />
          <h1>{t("brand.name")}</h1>
          <p>{t("brand.tagline")}</p>
          {manifest ? (
            <StatsRow record={profile.daily || {}} day={day} />
          ) : (
            <p className="pl-progress-line">{t("library.progress", { solved, total: index.cases.length })}</p>
          )}
        </div>
        {todays ? (
          <div className="pl-hero-feature">
            <p className="pl-eyebrow">
              {t("daily.today")} · <Countdown />
            </p>
            <TodayCard entry={todays} onOpen={onOpen} />
          </div>
        ) : (
          featured && (
            <div className="pl-hero-feature">
              <p className="pl-eyebrow">{fresh ? t("library.training") : t("library.featured")}</p>
              <CaseCard entry={featured} onOpen={onOpen} big />
            </div>
          )
        )}
      </section>
      {todays && fresh && (
        <button type="button" className="pl-training" onClick={() => onOpen(training.id)}>
          <Mascot pose="pointing" size={56} />
          <span>
            <strong>{t("library.training")}</strong>
            <span>{training.title}</span>
          </span>
          <span aria-hidden="true">→</span>
        </button>
      )}
      {manifest && <Archive manifest={manifest} day={day} unlock={unlock} onOpen={onOpen} />}
      {groups.map(([key, entries]) => {
        const setting = tokens.settings[key];
        const name = key === "classic" ? t("library.classics") : setting?.name || entries[0].setting.name;
        return (
          <section key={key} className="pl-shelf" data-setting={key}>
            <header>
              <h2>{name}</h2>
              {setting && <p>{setting.eyebrow}</p>}
            </header>
            <div className="pl-shelf-row">
              {entries.map((entry) => (
                <CaseCard key={entry.id} entry={entry} onOpen={onOpen} />
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}
