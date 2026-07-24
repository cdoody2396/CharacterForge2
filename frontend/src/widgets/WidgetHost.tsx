// §F.4 — render the four served widget kinds. An unserved or unknown
// `widget` value renders a visible fault card for that group: fail
// loud, never skip silently. The frame carries the shared facts
// (label, required, hint), the clear affordance (DELETE
// …/selections/{group_id} — the endpoint map's all-four-widgets
// consumer), and the field-anchored refusal stamp (§F.7).
import type { Refusal, ViewGroup } from "../spine/types";
import { FaultCard, RefusalStamp } from "../parts/faults";
import { Segmented } from "./Segmented";
import { Chips } from "./Chips";
import { Swatch } from "./Swatch";
import { Picker } from "./Picker";

export interface WidgetProps {
  group: ViewGroup;
  busy: boolean;
  onSelect: (value: string | string[]) => void;
}

export function WidgetHost({
  group,
  stamp,
  busy,
  highlight = false,
  onSelect,
  onClear,
}: WidgetProps & {
  stamp: Refusal | null;
  highlight?: boolean;
  onClear: () => void;
}) {
  let body;
  switch (group.widget) {
    case "segmented":
      body = <Segmented group={group} busy={busy} onSelect={onSelect} />;
      break;
    case "chips":
      body = <Chips group={group} busy={busy} onSelect={onSelect} />;
      break;
    case "swatch":
      body = <Swatch group={group} busy={busy} onSelect={onSelect} />;
      break;
    case "picker":
      body = <Picker group={group} busy={busy} onSelect={onSelect} />;
      break;
    default:
      body = (
        <FaultCard
          title={`unknown widget "${group.widget}"`}
          detail={
            `Group "${group.label}" (${group.id}) was served a widget ` +
            `kind this client does not know. Rendering refused loudly ` +
            `rather than skipped silently (§F.4).`
          }
        />
      );
  }
  return (
    <section
      className={highlight ? "widget-frame group-highlight" : "widget-frame"}
      id={`group-${group.id}`}
      data-group-id={group.id}
      aria-label={group.label}
    >
      <div className="widget-head">
        <span className="widget-label">{group.label}</span>
        {group.required ? (
          <span className="required-mark">required</span>
        ) : null}
        {group.hint ? <span className="widget-hint">{group.hint}</span> : null}
        <span className="spacer" />
        {group.current.length > 0 ? (
          <button type="button" disabled={busy} onClick={onClear}>
            Clear
          </button>
        ) : null}
      </div>
      {body}
      {stamp ? <RefusalStamp refusal={stamp} /> : null}
    </section>
  );
}

/** Shared helpers for the widget bodies. */
export function currentIds(group: ViewGroup): string[] {
  return group.current.map((entry) => entry.id);
}

export function isMulti(group: ViewGroup): boolean {
  return group.kind === "pick_many";
}

/** The next value for a toggle: pick_many sends the full new list
 * (§F.4 chips law, shared by every multi-capable widget); pick_one
 * replaces. Returns null when the toggle is a no-op. */
export function toggleValue(
  group: ViewGroup,
  optionId: string,
): string | string[] | null {
  if (!isMulti(group)) {
    return currentIds(group)[0] === optionId ? null : optionId;
  }
  const ids = currentIds(group);
  return ids.includes(optionId)
    ? ids.filter((id) => id !== optionId)
    : [...ids, optionId];
}
