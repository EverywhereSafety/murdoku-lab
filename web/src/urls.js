// Resolve against the document's directory so the same build works at /, at
// /index.html, and below gateways such as /.../proxy/8765/. A leading slash on
// a route here is an app route, never a request to the gateway's root.
// A page below the app root (the Lab at lab/) names the root in a meta tag.
const rootMeta = document.querySelector('meta[name="murdoku-app-root"]');
const applicationBase = new URL(rootMeta?.content || ".", window.location.href);

export function appUrl(path) {
  if (
    import.meta.env.VITE_STATIC_PLAY === "true" &&
    path.startsWith("/api/art/")
  )
    path = path.replace("/api/art/", "art/");
  return new URL(path.replace(/^\/+/, ""), applicationBase).href;
}

// DSW workspaces and proxied ports can share an origin. Keep their sessions apart.
export const sessionStorageKey = `murdoku-visual-session:${applicationBase.pathname}`;

export function savedSession() {
  return (
    localStorage.getItem(sessionStorageKey) ||
    (applicationBase.pathname === "/"
      ? localStorage.getItem("murdoku-visual-session")
      : null)
  );
}

// Public project navigation is independent of the game/API deployment origin.
const organizationSite = "https://everywheresafety.github.io";
export const projectLinks = [
  ["Everywhere Safety", `${organizationSite}/`],
  ["Project website", `${organizationSite}/murdoku/`],
  ["Blog", `${organizationSite}/blog/treasure-hunt/`],
  ["Code & generator", "https://github.com/EverywhereSafety/murdoku-lab"],
  ["Agentic RL infrastructure", `${organizationSite}/agent-horizon/`],
  [
    "Queries & rollouts",
    "https://github.com/EverywhereSafety/murdoku-lab/blob/main/docs/guides/data.md",
  ],
];
