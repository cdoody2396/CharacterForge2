// §F.4 picker — list/grid, virtualized (@tanstack/react-virtual). At
// ≥ 24 served options the heavy kit activates. Thumb grid when
// `thumb` is served. Current value pinned above the list.
import { useMemo, useRef, useState } from "react";
import { useVirtualizer } from "@tanstack/react-virtual";
import type { MenuOption } from "../spine/types";
import type { WidgetProps } from "./WidgetHost";
import { toggleValue } from "./WidgetHost";
import { OrphanedBadge, RetiredBadge } from "../parts/faults";
import {
  applyKit,
  EMPTY_KIT,
  HEAVY_KIT_THRESHOLD,
  HeavyKit,
} from "./HeavyKit";
import type { KitState } from "./HeavyKit";

const ROW_HEIGHT = 38;
const TILE_ROW_HEIGHT = 148;
const GRID_COLUMNS = 4;

export function Picker({ group, busy, onSelect }: WidgetProps) {
  const [kit, setKit] = useState<KitState>(EMPTY_KIT);
  const heavy = group.options.length >= HEAVY_KIT_THRESHOLD;
  const grid = group.options.some((option) => option.thumb !== null);
  const selected = new Set(group.current.map((entry) => entry.id));

  const shown = useMemo(
    () => (heavy ? applyKit(group.options, kit) : group.options),
    [heavy, group.options, kit],
  );

  const toggle = (id: string) => {
    const value = toggleValue(group, id);
    if (value !== null) onSelect(value);
  };

  return (
    <div className={grid ? "picker picker-grid" : "picker"}>
      {heavy ? (
        <HeavyKit
          options={group.options}
          kit={kit}
          onChange={setKit}
          resultCount={shown.length}
        />
      ) : null}
      {group.current.length > 0 ? (
        <div className="picker-pinned">
          {group.current.map((entry) => (
            <button
              key={entry.id}
              type="button"
              className="picker-item"
              aria-pressed="true"
              disabled={busy}
              onClick={() => toggle(entry.id)}
            >
              {entry.label ?? entry.id}
              {entry.retired ? <RetiredBadge /> : null}
              {entry.orphaned ? <OrphanedBadge /> : null}
            </button>
          ))}
        </div>
      ) : null}
      {grid ? (
        <GridBody
          options={shown}
          selected={selected}
          busy={busy}
          onToggle={toggle}
        />
      ) : (
        <ListBody
          options={shown}
          selected={selected}
          busy={busy}
          onToggle={toggle}
        />
      )}
    </div>
  );
}

function ListBody({
  options,
  selected,
  busy,
  onToggle,
}: {
  options: MenuOption[];
  selected: Set<string>;
  busy: boolean;
  onToggle: (id: string) => void;
}) {
  const parentRef = useRef<HTMLDivElement>(null);
  const virtualizer = useVirtualizer({
    count: options.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => ROW_HEIGHT,
    overscan: 12,
  });
  return (
    <div className="picker-list" ref={parentRef} role="listbox">
      <div
        style={{ height: virtualizer.getTotalSize(), position: "relative" }}
      >
        {virtualizer.getVirtualItems().map((row) => {
          const option = options[row.index];
          return (
            <button
              key={option.id}
              type="button"
              className="picker-item"
              role="option"
              aria-selected={selected.has(option.id)}
              aria-pressed={selected.has(option.id)}
              disabled={busy}
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                width: "100%",
                height: row.size,
                transform: `translateY(${row.start}px)`,
              }}
              onClick={() => onToggle(option.id)}
            >
              {option.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function GridBody({
  options,
  selected,
  busy,
  onToggle,
}: {
  options: MenuOption[];
  selected: Set<string>;
  busy: boolean;
  onToggle: (id: string) => void;
}) {
  const rows = useMemo(() => {
    const chunks: MenuOption[][] = [];
    for (let i = 0; i < options.length; i += GRID_COLUMNS) {
      chunks.push(options.slice(i, i + GRID_COLUMNS));
    }
    return chunks;
  }, [options]);
  const parentRef = useRef<HTMLDivElement>(null);
  const virtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => TILE_ROW_HEIGHT,
    overscan: 4,
  });
  return (
    <div className="picker-list" ref={parentRef} role="listbox">
      <div
        style={{ height: virtualizer.getTotalSize(), position: "relative" }}
      >
        {virtualizer.getVirtualItems().map((row) => (
          <div
            key={row.index}
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              width: "100%",
              transform: `translateY(${row.start}px)`,
              display: "grid",
              gridTemplateColumns: `repeat(${GRID_COLUMNS}, 1fr)`,
              gap: "0.5rem",
              padding: "0.5rem",
            }}
          >
            {rows[row.index].map((option) => (
              <button
                key={option.id}
                type="button"
                className="picker-item thumb-tile"
                role="option"
                aria-selected={selected.has(option.id)}
                aria-pressed={selected.has(option.id)}
                disabled={busy}
                onClick={() => onToggle(option.id)}
              >
                <span className="thumb-box">
                  {option.thumb ? (
                    <img src={option.thumb} alt="" />
                  ) : (
                    <span>{option.label.slice(0, 2)}</span>
                  )}
                </span>
                {option.label}
              </button>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
