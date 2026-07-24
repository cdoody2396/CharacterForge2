// §F.7 refusal surfacing primitives. Codes and subjects display
// verbatim — never renamed, never softened.
import type { Refusal } from "../spine/types";

/** Field-anchored stamp: code verbatim in mono, message beside it. */
export function RefusalStamp({ refusal }: { refusal: Refusal }) {
  return (
    <div className="stamp" role="alert">
      <span className="code">{refusal.code}</span>
      <span className="msg">{refusal.message}</span>
    </div>
  );
}

/** Generic fault card — FastAPI-shaped {detail} bodies, network
 * failures (§E.3), and the unknown-widget fail-loud case (§F.4). */
export function FaultCard({
  title,
  detail,
}: {
  title: string;
  detail?: string | null;
}) {
  return (
    <div className="fault-card" role="alert">
      <span className="code">{title}</span>
      {detail ? <div>{detail}</div> : null}
    </div>
  );
}

/** Full-screen fault: 401 (§D.3 — broken host wiring, not user
 * error) and corrupt-record loads (§F.7). Names the served code. */
export function FaultScreen({
  code,
  message,
  explanation,
}: {
  code: string;
  message: string;
  explanation: string;
}) {
  return (
    <div className="fault-screen" role="alert">
      <div className="code">{code}</div>
      <p>{message}</p>
      <p className="honest-line">{explanation}</p>
    </div>
  );
}

export function RetiredBadge() {
  return <span className="badge badge-retired">retired</span>;
}

export function OrphanedBadge() {
  return <span className="badge badge-orphaned">orphaned</span>;
}
