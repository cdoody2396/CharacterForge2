// §F.6 finalize — an Atelier-only ceremony. On success everything is
// refetched and the served grade shows. The G0/G1/G2 ladder renders
// as an explainer (the decided meanings, from the N8 ladder) with the
// honest line that grade building belongs to the image section and is
// not yet available — display, never a control (§I.9, the
// HERE/HARDWARE honesty pattern).
import { useState } from "react";
import type { GradeDerivation } from "../spine/types";
import { Overlay } from "./Overlay";

export function FinalizeCeremony({
  busy,
  grade,
  onFinalize,
}: {
  busy: boolean;
  grade: GradeDerivation | null;
  onFinalize: () => Promise<boolean>;
}) {
  const [open, setOpen] = useState(false);
  const [done, setDone] = useState(false);

  return (
    <>
      <button type="button" disabled={busy} onClick={() => {
        setDone(false);
        setOpen(true);
      }}>
        Finalize…
      </button>
      {open ? (
        <Overlay label="Finalize this identity" onClose={() => setOpen(false)}>
          <h3>Finalize</h3>
          {done ? (
            <>
              <p>
                <span className="confirm-tick">✓</span> Finalized. The served
                grade now reads:{" "}
                <strong className="mono">
                  {grade?.grade ?? "none yet"}
                </strong>
              </p>
              {grade?.notes ? (
                <p className="honest-line">{grade.notes}</p>
              ) : null}
              <div className="overlay-actions">
                <button type="button" onClick={() => setOpen(false)}>
                  Back to the workbench
                </button>
              </div>
            </>
          ) : (
            <>
              <p>
                Finalizing commits the open draft as the next identity
                version. Committed versions are never rewritten — the active
                pointer moves forward.
              </p>
              <div className="ladder" aria-label="Grade ladder (display only)">
                <div className="rung">
                  <span className="code">G0</span>
                  <span>
                    basic — the floor of every character; fully playable,
                    imagery on demand.
                  </span>
                </div>
                <div className="rung">
                  <span className="code">G1</span>
                  <span>
                    canonical — G0 plus the canonical shot set, one pass.
                  </span>
                </div>
                <div className="rung">
                  <span className="code">G2</span>
                  <span>
                    anchored — G1 plus an identity LoRA trained from the
                    reference core, one active.
                  </span>
                </div>
              </div>
              <p className="honest-line">
                Grade building belongs to the image section and is not yet
                available — this ladder is an explainer, not a control.
              </p>
              <div className="overlay-actions">
                <button type="button" onClick={() => setOpen(false)}>
                  Not yet
                </button>
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => {
                    void onFinalize().then((ok) => {
                      if (ok) setDone(true);
                      else setOpen(false); // refusal routed by the surface
                    });
                  }}
                >
                  Finalize this version
                </button>
              </div>
            </>
          )}
        </Overlay>
      ) : null}
    </>
  );
}
