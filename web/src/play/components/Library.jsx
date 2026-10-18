import React, { useEffect, useMemo, useState } from "react";
import { assetUrl, loadLibrary } from "../data.js";
import { caseStatus, nextCase } from "../engine/persist.js";
import { t } from "../i18n/index.js";
import { funnel } from "../lib/funnel.js";
import { Archive, DailyPicker, StatsRow } from "./Daily.jsx";
import { Mascot, Stars } from "./ui.jsx";

function CaseCard({ entry, onOpen }) {
  const status = caseStatus(entry);
  const [lo, hi] = entry.difficulty.minutes;
  return (
    <button
      type="button"
      className={`pl-card${status?.solved ? " is-solved" : ""}`}
      style={{ "--accent": entry.accent || "#0b7469" }}
      onClick={() => onOpen(entry.id)}
    >
      <span className="pl-card-thumb">
        <img
          src={assetUrl(`cases/${entry.thumb}`)}
          alt=""
          loading="lazy"
          width="320"
          height="320"
        />
        {status?.solved && (
          <span className="pl-card-stamp">
            <Stars count={status.stars} size={16} />
          </span>
        )}
        {status && !status.solved && (
          <span className="pl-card-flag">{t("library.inProgress")}</span>
        )}
      </span>
      <span className="pl-card-body">
        <span className="pl-card-setting">{entry.setting.name}</span>
        <strong>{entry.title}</strong>
        <span className="pl-card-meta">
          <span className={`pl-pill is-${entry.difficulty.band || "classic"}`}>
            {entry.difficulty.label}
          </span>
          <span>{entry.size}</span>
          <span>
            {hi >= 120
              ? t("library.hours", {
                  lo: Math.round(lo / 60),
                  hi: Math.round(hi / 60),
                })
              : t("library.minutes", { lo, hi })}
          </span>
        </span>
      </span>
    </button>
  );
}

export function Library({ onOpen, manifest, day, unlock, profile }) {
  const [index, setIndex] = useState(null);
  const [error, setError] = useState(null);
  const [setting, setSetting] = useState("");
  const [size, setSize] = useState("");
  const [limit, setLimit] = useState(6);
  useEffect(() => {
    loadLibrary().then(setIndex, setError);
  }, []);
  const generated = useMemo(
    () =>
      index?.cases
        .filter((c) => c.kind === "themed")
        .sort(
          (a, b) =>
            parseInt(a.size) - parseInt(b.size) ||
            a.setting.name.localeCompare(b.setting.name),
        ) || [],
    [index],
  );
  const settings = useMemo(
    () => [...new Map(generated.map((c) => [c.setting.id, c.setting.name]))],
    [generated],
  );
  const sizes = useMemo(
    () =>
      [...new Set(generated.map((c) => c.size))].sort(
        (a, b) => parseInt(a) - parseInt(b),
      ),
    [generated],
  );
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
  const recommended = nextCase(index.cases);
  const featured =
    recommended ||
    generated[0] ||
    index.cases.find((c) => c.kind !== "tutorial") ||
    training;
  const featuredStatus = featured && caseStatus(featured);
  const playLabel = t(
    featuredStatus && !featuredStatus.solved
      ? "library.resume"
      : !recommended
        ? "library.revisit"
        : featured?.kind === "themed"
          ? "library.playGenerated"
          : "library.playCase",
  );
  const filtered = generated.filter(
    (c) => (!setting || c.setting.id === setting) && (!size || c.size === size),
  );
  const classics = index.cases.filter((c) => c.kind === "classic");
  return (
    <div className="pl-library">
      <section className="pl-hero" aria-labelledby="workshop-title">
        <div className="pl-hero-copy">
          <p className="pl-eyebrow">{t("library.kicker")}</p>
          <h1 id="workshop-title">{t("library.headline")}</h1>
          <p className="pl-hero-intro">{t("library.intro")}</p>
          <div className="pl-hero-actions">
            {featured && (
              <button
                className="pl-primary"
                onClick={() => onOpen(featured.id)}
              >
                {playLabel} <span aria-hidden="true">→</span>
              </button>
            )}
            <a
              className="pl-secondary"
              href={generated.length ? "#collection" : "#classics"}
            >
              {t("library.browse")}
            </a>
          </div>
          <p className="pl-collection-note">
            {generated.length
              ? t("library.ready", { n: generated.length })
              : t("library.progress", { solved, total: index.cases.length })}
          </p>
          {fresh && (
            <button
              className="pl-link pl-first-case"
              onClick={() => onOpen(training.id)}
            >
              {t("library.training")} →
            </button>
          )}
        </div>
        {manifest?.days?.length ? (
          <DailyPicker
            manifest={manifest}
            day={day}
            unlock={unlock}
            onOpen={onOpen}
          />
        ) : (
          featured && (
            <button
              className="pl-featured-case"
              style={{ "--accent": featured.accent }}
              onClick={() => onOpen(featured.id)}
              aria-label={`${playLabel}: ${featured.title}`}
            >
              <span className="pl-featured-caption">
                <span className="pl-eyebrow">{t("library.heroCase")}</span>
                <span>
                  {featured.size} · {featured.difficulty.label}
                </span>
              </span>
              <img
                src={assetUrl(`cases/${featured.id}.day.svg`)}
                alt=""
                width="440"
                height="440"
              />
              <span className="pl-featured-title">
                <span>
                  <small>{featured.setting.name}</small>
                  <strong>{featured.title}</strong>
                </span>
                <span aria-hidden="true">↗</span>
              </span>
            </button>
          )
        )}
      </section>

      <section className="pl-workshop" aria-labelledby="quality-title">
        <header>
          <h2 id="quality-title">{t("workshop.title")}</h2>
          <a href={funnel("quality", "library")} target="_blank" rel="noopener">
            {t("workshop.evidence")} ↗
          </a>
        </header>
        <div className="pl-workshop-points">
          {["solution", "rhythm", "variety"].map((key, i) => (
            <div key={key}>
              <span className="pl-step" aria-hidden="true">
                0{i + 1}
              </span>
              <div>
                <h3>{t(`workshop.${key}`)}</h3>
                <p>{t(`workshop.${key}Body`)}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {generated.length > 0 && (
        <section
          className="pl-collection"
          id="collection"
          aria-labelledby="collection-title"
        >
          <header className="pl-section-head">
            <div>
              <p className="pl-eyebrow">{t("library.generated")}</p>
              <h2 id="collection-title">{t("library.collection")}</h2>
              <p>{t("library.collectionBody")}</p>
            </div>
            <div className="pl-filters">
              <label>
                {t("library.setting")}
                <select
                  aria-label={t("library.setting")}
                  value={setting}
                  onChange={(e) => {
                    setSetting(e.target.value);
                    setLimit(6);
                  }}
                >
                  <option value="">{t("library.allSettings")}</option>
                  {settings.map(([id, name]) => (
                    <option value={id} key={id}>
                      {name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                {t("library.size")}
                <select
                  aria-label={t("library.size")}
                  value={size}
                  onChange={(e) => {
                    setSize(e.target.value);
                    setLimit(6);
                  }}
                >
                  <option value="">{t("library.allSizes")}</option>
                  {sizes.map((n) => (
                    <option key={n}>{n}</option>
                  ))}
                </select>
              </label>
            </div>
          </header>
          <div className="pl-shelf-row">
            {filtered.slice(0, limit).map((entry) => (
              <CaseCard key={entry.id} entry={entry} onOpen={onOpen} />
            ))}
          </div>
          <div className="pl-collection-bottom">
            <p role="status">
              {filtered.length
                ? t("library.showing", {
                    shown: Math.min(limit, filtered.length),
                    total: filtered.length,
                  })
                : t("library.noMatches")}
            </p>
            {filtered.length > limit && (
              <button
                className="pl-secondary"
                onClick={() => setLimit(limit + 6)}
              >
                {t("library.more")} <span aria-hidden="true">↓</span>
              </button>
            )}
          </div>
        </section>
      )}

      {manifest?.days?.length > 0 && (
        <section className="pl-daily-section" aria-labelledby="daily-title">
          <div className="pl-daily-intro">
            <p className="pl-eyebrow">{t("daily.track")}</p>
            <h2 id="daily-title">{t("daily.archive")}</h2>
            <p>{t("library.dailyBody")}</p>
            <StatsRow record={profile.daily || {}} day={day} />
          </div>
          {training && (
            <button
              type="button"
              className="pl-training"
              onClick={() => onOpen(training.id)}
            >
              <Mascot pose="pointing" size={64} />
              <span>
                <strong>{t("library.firstCase")}</strong>
                <span>{t("library.trainingBody")}</span>
              </span>
              <span aria-hidden="true">→</span>
            </button>
          )}
          <details className="pl-season">
            <summary>{t("library.calendar")}</summary>
            <Archive
              manifest={manifest}
              day={day}
              unlock={unlock}
              onOpen={onOpen}
            />
          </details>
        </section>
      )}

      {classics.length > 0 && (
        <section
          className="pl-shelf"
          id="classics"
          aria-labelledby="classics-title"
        >
          <header className="pl-section-head">
            <div>
              <h2 id="classics-title">{t("library.classics")}</h2>
              <p>{t("library.classicsBody")}</p>
            </div>
          </header>
          <div className="pl-shelf-row">
            {classics.map((entry) => (
              <CaseCard key={entry.id} entry={entry} onOpen={onOpen} />
            ))}
          </div>
        </section>
      )}

      <section className="pl-story" aria-labelledby="story-title">
        <Mascot pose="thinking" size={96} />
        <div>
          <p className="pl-eyebrow">Everywhere Safety · Murdoku Lab</p>
          <h2 id="story-title">{t("workshop.storyTitle")}</h2>
          <p>{t("workshop.storyBody")}</p>
          <div className="pl-story-links">
            <a
              href={funnel("blog", "library-story")}
              target="_blank"
              rel="noopener"
            >
              {t("workshop.storyCta")} ↗
            </a>
            <a
              href={funnel("project", "library-story")}
              target="_blank"
              rel="noopener"
            >
              {t("workshop.projectCta")} ↗
            </a>
          </div>
        </div>
      </section>
    </div>
  );
}
