// §F.4 segmented — exclusive horizontal buttons; re-pick replaces.
// A held value not in the served menu (retired or orphaned) renders
// as a pinned, badged, still-functional button (§F.4 everywhere-law).
import type { WidgetProps } from "./WidgetHost";
import { toggleValue } from "./WidgetHost";
import { OrphanedBadge, RetiredBadge } from "../parts/faults";

export function Segmented({ group, busy, onSelect }: WidgetProps) {
  const menuIds = new Set(group.options.map((option) => option.id));
  const held = group.current.filter((entry) => !menuIds.has(entry.id));
  const selected = new Set(group.current.map((entry) => entry.id));
  return (
    <div className="seg-row" role="group" aria-label={group.label}>
      {held.map((entry) => (
        <button
          key={entry.id}
          type="button"
          className="seg-btn"
          aria-pressed="true"
          disabled={busy}
          onClick={() => {
            const value = toggleValue(group, entry.id);
            if (value !== null) onSelect(value);
          }}
        >
          {entry.label ?? entry.id}
          {entry.retired ? <RetiredBadge /> : null}
          {entry.orphaned ? <OrphanedBadge /> : null}
        </button>
      ))}
      {group.options.map((option) => (
        <button
          key={option.id}
          type="button"
          className="seg-btn"
          aria-pressed={selected.has(option.id)}
          disabled={busy}
          onClick={() => {
            const value = toggleValue(group, option.id);
            if (value !== null) onSelect(value);
          }}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
