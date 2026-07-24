// §F.4 picker heavy kit — activates at ≥ 24 served options (§I.7:
// guidance, presentation-side): type-to-filter on labels, facet chips
// with counts when served options carry tags (§G.1), sort modes
// catalog / A–Z (client-side curation, §B — never a widen), current
// value pinned by the Picker itself.
import type { MenuOption } from "../spine/types";

export const HEAVY_KIT_THRESHOLD = 24;

export type SortMode = "catalog" | "alpha";

export interface KitState {
  filter: string;
  facets: string[];
  sort: SortMode;
}

export const EMPTY_KIT: KitState = { filter: "", facets: [], sort: "catalog" };

/** Facet tags with counts over the SERVED menu (overall counts). */
export function facetCounts(options: MenuOption[]): Array<[string, number]> {
  const counts = new Map<string, number>();
  for (const option of options) {
    for (const tag of option.tags) {
      counts.set(tag, (counts.get(tag) ?? 0) + 1);
    }
  }
  return [...counts.entries()].sort(
    (a, b) => b[1] - a[1] || a[0].localeCompare(b[0]),
  );
}

/** Narrow + reorder the served menu per the kit state (§B: curation
 * of an already-judged menu). */
export function applyKit(
  options: MenuOption[],
  kit: KitState,
): MenuOption[] {
  const needle = kit.filter.trim().toLowerCase();
  let result = options.filter(
    (option) =>
      (needle === "" || option.label.toLowerCase().includes(needle)) &&
      kit.facets.every((facet) => option.tags.includes(facet)),
  );
  if (kit.sort === "alpha") {
    result = [...result].sort((a, b) => a.label.localeCompare(b.label));
  }
  return result;
}

export function HeavyKit({
  options,
  kit,
  onChange,
  resultCount,
}: {
  options: MenuOption[];
  kit: KitState;
  onChange: (kit: KitState) => void;
  resultCount: number;
}) {
  const facets = facetCounts(options);
  return (
    <div className="heavy-kit">
      <div className="kit-row">
        <input
          type="search"
          placeholder="Filter options…"
          aria-label="Filter options"
          value={kit.filter}
          onChange={(event) =>
            onChange({ ...kit, filter: event.target.value })
          }
        />
        <button
          type="button"
          aria-pressed={kit.sort === "catalog"}
          onClick={() => onChange({ ...kit, sort: "catalog" })}
        >
          Catalog
        </button>
        <button
          type="button"
          aria-pressed={kit.sort === "alpha"}
          onClick={() => onChange({ ...kit, sort: "alpha" })}
        >
          A–Z
        </button>
        <span className="chip-count" aria-live="polite">
          {resultCount} of {options.length}
        </span>
      </div>
      {facets.length > 0 ? (
        <div className="kit-row" role="group" aria-label="Facets">
          {facets.map(([tag, count]) => (
            <button
              key={tag}
              type="button"
              className="facet-chip"
              aria-pressed={kit.facets.includes(tag)}
              onClick={() =>
                onChange({
                  ...kit,
                  facets: kit.facets.includes(tag)
                    ? kit.facets.filter((facet) => facet !== tag)
                    : [...kit.facets, tag],
                })
              }
            >
              {tag} · {count}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
