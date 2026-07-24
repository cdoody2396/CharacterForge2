// §F.4 swatch — circles from the served `color`, label on
// focus/selection. Handles pick_one and pick_many alike (widget
// derivation is spine-side; color wins over kind).
import { useState } from "react";
import type { WidgetProps } from "./WidgetHost";
import { toggleValue } from "./WidgetHost";
import { OrphanedBadge, RetiredBadge } from "../parts/faults";

export function Swatch({ group, busy, onSelect }: WidgetProps) {
  const [focusedId, setFocusedId] = useState<string | null>(null);
  const menuIds = new Set(group.options.map((option) => option.id));
  const held = group.current.filter((entry) => !menuIds.has(entry.id));
  const selected = new Set(group.current.map((entry) => entry.id));
  const toggle = (id: string) => {
    const value = toggleValue(group, id);
    if (value !== null) onSelect(value);
  };

  const focused =
    group.options.find((option) => option.id === focusedId) ??
    group.current.find((entry) => entry.id === focusedId);
  const shown =
    focused ??
    group.current[0] ??
    null; // label on focus/selection (§F.4)

  return (
    <div>
      <div className="swatch-row" role="group" aria-label={group.label}>
        {held.map((entry) => (
          <button
            key={entry.id}
            type="button"
            className="swatch-circle"
            style={entry.color ? { background: entry.color } : undefined}
            aria-pressed="true"
            aria-label={entry.label ?? entry.id}
            disabled={busy}
            onClick={() => toggle(entry.id)}
            onFocus={() => setFocusedId(entry.id)}
            onBlur={() => setFocusedId(null)}
          />
        ))}
        {group.options.map((option) => (
          <button
            key={option.id}
            type="button"
            className="swatch-circle"
            style={option.color ? { background: option.color } : undefined}
            aria-pressed={selected.has(option.id)}
            aria-label={option.label}
            disabled={busy}
            onClick={() => toggle(option.id)}
            onFocus={() => setFocusedId(option.id)}
            onBlur={() => setFocusedId(null)}
          />
        ))}
      </div>
      <div className="swatch-label" aria-live="polite">
        {shown ? (
          <>
            {shown.label ?? shown.id}
            {"retired" in shown && shown.retired ? <RetiredBadge /> : null}
            {"orphaned" in shown && shown.orphaned ? <OrphanedBadge /> : null}
          </>
        ) : null}
      </div>
    </div>
  );
}
