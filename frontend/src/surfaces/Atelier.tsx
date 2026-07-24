// §F.3 Atelier — three panes. Rail: stations = served sections in
// order with set/total counts, a trailing Unfiled station, a fixed
// Text station, the jump palette (Ctrl+K). Canvas: the active
// station's groups in `order` with a sticky mini-spine past 6 groups.
// Record pane: served fields verbatim; the committed appearance
// paragraph, else a client-assembled pick summary explicitly
// captioned as a preview — never presented as the paragraph.
import { useEffect, useMemo, useState } from "react";
import { api } from "../spine/client";
import type { Refusal } from "../spine/types";
import {
  groupsSetCount,
  stationsOf,
  useRecordData,
  visibleGroups,
} from "../state/recordData";
import { WidgetHost } from "../widgets/WidgetHost";
import { FaultScreen } from "../parts/faults";
import { DraftChip, draftOpen } from "../parts/DraftChip";
import { RatingRaise } from "../parts/RatingRaise";
import { FinalizeCeremony } from "../parts/FinalizeCeremony";
import { TextStation, TEXT_SLOTS } from "../parts/TextStation";
import { JumpPalette } from "../parts/JumpPalette";
import type { ToastPayload } from "../parts/ToastHost";

const TEXT_KEY = "__text__";
const MINI_SPINE_AT = 6;

export function Atelier({
  characterId,
  onRoster,
  onGuided,
  onToast,
}: {
  characterId: string;
  onRoster: () => void;
  onGuided: () => void;
  onToast: (toast: ToastPayload) => void;
}) {
  const { bundle, failure, mutate } = useRecordData(characterId);
  const [activeKey, setActiveKey] = useState<string | null>(null);
  const [stamp, setStamp] = useState<Refusal | null>(null);
  const [highlightId, setHighlightId] = useState<string | null>(null);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [busy, setBusy] = useState(false);

  // §F.8 — Ctrl+K opens the jump palette.
  useEffect(() => {
    const listener = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setPaletteOpen((open) => !open);
      }
    };
    window.addEventListener("keydown", listener);
    return () => window.removeEventListener("keydown", listener);
  }, []);

  useEffect(() => {
    if (highlightId === null) return;
    document
      .getElementById(`group-${highlightId}`)
      ?.scrollIntoView({ block: "center" });
    const timer = setTimeout(() => setHighlightId(null), 2500);
    return () => clearTimeout(timer);
  }, [highlightId]);

  const stations = useMemo(
    () => (bundle ? stationsOf(bundle.view) : []),
    [bundle],
  );

  if (failure) {
    return failure.kind === "refusal" ? (
      <FaultScreen
        code={failure.refusal.code}
        message={failure.refusal.message}
        explanation="The record did not load. The code above is the spine's, verbatim; no recovery UI exists for a corrupt record."
      />
    ) : (
      <FaultScreen
        code={failure.status === null ? "network failure" : `HTTP ${failure.status}`}
        message={failure.detail ?? "The spine did not answer."}
        explanation="The workbench cannot open without the spine."
      />
    );
  }
  if (!bundle) return <div className="loading">Reaching the spine…</div>;

  const { view, payload, staleness, grade } = bundle;
  const record = payload.record;
  const active =
    stations.find((station) => station.key === activeKey) ??
    (activeKey === TEXT_KEY ? null : stations[0]);
  const activeIsText =
    activeKey === TEXT_KEY || (stations.length === 0 && activeKey === null);

  const routeRefusal = (refusal: Refusal) => {
    const station = stations.find((s) =>
      s.groups.some((group) => group.id === refusal.subject),
    );
    if (station) {
      // Field-anchored (§F.7) — and the §F.6 deep-link for
      // REQUIRED_GROUP_UNFILLED: the named group's station activates.
      setActiveKey(station.key);
      setStamp(refusal);
      setHighlightId(refusal.subject);
    } else if ((TEXT_SLOTS as readonly string[]).includes(refusal.subject)) {
      setActiveKey(TEXT_KEY);
      setStamp(refusal);
    } else {
      onToast({ kind: "refusal", refusal });
    }
  };

  const run = async (call: () => Promise<unknown>): Promise<boolean> => {
    setBusy(true);
    setStamp(null);
    const outcome = await mutate(call);
    setBusy(false);
    if (outcome.kind === "ok") return true;
    if (outcome.kind === "refusal") routeRefusal(outcome.refusal);
    else
      onToast({
        kind: "fault",
        title:
          outcome.status === null ? "network failure" : `HTTP ${outcome.status}`,
        detail: outcome.detail,
      });
    return false;
  };

  const jumpTo = (groupId: string) => {
    const station = stations.find((s) =>
      s.groups.some((group) => group.id === groupId),
    );
    if (station) {
      setActiveKey(station.key);
      setHighlightId(groupId);
    }
    setPaletteOpen(false);
  };

  const counts = groupsSetCount(view);
  const activeVersion = record.identity_versions.find(
    (version) => version.version === record.active_version,
  );
  const summaryLabels = visibleGroups(view)
    .flatMap((group) => group.current)
    .map((entry) => entry.label ?? entry.id);

  return (
    <div className="atelier">
      <div className="atelier-header">
        <button type="button" onClick={onRoster}>
          ← Roster
        </button>
        <h2>{record.persona.name ?? "Unnamed"}</h2>
        <RatingRaise
          rating={view.rating}
          busy={busy}
          onRaise={(target) => run(() => api.raiseRating(characterId, target))}
        />
        <DraftChip record={record} />
        <span className="chip-tag">
          {counts.set}/{counts.total} set
        </span>
        <span style={{ flex: 1 }} />
        <button type="button" onClick={onGuided}>
          Guided pass
        </button>
        <button type="button" onClick={() => setPaletteOpen(true)}>
          Jump… (Ctrl+K)
        </button>
        <FinalizeCeremony
          busy={busy}
          grade={grade}
          onFinalize={() => run(() => api.finalize(characterId))}
        />
      </div>

      <nav className="rail" aria-label="Stations">
        {stations.map((station) => {
          const set = station.groups.filter(
            (group) => group.current.length > 0,
          ).length;
          return (
            <button
              key={station.key}
              type="button"
              className="station-btn"
              aria-current={!activeIsText && active?.key === station.key}
              onClick={() => {
                setActiveKey(station.key);
              }}
            >
              <span>{station.title}</span>
              <span className="station-count">
                {set}/{station.groups.length}
              </span>
            </button>
          );
        })}
        <div className="rail-divider" />
        <button
          type="button"
          className="station-btn"
          aria-current={activeIsText}
          onClick={() => setActiveKey(TEXT_KEY)}
        >
          <span>Text</span>
        </button>
      </nav>

      <main className="canvas">
        {activeIsText ? (
          <>
            <h2>Text</h2>
            <TextStation
              payload={payload}
              busy={busy}
              stamp={stamp}
              run={run}
            />
          </>
        ) : active ? (
          <>
            <h2>{active.title}</h2>
            {active.groups.length > MINI_SPINE_AT ? (
              <div className="mini-spine" aria-label="In this station">
                {active.groups.map((group) => (
                  <button
                    key={group.id}
                    type="button"
                    onClick={() => setHighlightId(group.id)}
                  >
                    {group.label}
                  </button>
                ))}
              </div>
            ) : null}
            {active.groups.map((group) => (
              <WidgetHost
                key={group.id}
                group={group}
                stamp={stamp?.subject === group.id ? stamp : null}
                highlight={highlightId === group.id}
                busy={busy}
                onSelect={(value) =>
                  void run(() =>
                    api.setSelection(characterId, group.id, value),
                  )
                }
                onClear={() =>
                  void run(() => api.clearSelection(characterId, group.id))
                }
              />
            ))}
          </>
        ) : null}
      </main>

      <aside className="record-pane" aria-label="Record">
        <h3>{record.persona.name ?? "Unnamed"}</h3>
        <div className="kv">
          <span className="k">rating</span>
          <span>{view.rating}</span>
        </div>
        <div className="kv">
          <span className="k">version</span>
          <DraftChip record={record} />
        </div>
        <div className="kv">
          <span className="k">groups set</span>
          <span>
            {counts.set}/{counts.total}
          </span>
        </div>
        <div className="kv">
          <span className="k">grade</span>
          <span className="mono">{grade.grade ?? "none yet"}</span>
        </div>
        {grade.notes ? <p className="honest-line">{grade.notes}</p> : null}
        <div className="kv">
          <span className="k">staleness</span>
          <span>
            {staleness.identity_stale.length === 0 &&
            staleness.variable_stale_marked.length === 0
              ? "fresh"
              : [
                  ...staleness.identity_stale,
                  ...staleness.variable_stale_marked,
                ].join(", ")}
          </span>
        </div>
        {payload.orphans.length > 0 ? (
          <div>
            <div className="kv">
              <span className="k">orphans</span>
            </div>
            <ul className="orphan-list">
              {payload.orphans.map((orphan, index) => (
                <li key={index} className="mono">
                  {orphan.group_id}
                  {orphan.option_id ? ` · ${orphan.option_id}` : ""} —{" "}
                  {orphan.reason} ({orphan.location})
                </li>
              ))}
            </ul>
          </div>
        ) : null}
        {activeVersion?.appearance_paragraph ? (
          <div>
            <div className="prose">{activeVersion.appearance_paragraph}</div>
            <p className="caption">
              committed appearance paragraph · v{activeVersion.version}
            </p>
          </div>
        ) : (
          <div>
            <div className="prose">
              {summaryLabels.length > 0
                ? summaryLabels.join(" · ")
                : "Nothing picked yet."}
            </div>
            <p className="caption">
              a preview assembled from the picks — not the paragraph
            </p>
          </div>
        )}
        {!draftOpen(record) ? (
          <button
            type="button"
            disabled={busy}
            onClick={() => void run(() => api.openDraft(characterId))}
          >
            Open a draft
          </button>
        ) : null}
      </aside>

      {paletteOpen ? (
        <JumpPalette
          view={view}
          onJump={jumpTo}
          onClose={() => setPaletteOpen(false)}
        />
      ) : null}
    </div>
  );
}
