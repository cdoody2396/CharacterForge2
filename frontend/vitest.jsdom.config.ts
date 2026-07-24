import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

// Component tests (§H): jsdom, captured fixtures, mocked fetch.
export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    include: ["tests/**/*.test.tsx"],
    setupFiles: ["tests/setup.ts"],
  },
});
