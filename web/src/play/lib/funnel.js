// Every link to Everywhere Safety carries the same campaign tags, so a visit from the game is
// attributable without any analytics in the game itself.
const SITE = "https://everywheresafety.github.io";

export const LINKS = {
  home: `${SITE}/`,
  project: `${SITE}/murdoku/`,
  blog: `${SITE}/blog/treasure-hunt/`,
  quality: `${SITE}/blog/treasure-hunt/#make-the-clues-worth-following`,
  code: "https://github.com/EverywhereSafety/murdoku-lab",
  agents: `${SITE}/agent-horizon/`,
  data: "https://github.com/EverywhereSafety/murdoku-lab/blob/main/docs/guides/data.md",
};

export function funnel(name, placement) {
  const url = new URL(LINKS[name] || name);
  url.searchParams.set("utm_source", "murdoku-lab");
  url.searchParams.set("utm_medium", "game");
  url.searchParams.set("utm_campaign", "player");
  url.searchParams.set("utm_content", placement);
  return url.href;
}
