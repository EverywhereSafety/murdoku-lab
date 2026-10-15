import { resolve } from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Two pages: the player at the root and the research Lab at lab/.
export default defineConfig({
  root: "web",
  base: "./",
  worker: { format: "es" },
  plugins: [react()],
  build: {
    outDir: "../dist",
    emptyOutDir: true,
    rollupOptions: {
      input: {
        play: resolve(import.meta.dirname, "web/index.html"),
        lab: resolve(import.meta.dirname, "web/lab/index.html"),
      },
    },
  },
  server: { port: 5173, proxy: { "/api": "http://127.0.0.1:8765" } },
});
