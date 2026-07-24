// §A — three surfaces over the spine: Roster (list, create, open) →
// Session (guided walk) ⇄ Atelier (workbench). Nothing else renders.
// Single-window presentation (§F.9). 401 → full-screen fault (§D.3):
// the host wiring is broken, not the user.
import { useEffect, useState } from "react";
import { onAuthFault } from "./spine/client";
import type { Refusal } from "./spine/types";
import { Roster } from "./surfaces/Roster";
import { Session } from "./surfaces/Session";
import { Atelier } from "./surfaces/Atelier";
import { FaultScreen } from "./parts/faults";
import { ToastHost } from "./parts/ToastHost";
import type { ToastItem } from "./parts/ToastHost";

type AppView =
  | { kind: "roster" }
  | { kind: "session"; id: string; nameStep: boolean }
  | { kind: "atelier"; id: string };

let toastSerial = 0;

export default function App() {
  const [view, setView] = useState<AppView>({ kind: "roster" });
  const [authFault, setAuthFault] = useState<Refusal | null>(null);
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  useEffect(() => onAuthFault(setAuthFault), []);

  const pushToast = (toast: Omit<ToastItem, "id">) => {
    const id = ++toastSerial;
    setToasts((existing) => [...existing, { ...toast, id } as ToastItem]);
  };
  const dismissToast = (id: number) =>
    setToasts((existing) => existing.filter((toast) => toast.id !== id));

  if (authFault) {
    return (
      <FaultScreen
        code={authFault.code}
        message={authFault.message}
        explanation="The spine refused the token. This means the host wiring is broken — start the app through scripts/dev.py — not that you did anything wrong."
      />
    );
  }

  return (
    <div className="app">
      {view.kind === "roster" ? (
        <Roster
          onOpen={(id) => setView({ kind: "atelier", id })}
          onGuided={(id) => setView({ kind: "session", id, nameStep: false })}
          onCreated={(id) => setView({ kind: "session", id, nameStep: true })}
          onToast={pushToast}
        />
      ) : view.kind === "session" ? (
        <Session
          characterId={view.id}
          nameStep={view.nameStep}
          onWorkbench={() => setView({ kind: "atelier", id: view.id })}
          onToast={pushToast}
        />
      ) : (
        <Atelier
          characterId={view.id}
          onRoster={() => setView({ kind: "roster" })}
          onGuided={() =>
            setView({ kind: "session", id: view.id, nameStep: false })
          }
          onToast={pushToast}
        />
      )}
      <ToastHost toasts={toasts} onDismiss={dismissToast} />
    </div>
  );
}
