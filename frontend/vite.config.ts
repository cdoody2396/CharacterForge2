import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// §D.1 same-origin rule: the app fetches only relative paths under
// /spine/* and never knows the spine's origin. In dev this proxy maps
// /spine/* onto the spine; the target comes from VITE_SPINE_ORIGIN,
// config-side only (set by scripts/dev.py). The packaged shell later
// reproduces the same mapping. The spine gains no CORS handling — no
// cross-origin surface exists.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/spine": {
        target: process.env.VITE_SPINE_ORIGIN ?? "http://127.0.0.1:1",
        changeOrigin: false,
        rewrite: (path) => path.replace(/^\/spine/, ""),
      },
    },
  },
});
