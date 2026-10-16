import React, { useEffect, useRef } from "react";
import { assetUrl } from "../data.js";
import { t } from "../i18n/index.js";

// One shared clip for every portrait card on the page.
export function SharedDefs() {
  return (
    <svg width="0" height="0" aria-hidden="true" style={{ position: "absolute" }}>
      <defs>
        {/* userSpaceOnUse: every face is drawn in its own 0–100 box. */}
        <clipPath id="pl-card-clip">
          <circle cx="50" cy="50" r="48" />
        </clipPath>
      </defs>
    </svg>
  );
}

export function Face({ person, size = 56, className = "" }) {
  return (
    <span
      className={`pl-face ${person.victim ? "is-victim" : ""} ${className}`}
      style={{ width: size, height: size, "--accent": person.accent }}
      aria-hidden="true"
    >
      <svg viewBox="0 0 100 100" width={size} height={size}>
        <circle cx="50" cy="50" r="49" fill="#fbf7ee" />
        <g clipPath="url(#pl-card-clip)" dangerouslySetInnerHTML={{ __html: person.face }} />
      </svg>
    </span>
  );
}

export function Mascot({ pose = "idle", size = 96, className = "" }) {
  return (
    <img
      className={`pl-mascot ${className}`}
      src={assetUrl(`brand/mascot-${pose}.svg`)}
      width={size}
      height={size}
      alt=""
      draggable="false"
    />
  );
}

export function Stars({ count, size = 22 }) {
  return (
    <span className="pl-stars" role="img" aria-label={t("reveal.stars", { n: count })}>
      {[0, 1, 2].map((i) => (
        <svg key={i} viewBox="0 0 24 24" width={size} height={size} className={i < count ? "is-on" : ""}>
          <path d="M12 2.6l2.9 6 6.6.9-4.8 4.6 1.2 6.5L12 17.5l-5.9 3.1 1.2-6.5L2.5 9.5l6.6-.9Z" />
        </svg>
      ))}
    </span>
  );
}

export function Dialog({ open, onClose, labelledBy, className = "", children }) {
  const ref = useRef(null);
  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    if (open && !node.open) node.showModal();
    if (!open && node.open) node.close();
  }, [open]);
  return (
    <dialog
      ref={ref}
      className={`pl-dialog ${className}`}
      aria-labelledby={labelledBy}
      onCancel={(event) => {
        event.preventDefault();
        onClose?.();
      }}
      onClick={(event) => {
        if (event.target === ref.current) onClose?.();
      }}
    >
      {open && <div className="pl-dialog-body">{children}</div>}
    </dialog>
  );
}

export function Toast({ toast }) {
  return (
    <div className="pl-toast-region" aria-live="polite" aria-atomic="true">
      {toast && (
        <div key={toast.id} className={`pl-toast ${toast.tone || ""}`}>
          {toast.text}
        </div>
      )}
    </div>
  );
}

export function formatTime(ms) {
  const total = Math.round(ms / 1000);
  const m = Math.floor(total / 60);
  const s = String(total % 60).padStart(2, "0");
  return `${m}:${s}`;
}
