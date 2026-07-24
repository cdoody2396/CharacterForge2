// The spine client (§D/§E). Fetches only relative paths under
// /spine/* — the app never knows the spine's origin (§D.1). Every
// request carries X-Spine-Token (§D.3). Any non-2xx with a
// {code, subject, message} body throws SpineRefusal; FastAPI-shaped
// {detail} bodies and network failures throw SpineFault (§E.3).
import { config } from "./config";
import type {
  CreatorView,
  GradeDerivation,
  RecordPayload,
  Refusal,
  RosterResponse,
  Staleness,
} from "./types";

export class SpineRefusal extends Error {
  constructor(
    readonly status: number,
    readonly refusal: Refusal,
  ) {
    super(`[${refusal.code}] ${refusal.message}`);
    this.name = "SpineRefusal";
  }
}

export class SpineFault extends Error {
  constructor(
    readonly status: number | null,
    readonly detail: string | null,
  ) {
    super(detail ?? (status === null ? "network failure" : `HTTP ${status}`));
    this.name = "SpineFault";
  }
}

// §D.3: a 401 means the host wiring is broken, not a user error — the
// app renders a full-screen fault. The listener is installed by App.
let authFaultListener: ((refusal: Refusal) => void) | null = null;

export function onAuthFault(listener: (refusal: Refusal) => void): () => void {
  authFaultListener = listener;
  return () => {
    if (authFaultListener === listener) authFaultListener = null;
  };
}

function asRefusal(data: unknown): Refusal | null {
  if (typeof data !== "object" || data === null) return null;
  const body = data as Record<string, unknown>;
  if (
    typeof body.code === "string" &&
    typeof body.subject === "string" &&
    typeof body.message === "string"
  ) {
    return { code: body.code, subject: body.subject, message: body.message };
  }
  return null;
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/spine${path}`, {
      method,
      headers: {
        "X-Spine-Token": config.token,
        ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new SpineFault(null, null); // network failure → generic fault card
  }
  if (response.ok) return (await response.json()) as T;

  let data: unknown = null;
  try {
    data = await response.json();
  } catch {
    throw new SpineFault(response.status, null);
  }
  const refusal = asRefusal(data);
  if (refusal) {
    if (response.status === 401) authFaultListener?.(refusal);
    throw new SpineRefusal(response.status, refusal);
  }
  const detail = (data as Record<string, unknown> | null)?.detail;
  throw new SpineFault(
    response.status,
    typeof detail === "string" ? detail : null,
  );
}

// ---- endpoint surface (the usage map, as built) ----

export const api = {
  listRecords: () => request<RosterResponse>("GET", "/records"),
  createRecord: (age: unknown) =>
    request<RecordPayload>("POST", "/records", { age }),
  getRecord: (id: string) => request<RecordPayload>("GET", `/records/${id}`),
  getCreatorView: (id: string) =>
    request<CreatorView>("GET", `/records/${id}/creator-view`),
  getStaleness: (id: string) =>
    request<Staleness>("GET", `/records/${id}/staleness`),
  getGrade: (id: string) =>
    request<GradeDerivation>("GET", `/records/${id}/grade`),
  raiseRating: (id: string, rating: string) =>
    request<RecordPayload>("POST", `/records/${id}/rating`, { rating }),
  setSelection: (id: string, groupId: string, value: string | string[]) =>
    request<RecordPayload>("POST", `/records/${id}/selections`, {
      group_id: groupId,
      value,
    }),
  clearSelection: (id: string, groupId: string) =>
    request<RecordPayload>("DELETE", `/records/${id}/selections/${groupId}`),
  openDraft: (id: string) =>
    request<RecordPayload>("POST", `/records/${id}/draft`),
  finalize: (id: string) =>
    request<RecordPayload>("POST", `/records/${id}/finalize`),
  setName: (id: string, name: unknown) =>
    request<RecordPayload>("PUT", `/records/${id}/name`, { name }),
  revalidateName: (id: string) =>
    request<RecordPayload>("POST", `/records/${id}/name/revalidate`),
  setLooksText: (id: string, text: unknown) =>
    request<RecordPayload>("PUT", `/records/${id}/looks-text`, { text }),
  clearLooksText: (id: string) =>
    request<RecordPayload>("DELETE", `/records/${id}/looks-text`),
  setStoryText: (id: string, text: unknown) =>
    request<RecordPayload>("PUT", `/records/${id}/story-text`, { text }),
  clearStoryText: (id: string) =>
    request<RecordPayload>("DELETE", `/records/${id}/story-text`),
  editAppearanceParagraph: (id: string, text: unknown) =>
    request<RecordPayload>("PUT", `/records/${id}/appearance-paragraph`, {
      text,
    }),
};
