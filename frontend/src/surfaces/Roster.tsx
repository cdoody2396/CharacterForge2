// §F.1 Roster — GET /records → cards of served fields only. Actions:
// open (→ Atelier) · guided pass (→ Session) · create. Create runs
// the age gate as step zero: the age input POSTs /records;
// AGE_UNDER_FLOOR stamps on the field; success opens the Session on
// the new record. No delete exists (§A — no spine endpoint).
import { useCallback, useEffect, useState } from "react";
import { api } from "../spine/client";
import type { RosterEntry, Refusal } from "../spine/types";
import { toFailure } from "../state/recordData";
import type { LoadFailure } from "../state/recordData";
import { FaultCard, RefusalStamp } from "../parts/faults";
import type { ToastPayload } from "../parts/ToastHost";

export function Roster({
  onOpen,
  onGuided,
  onCreated,
  onToast,
}: {
  onOpen: (id: string) => void;
  onGuided: (id: string) => void;
  onCreated: (id: string) => void;
  onToast: (toast: ToastPayload) => void;
}) {
  const [records, setRecords] = useState<RosterEntry[] | null>(null);
  const [failure, setFailure] = useState<LoadFailure | null>(null);
  const [age, setAge] = useState("");
  const [ageStamp, setAgeStamp] = useState<Refusal | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setFailure(null);
    try {
      const response = await api.listRecords();
      setRecords(response.records);
    } catch (error) {
      setFailure(toFailure(error));
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const create = async () => {
    setBusy(true);
    setAgeStamp(null);
    try {
      const payload = await api.createRecord(age === "" ? null : Number(age));
      onCreated(payload.record.character_id);
    } catch (error) {
      const failed = toFailure(error);
      if (failed.kind === "refusal" && failed.refusal.subject === "age") {
        setAgeStamp(failed.refusal); // AGE_UNDER_FLOOR stamps on the field
      } else if (failed.kind === "refusal") {
        onToast({ kind: "refusal", refusal: failed.refusal });
      } else {
        onToast({
          kind: "fault",
          title: failed.status === null ? "network failure" : `HTTP ${failed.status}`,
          detail: failed.detail,
        });
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="roster">
      <div className="roster-head">
        <h1>CharacterForge</h1>
        <span className="chip-tag">Roster</span>
      </div>
      {failure ? (
        <FaultCard
          title={
            failure.kind === "refusal"
              ? failure.refusal.code
              : failure.status === null
                ? "network failure"
                : `HTTP ${failure.status}`
          }
          detail={
            failure.kind === "refusal"
              ? failure.refusal.message
              : (failure.detail ?? "The spine did not answer.")
          }
        />
      ) : null}
      <div className="roster-grid">
        <div className="create-card">
          <h3>New character</h3>
          <p className="floor-copy">
            CharacterForge is for characters aged 20 and over — the spine
            holds that floor and refuses anything under it.
          </p>
          <label>
            Age
            <input
              type="number"
              aria-label="Age"
              value={age}
              disabled={busy}
              onChange={(event) => setAge(event.target.value)}
            />
          </label>
          {ageStamp ? <RefusalStamp refusal={ageStamp} /> : null}
          <div>
            <button type="button" disabled={busy} onClick={() => void create()}>
              Begin the guided pass
            </button>
          </div>
        </div>
        {(records ?? []).map((entry) => (
          <div key={entry.character_id} className="record-card">
            <h3>{entry.name ?? "Unnamed"}</h3>
            <div className="meta">
              <span className="chip-tag">rating: {entry.rating}</span>
              <span className="chip-tag">
                {entry.active_version !== null
                  ? `v${entry.active_version}`
                  : "no version yet"}
              </span>
              <span className="chip-tag">
                grade: {entry.grade.grade ?? "none yet"}
              </span>
              {entry.orphan_count > 0 ? (
                <span className="chip-tag">
                  orphans: {entry.orphan_count}
                </span>
              ) : null}
            </div>
            <div className="actions">
              <button type="button" onClick={() => onOpen(entry.character_id)}>
                Open
              </button>
              <button
                type="button"
                onClick={() => onGuided(entry.character_id)}
              >
                Guided pass
              </button>
            </div>
          </div>
        ))}
      </div>
      {records !== null && records.length === 0 ? (
        <p className="loading">No characters yet — begin one above.</p>
      ) : null}
      {records === null && failure === null ? (
        <p className="loading">Reaching the spine…</p>
      ) : null}
    </div>
  );
}
