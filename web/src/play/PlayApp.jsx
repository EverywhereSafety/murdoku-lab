import React, { useCallback, useEffect, useState } from "react";
import { CaseView } from "./components/CaseView.jsx";
import { Footer, HowToDialog, SettingsDialog, TopBar } from "./components/Chrome.jsx";
import { Library } from "./components/Library.jsx";
import { Locked } from "./components/Daily.jsx";
import { SharedDefs } from "./components/ui.jsx";
import { loadDaily } from "./data.js";
import { today } from "./engine/daily.js";
import { loadProfile, saveProfile } from "./engine/persist.js";

function route() {
  const params = new URLSearchParams(window.location.search);
  const d = params.get("d");
  return {
    caseId: d && /^\d+$/.test(d) ? `daily-${d}` : params.get("case"),
    day: today(params),
    unlock: params.get("unlock") === "all",
  };
}

export default function PlayApp() {
  const [where, setWhere] = useState(route);
  const [profile, setProfile] = useState(loadProfile);
  const [manifest, setManifest] = useState(null);
  const [dialog, setDialog] = useState(null);

  useEffect(() => {
    loadDaily().then(setManifest);
    const pop = () => setWhere(route());
    window.addEventListener("popstate", pop);
    return () => window.removeEventListener("popstate", pop);
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = profile.settings.night ? "night" : "day";
  }, [profile.settings.night]);

  // Preview switches (?date=, ?unlock=all) survive navigation inside the app.
  const open = useCallback((id) => {
    const url = new URL(window.location.href);
    url.searchParams.delete("case");
    url.searchParams.delete("d");
    if (id?.startsWith("daily-")) url.searchParams.set("d", id.slice(6));
    else if (id) url.searchParams.set("case", id);
    window.history.pushState({}, "", url);
    setWhere(route());
    window.scrollTo(0, 0);
  }, []);

  const save = (next) => {
    setProfile(next);
    saveProfile(next);
  };

  const solved = useCallback(
    (game, finished, progress) => {
      if (!game.bundle.daily) return;
      const { n, date } = game.bundle.daily;
      setProfile((current) => {
        const next = {
          ...current,
          daily: {
            ...(current.daily || {}),
            [n]: {
              date,
              solved_on: where.day,
              stars: finished.stars,
              hints: progress.hints.length,
              wrong: progress.wrong_verdicts,
              elapsed_ms: finished.elapsed_ms,
            },
          },
        };
        saveProfile(next);
        return next;
      });
    },
    [where.day],
  );

  const entry = where.caseId?.startsWith("daily-") ? manifest?.days.find((d) => d.id === where.caseId) : null;
  const locked = entry && entry.date > where.day && !where.unlock;

  return (
    <div className="pl-app">
      <SharedDefs />
      <TopBar
        inCase={Boolean(where.caseId)}
        onHome={() => open(null)}
        onHowTo={() => setDialog("howto")}
        onSettings={() => setDialog("settings")}
      />
      <main className="pl-main">
        {locked ? (
          <Locked entry={entry} onOpen={open} />
        ) : where.caseId ? (
          <CaseView id={where.caseId} settings={profile.settings} onOpen={open} onSolved={solved} profile={profile} day={where.day} />
        ) : (
          <Library onOpen={open} manifest={manifest} day={where.day} unlock={where.unlock} profile={profile} />
        )}
      </main>
      <Footer />
      <SettingsDialog
        open={dialog === "settings"}
        settings={profile.settings}
        onChange={(settings) => save({ ...profile, settings })}
        onClose={() => setDialog(null)}
      />
      <HowToDialog
        open={dialog === "howto"}
        onClose={() => setDialog(null)}
        onTraining={() => {
          setDialog(null);
          open("tutorial");
        }}
      />
    </div>
  );
}
