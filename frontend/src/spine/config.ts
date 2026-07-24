// §D.2 — the injection boundary. This is the ONE module that resolves
// { token }, from import.meta.env.VITE_SPINE_TOKEN (set host-side by
// scripts/dev.py). The React app never reads runtime.json, never
// spawns processes, never sees a port. The packaged shell later swaps
// this module's source and nothing else.
export const config = {
  token: (import.meta.env.VITE_SPINE_TOKEN ?? "") as string,
};
