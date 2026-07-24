// §F.4 chips — multi-pick; each toggle sends the FULL new list;
// selected pinned first with a live count.
import type { WidgetProps } from "./WidgetHost";
import { toggleValue } from "./WidgetHost";
import { OrphanedBadge, RetiredBadge } from "../parts/faults";

export function Chips({ group, busy, onSelect }: WidgetProps) {
  const selectedIds = new Set(group.current.map((entry) => entry.id));
  const unselected = group.options.filter(
    (option) => !selectedIds.has(option.id),
  );
  const toggle = (id: string) => {
    const value = toggleValue(group, id);
    if (value !== null) onSelect(value);
  };
  return (
    <div className="chip-row" role="group" aria-label={group.label}>
      <span className="chip-count" aria-live="polite">
        {group.current.length} selected
        {group.max_picks !== null ? ` / ${group.max_picks}` : ""}
      </span>
      {group.current.map((entry) => (
        <button
          key={entry.id}
          type="button"
          className="chip"
          aria-pressed="true"
          disabled={busy}
          onClick={() => toggle(entry.id)}
        >
          {entry.label ?? entry.id}
          {entry.retired ? <RetiredBadge /> : null}
          {entry.orphaned ? <OrphanedBadge /> : null}
        </button>
      ))}
      {unselected.map((option) => (
        <button
          key={option.id}
          type="button"
          className="chip"
          aria-pressed="false"
          disabled={busy}
          onClick={() => toggle(option.id)}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
