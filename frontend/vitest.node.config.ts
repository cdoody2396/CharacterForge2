import { defineConfig } from "vitest/config";

// Integration tests (§H): node environment, a REAL spine spawned via
// `uv run python -m app.spine --data-root <tmpdir>`, token read
// launcher-side from runtime.json — never from client code.
export default defineConfig({
  test: {
    environment: "node",
    include: ["tests/integration/**/*.test.ts"],
    testTimeout: 60_000,
    hookTimeout: 120_000,
  },
});
