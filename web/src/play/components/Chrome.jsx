import React from "react";
import { assetUrl } from "../data.js";
import { t } from "../i18n/index.js";
import { funnel } from "../lib/funnel.js";
import { Dialog, Mascot } from "./ui.jsx";

export function TopBar({ inCase, onHome, onHowTo, onSettings }) {
  return (
    <header className="pl-topbar">
      <a
        className="pl-brand"
        href="./"
        onClick={(event) => {
          event.preventDefault();
          onHome();
        }}
      >
        <img src={assetUrl("favicon.svg")} width="34" height="34" alt="" />
        <span>{t("brand.name")}</span>
      </a>
      <nav className="pl-nav">
        {inCase && (
          <button type="button" className="pl-nav-link" onClick={onHome}>
            ← {t("nav.back")}
          </button>
        )}
        <button type="button" className="pl-nav-link" onClick={onHowTo}>
          {t("nav.howto")}
        </button>
        <button type="button" className="pl-icon-button" onClick={onSettings} aria-label={t("nav.settings")}>
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="12" cy="12" r="3.2" />
            <path d="M12 2.8v2.4M12 18.8v2.4M2.8 12h2.4M18.8 12h2.4M5.5 5.5l1.7 1.7M16.8 16.8l1.7 1.7M5.5 18.5l1.7-1.7M16.8 7.2l1.7-1.7" />
          </svg>
        </button>
      </nav>
    </header>
  );
}

export function Footer() {
  return (
    <footer className="pl-footer">
      <span>{t("footer.made")}</span>
      <a href={funnel("home", "footer")} target="_blank" rel="noopener">
        everywheresafety
      </a>
      <a href={funnel("project", "footer")} target="_blank" rel="noopener">
        {t("footer.project")}
      </a>
      <a href={funnel("blog", "footer")} target="_blank" rel="noopener">
        {t("footer.blog")}
      </a>
      <a href="lab/">{t("footer.lab")}</a>
    </footer>
  );
}

export function SettingsDialog({ open, settings, onChange, onClose }) {
  const rows = ["sound", "haptics", "night", "timer", "notesFirst"];
  return (
    <Dialog open={open} onClose={onClose} labelledBy="pl-settings-title" className="pl-settings">
      <h2 id="pl-settings-title">{t("settings.title")}</h2>
      <div className="pl-switches">
        {rows.map((key) => (
          <label key={key} className="pl-switch">
            <span>{t(`settings.${key}`)}</span>
            <input type="checkbox" checked={Boolean(settings[key])} onChange={(event) => onChange({ ...settings, [key]: event.target.checked })} />
            <span className="pl-switch-track" aria-hidden="true" />
          </label>
        ))}
      </div>
      <div className="pl-dialog-buttons">
        <button type="button" className="pl-primary" onClick={onClose}>
          {t("settings.close")}
        </button>
      </div>
    </Dialog>
  );
}

export function HowToDialog({ open, onClose, onTraining }) {
  return (
    <Dialog open={open} onClose={onClose} labelledBy="pl-howto-title" className="pl-howto">
      <Mascot pose="pointing" size={96} className="pl-dialog-mascot" />
      <h2 id="pl-howto-title">{t("howto.title")}</h2>
      <ol>
        {[1, 2, 3, 4, 5].map((i) => (
          <li key={i}>{t(`howto.${i}`)}</li>
        ))}
      </ol>
      <div className="pl-dialog-buttons">
        <button type="button" className="pl-primary" onClick={onTraining}>
          {t("howto.training")}
        </button>
        <button type="button" className="pl-secondary" onClick={onClose}>
          {t("settings.close")}
        </button>
      </div>
    </Dialog>
  );
}
