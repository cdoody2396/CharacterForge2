// §F.8 — the jump palette's client-side fuzzy index over served group
// and option labels. Hand-rolled subsequence matcher (the dependency
// set is closed, §C.2). Rebuilt on every view refetch by the caller.
import type { CreatorView } from "../spine/types";

export interface PaletteEntry {
  type: "group" | "option";
  groupId: string;
  label: string;
  sub: string | null;
}

export function buildIndex(view: CreatorView): PaletteEntry[] {
  const entries: PaletteEntry[] = [];
  for (const group of view.groups) {
    entries.push({ type: "group", groupId: group.id, label: group.label, sub: null });
    for (const option of group.options) {
      entries.push({
        type: "option",
        groupId: group.id,
        label: option.label,
        sub: group.label,
      });
    }
  }
  return entries;
}

/** Case-insensitive subsequence score: -1 = no match; higher is
 * better. Consecutive runs and word starts score up, gaps score
 * down a little. */
export function fuzzyScore(query: string, label: string): number {
  const q = query.toLowerCase();
  const l = label.toLowerCase();
  if (q.length === 0) return 0;
  let score = 0;
  let li = 0;
  let previousHit = -2;
  for (let qi = 0; qi < q.length; qi++) {
    const found = l.indexOf(q[qi], li);
    if (found === -1) return -1;
    score += 2;
    if (found === previousHit + 1) score += 3; // consecutive
    if (found === 0 || l[found - 1] === " " || l[found - 1] === "-") {
      score += 2; // word start
    }
    score -= Math.min(found - li, 4) * 0.25; // gap penalty, capped
    previousHit = found;
    li = found + 1;
  }
  score -= l.length * 0.01; // gentle preference for shorter labels
  return score;
}

export function fuzzyFilter(
  entries: PaletteEntry[],
  query: string,
  limit = 20,
): PaletteEntry[] {
  if (query.trim() === "") return entries.slice(0, limit);
  const scored: Array<{ entry: PaletteEntry; score: number }> = [];
  for (const entry of entries) {
    const score = fuzzyScore(query, entry.label);
    if (score >= 0) scored.push({ entry, score });
  }
  scored.sort((a, b) => b.score - a.score);
  return scored.slice(0, limit).map((item) => item.entry);
}
