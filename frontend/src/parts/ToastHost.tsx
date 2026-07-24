// §F.7: record-level or unmatched-subject refusals surface as a toast
// carrying the same {code, subject, message} shape; faults surface as
// generic fault-styled cards.
import type { Refusal } from "../spine/types";

export type ToastPayload =
  | { kind: "refusal"; refusal: Refusal }
  | { kind: "fault"; title: string; detail: string | null };

export type ToastItem = ToastPayload & { id: number };

export function ToastHost({
  toasts,
  onDismiss,
}: {
  toasts: ToastItem[];
  onDismiss: (id: number) => void;
}) {
  if (toasts.length === 0) return null;
  return (
    <div className="toast-host">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={toast.kind === "fault" ? "toast toast-fault" : "toast"}
          role="alert"
        >
          {toast.kind === "refusal" ? (
            <>
              <span className="code">{toast.refusal.code}</span>
              <span className="msg">{toast.refusal.message}</span>
            </>
          ) : (
            <>
              <span className="code">{toast.title}</span>
              {toast.detail ? <span className="msg">{toast.detail}</span> : null}
            </>
          )}
          <button
            type="button"
            aria-label="Dismiss"
            onClick={() => onDismiss(toast.id)}
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
}
