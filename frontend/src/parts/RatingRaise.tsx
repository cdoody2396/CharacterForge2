// §F.6 rating raise — header control listing the raise targets
// (gate ruling: the fixed ladder standard → mature → explicit is
// mirrored in copy only, like the RATING_DECREASE copy; the spine
// refuses any inadmissible pick). Confirm dialog names the
// irreversibility. Success → full refetch; explicit families simply
// appear. Locked options stay invisible — no teaser.
import { useState } from "react";
import { raiseTargets } from "../state/recordData";
import { Overlay } from "./Overlay";

export function RatingRaise({
  rating,
  busy,
  onRaise,
}: {
  rating: string;
  busy: boolean;
  onRaise: (target: string) => Promise<boolean>;
}) {
  const [open, setOpen] = useState(false);
  const targets = raiseTargets(rating);

  return (
    <>
      <span className="chip-tag">rating: {rating}</span>
      {targets.length > 0 ? (
        <button type="button" disabled={busy} onClick={() => setOpen(true)}>
          Raise rating…
        </button>
      ) : null}
      {open ? (
        <Overlay label="Raise the rating" onClose={() => setOpen(false)}>
          <h3>Raise the rating</h3>
          <p>
            The record is rated <strong>{rating}</strong>. Raising it widens
            what the spine serves.
          </p>
          <p className="danger-copy">
            A rating only ever rises — the spine refuses any lowering
            (RATING_DECREASE). This raise is irreversible.
          </p>
          <div className="overlay-actions">
            <button type="button" onClick={() => setOpen(false)}>
              Keep {rating}
            </button>
            {targets.map((target) => (
              <button
                key={target}
                type="button"
                disabled={busy}
                onClick={() => {
                  void onRaise(target).then((ok) => {
                    if (ok) setOpen(false);
                  });
                }}
              >
                Raise to {target}
              </button>
            ))}
          </div>
        </Overlay>
      ) : null}
    </>
  );
}
