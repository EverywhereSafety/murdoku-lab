import React, { useCallback, useEffect, useState } from "react";
import { CaseView } from "./components/CaseView.jsx";
import { Footer, HowToDialog, SettingsDialog, TopBar } from "./components/Chrome.jsx";
import { Library } from "./components/Library.jsx";
import { SharedDefs } from "./components/ui.jsx";
import { loadProfile, saveProfile } from "./engine/persist.js";

function currentCase() {
  return new URLSearchParams(window.location.search).get("case");
}

export default function PlayApp() {
  const [caseId, setCaseId] = useState(currentCase);
  const [profile, setProfile] = useState(loadProfile);
  const [dialog, setDialog] = useState(null);

  useEffect(() => {
    const pop = () => setCaseId(currentCase());
    window.addEventListener("popstate", pop);
    return () => window.removeEventListener("popstate", pop);
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = profile.settings.night ? "night" : "day";
  }, [profile.settings.night]);

  const open = useCallback((id) => {
    const url = new URL(window.location.href);
    if (id) url.searchParams.set("case", id);
    else url.searchParams.delete("case");
    window.history.pushState({}, "", url);
    setCaseId(id);
    window.scrollTo(0, 0);
  }, []);

  const changeSettings = (settings) => {
    const next = { ...profile, settings };
    setProfile(next);
    saveProfile(next);
  };

  return (
    <div className="pl-app">
      <SharedDefs />
      <TopBar
        inCase={Boolean(caseId)}
        onHome={() => open(null)}
        onHowTo={() => setDialog("howto")}
        onSettings={() => setDialog("settings")}
      />
      <main className="pl-main">
        {caseId ? <CaseView id={caseId} settings={profile.settings} onOpen={open} /> : <Library onOpen={open} />}
      </main>
      <Footer />
      <SettingsDialog
        open={dialog === "settings"}
        settings={profile.settings}
        onChange={changeSettings}
        onClose={() => setDialog(null)}
      />
      <HowToDialog open={dialog === "howto"} onClose={() => setDialog(null)} />
    </div>
  );
}
