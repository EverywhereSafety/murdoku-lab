// Resolve against the document's directory so the same build works at /, at
// /index.html, and below gateways such as /.../proxy/8765/. A leading slash on
// a route here is an app route, never a request to the gateway's root.
const applicationBase = new URL(".", window.location.href);

export function appUrl(path) {
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
  ["Blog", `${organizationSite}/blog/murdoku-as-vhd/`],
  ["Code & generator", "https://github.com/EverywhereSafety/murdoku-lab"],
  ["Agentic RL infrastructure", `${organizationSite}/agent-horizon/`],
  [
    "Queries & rollouts",
    "https://github.com/EverywhereSafety/murdoku-lab/blob/main/docs/guides/data.md",
  ],
];
