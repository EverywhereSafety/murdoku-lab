import { browserRequest } from "./browser-api.js";
import { appUrl } from "../urls.js";

export const api = async (path, body) => {
  if (import.meta.env.VITE_STATIC_PLAY === "true")
    return browserRequest(path, body);
  const response = await fetch(
    appUrl(path),
    body === undefined
      ? {}
      : {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        },
  );
  const data = await response.json();
  if (!response.ok)
    throw new Error(data.error || `Request failed (${response.status})`);
  return data;
};

export async function fetchResource(url, options) {
  if (import.meta.env.VITE_STATIC_PLAY !== "true") return fetch(url, options);
  options?.signal?.throwIfAborted();
  const target = new URL(url);
  const path = "/api/" + target.pathname.split("/api/")[1] + target.search;
  const result = await browserRequest(path);
  options?.signal?.throwIfAborted();
  return new Response(result, { headers: { "Content-Type": "image/svg+xml" } });
}
