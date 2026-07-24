// §F.8 — the jump palette. Ctrl+K overlay; client-side fuzzy index
// over served group and option labels; selecting jumps to the station
// and highlights the group. The index is rebuilt on every view
// refetch (the caller memoizes on the view object).
import { useMemo, useState } from "react";
import type { CreatorView } from "../spine/types";
import { buildIndex, fuzzyFilter } from "../state/fuzzy";
import { Overlay } from "./Overlay";

export function JumpPalette({
  view,
  onJump,
  onClose,
}: {
  view: CreatorView;
  onJump: (groupId: string) => void;
  onClose: () => void;
}) {
  const [query, setQuery] = useState("");
  const index = useMemo(() => buildIndex(view), [view]);
  const results = useMemo(() => fuzzyFilter(index, query), [index, query]);

  return (
    <Overlay label="Jump to a group or option" onClose={onClose}>
      <div className="palette">
        <input
          type="search"
          placeholder="Jump to a group or option…"
          aria-label="Jump to a group or option"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && results.length > 0) {
              onJump(results[0].groupId);
            }
          }}
        />
        <div className="palette-results">
          {results.map((entry, i) => (
            <button
              key={`${entry.type}-${entry.groupId}-${entry.label}-${i}`}
              type="button"
              className="palette-item"
              onClick={() => onJump(entry.groupId)}
            >
              <span>{entry.label}</span>
              {entry.sub ? <span className="sub">in {entry.sub}</span> : null}
              <span className="sub">{entry.type}</span>
            </button>
          ))}
          {results.length === 0 ? (
            <span className="sub">Nothing matches.</span>
          ) : null}
        </div>
      </div>
    </Overlay>
  );
}
