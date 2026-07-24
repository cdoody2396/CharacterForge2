// §F.2 Session — walks the served creator view: sections in served
// order, groups in `order`, ONE group per screen, the group's real
// widget at large scale (big-type register). Controls: answer
// (mutation → refetch → advance), skip group, skip to workbench,
// per-section progress thread. After creation, one Name screen
// (filtered PUT /name; skippable). The Session ends at the workbench,
// never at finalize (§F.2 — finalize lives in the Atelier only).
import { useMemo, useState } from "react";
import { api } from "../spine/client";
import type { Refusal, ViewGroup } from "../spine/types";
import { stationsOf, subjectMatches, useRecordData } from "../state/recordData";
import { WidgetHost, isMulti } from "../widgets/WidgetHost";
import { FaultScreen, RefusalStamp } from "../parts/faults";
import type { ToastPayload } from "../parts/ToastHost";

type Cursor = { kind: "name" } | { kind: "group"; id: string };

export function Session({
  characterId,
  nameStep,
  onWorkbench,
  onToast,
}: {
  characterId: string;
  nameStep: boolean;
  onWorkbench: () => void;
  onToast: (toast: ToastPayload) => void;
}) {
  const { bundle, failure, mutate } = useRecordData(characterId);
  const [cursor, setCursor] = useState<Cursor | null>(
    nameStep ? { kind: "name" } : null,
  );
  const [stamp, setStamp] = useState<Refusal | null>(null);
  const [busy, setBusy] = useState(false);
  const [name, setName] = useState("");

  const stations = useMemo(
    () => (bundle ? stationsOf(bundle.view) : []),
    [bundle],
  );
  const flat = useMemo(() => stations.flatMap((s) => s.groups), [stations]);
  const ids = useMemo(() => flat.map((group) => group.id), [flat]);

  if (failure) {
    // Corrupt-record and load refusals → full-pane fault naming the
    // served code (§F.7); faults name the transport state.
    return failure.kind === "refusal" ? (
      <FaultScreen
        code={failure.refusal.code}
        message={failure.refusal.message}
        explanation="The record did not load. The code above is the spine's, verbatim."
      />
    ) : (
      <FaultScreen
        code={failure.status === null ? "network failure" : `HTTP ${failure.status}`}
        message={failure.detail ?? "The spine did not answer."}
        explanation="The guided pass cannot run without the spine."
      />
    );
  }
  if (!bundle) return <div className="loading">Reaching the spine…</div>;

  const current: Cursor =
    cursor ?? (ids.length > 0 ? { kind: "group", id: ids[0] } : { kind: "name" });
  const currentGroup: ViewGroup | undefined =
    current.kind === "group"
      ? flat.find((group) => group.id === current.id)
      : undefined;

  const advance = () => {
    setStamp(null);
    if (current.kind === "name") {
      if (ids.length > 0) setCursor({ kind: "group", id: ids[0] });
      else onWorkbench();
      return;
    }
    const at = ids.indexOf(current.id);
    const next = at === -1 ? ids[0] : ids[at + 1];
    if (next === undefined) onWorkbench();
    else setCursor({ kind: "group", id: next });
  };

  const routeRefusal = (refusal: Refusal) => {
    const anchored =
      (current.kind === "group" &&
        subjectMatches(refusal.subject, current.id)) ||
      (current.kind === "name" && refusal.subject === "name");
    if (anchored) setStamp(refusal);
    else onToast({ kind: "refusal", refusal });
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

  // §F.2: answer → mutation → refetch → advance. Single-pick advances
  // on the answer; multi-pick keeps the screen for more toggles and
  // advances by the explicit control (builder detail, recorded).
  const answer = (group: ViewGroup, value: string | string[]) => {
    void run(() => api.setSelection(characterId, group.id, value)).then(
      (ok) => {
        if (ok && !isMulti(group)) advance();
      },
    );
  };

  // Progress thread: per-section set/total, current section marked.
  const currentSectionKey = currentGroup
    ? stations.find((s) => s.groups.some((g) => g.id === currentGroup.id))?.key
    : undefined;

  return (
    <div className="session">
      <div className="session-top">
        <span className="chip-tag">Guided pass</span>
        <span className="spacer" style={{ flex: 1 }} />
        <button type="button" onClick={onWorkbench}>
          Skip to the workbench
        </button>
      </div>
      <div className="progress-thread" aria-label="Progress">
        {stations.map((station) => {
          const set = station.groups.filter((g) => g.current.length > 0).length;
          return (
            <span
              key={station.key}
              className={station.key === currentSectionKey ? "current" : undefined}
            >
              {station.title} {set}/{station.groups.length}
            </span>
          );
        })}
      </div>
      <div className="session-body">
        {current.kind === "name" ? (
          <>
            <div className="session-question">What is their name?</div>
            <p className="session-hint">
              The name passes the spine's filter — it can be set again later
              from the Atelier's Text station.
            </p>
            <input
              aria-label="Name"
              value={name}
              disabled={busy}
              onChange={(event) => setName(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  void run(() => api.setName(characterId, name)).then(
                    (ok) => ok && advance(),
                  );
                }
              }}
            />
            {stamp ? <RefusalStamp refusal={stamp} /> : null}
          </>
        ) : currentGroup ? (
          <>
            <div className="session-question">{currentGroup.label}</div>
            {currentGroup.hint ? (
              <p className="session-hint">{currentGroup.hint}</p>
            ) : null}
            <WidgetHost
              group={currentGroup}
              stamp={stamp}
              busy={busy}
              onSelect={(value) => answer(currentGroup, value)}
              onClear={() =>
                void run(() => api.clearSelection(characterId, currentGroup.id))
              }
            />
          </>
        ) : (
          <p className="loading">Nothing left to walk — the workbench is next.</p>
        )}
      </div>
      <div className="session-controls">
        {current.kind === "name" ? (
          <>
            <button
              type="button"
              disabled={busy}
              onClick={() =>
                void run(() => api.setName(characterId, name)).then(
                  (ok) => ok && advance(),
                )
              }
            >
              Set the name
            </button>
            <button type="button" disabled={busy} onClick={advance}>
              Skip the name
            </button>
          </>
        ) : currentGroup ? (
          <>
            {isMulti(currentGroup) ? (
              <button type="button" disabled={busy} onClick={advance}>
                Continue
              </button>
            ) : null}
            <button type="button" disabled={busy} onClick={advance}>
              Skip this group
            </button>
          </>
        ) : (
          <button type="button" onClick={onWorkbench}>
            To the workbench
          </button>
        )}
      </div>
    </div>
  );
}
