import React, { useMemo } from "react";
import { t } from "../i18n/index.js";
import { Face } from "./ui.jsx";

// Names in clue text that point at something on the board: people, rooms, objects, ground.
export function useReferences(game) {
  return useMemo(() => {
    const refs = [];
    for (const p of game.people) {
      refs.push({ text: p.name, kind: "person", id: p.id });
      const first = p.name.split(" ")[0];
      if (first !== p.name) refs.push({ text: first, kind: "person", id: p.id });
    }
    for (const a of game.areas) refs.push({ text: a.name, kind: "area", id: a.id });
    for (const prop of game.props) refs.push({ text: prop.name, kind: "prop", id: prop.id });
    for (const ground of game.public.scene.terrains || []) {
      if (ground.id !== "floor") refs.push({ text: ground.name, kind: "terrain", id: ground.id });
    }
    refs.sort((a, b) => b.text.length - a.text.length);
    const escaped = refs.map((r) => r.text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
    const pattern = escaped.length ? new RegExp(`\\b(${escaped.join("|")})\\b`, "gi") : null;
    const lookup = new Map(refs.map((r) => [r.text.toLowerCase(), r]));
    return { pattern, lookup };
  }, [game]);
}

export function ClueText({ text, refs, onRef }) {
  if (!refs.pattern) return text;
  const parts = [];
  let last = 0;
  for (const match of text.matchAll(refs.pattern)) {
    const ref = refs.lookup.get(match[0].toLowerCase());
    if (match.index > last) parts.push(text.slice(last, match.index));
    parts.push(
      <button
        key={match.index}
        type="button"
        className={`pl-ref is-${ref.kind}`}
        onMouseEnter={() => onRef(ref)}
        onMouseLeave={() => onRef(null)}
        onFocus={() => onRef(ref)}
        onBlur={() => onRef(null)}
        onClick={(event) => {
          event.stopPropagation();
          onRef(ref, true);
        }}
      >
        {match[0]}
      </button>,
    );
    last = match.index + match[0].length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return parts;
}

function SuspectCard({ game, person, index, state, selected, clashing, clues, refs, onSelect, onRef, onReview, hinted, coached }) {
  const where = state.placed[person.id];
  return (
    <article
      className={`pl-suspect${selected ? " is-selected" : ""}${person.victim ? " is-victim" : ""}${clashing ? " is-clash" : ""}${where ? " is-placed" : ""}${coached === person.id && !selected ? " is-coached" : ""}`}
      style={{ "--accent": person.accent, "--deal": index }}
      draggable
      onDragStart={(event) => {
        event.dataTransfer.setData("text/murdoku-person", person.id);
        event.dataTransfer.effectAllowed = "move";
        onSelect(person.id);
      }}
      onClick={() => onSelect(person.id)}
      onMouseEnter={() => onRef({ kind: "person", id: person.id })}
      onMouseLeave={() => onRef(null)}
    >
      <Face person={person} size={54} />
      <div className="pl-suspect-body">
        <header>
          <span className="pl-badge">{person.id}</span>
          <strong>{person.name}</strong>
          {person.victim && <span className="pl-victim-tag">{t("case.victim")}</span>}
          <span className="pl-where">{where ? t("case.placedAt", { cell: where.toUpperCase() }) : t("case.notPlaced")}</span>
        </header>
        {clues.map((clue) => (
          <p
            key={clue.id}
            className={`pl-statement${state.reviewed.includes(clue.id) ? " is-reviewed" : ""}${hinted === clue.id ? " is-hinted" : ""}`}
          >
            <span className="pl-clue-no">{clue.number}</span>
            <span className="pl-quote">
              <ClueText text={clue.text} refs={refs} onRef={onRef} />
            </span>
            <label className="pl-check" title={t("case.reviewed")} onClick={(event) => event.stopPropagation()}>
              <input
                type="checkbox"
                checked={state.reviewed.includes(clue.id)}
                onChange={(event) => onReview(clue.id, event.target.checked)}
                aria-label={t("case.reviewed")}
              />
              <span aria-hidden="true" />
            </label>
          </p>
        ))}
      </div>
    </article>
  );
}

export function Dossier({ game, state, selected, clashes, onSelect, onRef, onReview, hinted, coached, compact = false }) {
  const refs = useReferences(game);
  const byHolder = useMemo(() => {
    const map = new Map();
    for (const clue of game.clues) {
      const key = clue.person || "";
      if (!map.has(key)) map.set(key, []);
      map.get(key).push(clue);
    }
    return map;
  }, [game]);
  const facts = byHolder.get("") || [];
  const victim = game.people.find((p) => p.victim);
  const ordered = [...game.people.filter((p) => !p.victim), ...(victim ? [victim] : [])];
  return (
    <div className={`pl-dossier${compact ? " is-compact" : ""}`}>
      {!compact && (
        <header className="pl-dossier-head">
          <p className="pl-eyebrow">{game.meta.eyebrow}</p>
          <h1>{game.meta.title}</h1>
          <p className="pl-blurb">{game.meta.blurb}</p>
          <p className="pl-goal">
            {t(`case.goal.${game.goalType}`, { victim: victim?.name.split(" ")[0] ?? "the victim" })}
          </p>
        </header>
      )}
      <section aria-label={t("case.suspects")}>
        <h2>{t("case.suspects")}</h2>
        {ordered.map((person, index) => (
          <SuspectCard
            key={person.id}
            index={index}
            game={game}
            person={person}
            state={state}
            selected={person.id === selected}
            clashing={clashes.people.has(person.id)}
            clues={byHolder.get(person.id) || []}
            refs={refs}
            onSelect={onSelect}
            onRef={onRef}
            onReview={onReview}
            hinted={hinted}
            coached={coached}
          />
        ))}
      </section>
      {facts.length > 0 && (
        <section className="pl-facts" aria-label={t("case.facts")}>
          <h2>{t("case.facts")}</h2>
          {facts.map((clue) => (
            <p
              key={clue.id}
              className={`pl-statement${state.reviewed.includes(clue.id) ? " is-reviewed" : ""}${hinted === clue.id ? " is-hinted" : ""}`}
            >
              <span className="pl-clue-no">{clue.number}</span>
              <span className="pl-quote">
                <ClueText text={clue.text} refs={refs} onRef={onRef} />
              </span>
              <label className="pl-check">
                <input
                  type="checkbox"
                  checked={state.reviewed.includes(clue.id)}
                  onChange={(event) => onReview(clue.id, event.target.checked)}
                  aria-label={t("case.reviewed")}
                />
                <span aria-hidden="true" />
              </label>
            </p>
          ))}
        </section>
      )}
      <details className="pl-rules">
        <summary>{t("case.rules")}</summary>
        <ul>
          {game.public.rules.map((rule) => (
            <li key={rule}>{rule}</li>
          ))}
        </ul>
      </details>
    </div>
  );
}
