import "@fontsource/dm-sans/400.css";
import "@fontsource/dm-sans/500.css";
import "@fontsource/dm-sans/700.css";
import "@fontsource/dm-mono/500.css";
import "@fontsource/newsreader/500.css";
import "@fontsource/newsreader/600.css";
import React from "react";
import { createRoot } from "react-dom/client";
import "../generated/tokens.css";
import PlayApp from "./PlayApp.jsx";
import "./play.css";

// Old links to the research casebook (?lab=1) still land in the Lab.
const params = new URLSearchParams(window.location.search);
if (params.has("lab")) {
  params.delete("lab");
  window.location.replace(`lab/${params.toString() ? `?${params}` : ""}${window.location.hash}`);
} else {
  createRoot(document.getElementById("root")).render(<PlayApp />);
}
