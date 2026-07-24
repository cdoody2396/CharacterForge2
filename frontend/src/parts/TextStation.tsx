// §F.5 — the Text station: name (set / revalidate), looks text
// (draft-scoped), story text, appearance-paragraph editor
// (draft-scoped) — the existing endpoints only. §I.2 stays sealed: no
// catalog free_text group exists here. Draft-scoped editors render
// disabled-with-reason when no draft is open, with an inline
// open-draft affordance; a raced IDENTITY_NO_DRAFT refusal remains
// the truth and stamps normally (§F.7 anchors it by subject).
import { useEffect, useState } from "react";
import { api } from "../spine/client";
import type { RecordPayload, Refusal } from "../spine/types";
import { draftOpen } from "./DraftChip";
import { RefusalStamp } from "./faults";

export const TEXT_SLOTS = [
  "name",
  "looks_text",
  "story_text",
  "appearance_paragraph",
] as const;

function useSynced(served: string): [string, (next: string) => void] {
  const [text, setText] = useState(served);
  useEffect(() => setText(served), [served]);
  return [text, setText];
}

export function TextStation({
  payload,
  busy,
  stamp,
  run,
}: {
  payload: RecordPayload;
  busy: boolean;
  stamp: Refusal | null;
  run: (call: () => Promise<unknown>) => Promise<boolean>;
}) {
  const record = payload.record;
  const id = record.character_id;
  const hasDraft = draftOpen(record);
  const active = record.identity_versions.find(
    (version) => version.version === record.active_version,
  );

  const [name, setName] = useSynced(record.persona.name ?? "");
  const [looks, setLooks] = useSynced(record.draft_identity?.looks_text ?? "");
  const [story, setStory] = useSynced(record.persona.story_text ?? "");
  const [paragraph, setParagraph] = useSynced(
    record.draft_identity?.paragraph_edit ?? active?.appearance_paragraph ?? "",
  );

  const stampFor = (slot: string) =>
    stamp && stamp.subject === slot ? <RefusalStamp refusal={stamp} /> : null;

  const openDraft = (
    <div className="row">
      <span className="disabled-reason">
        No draft is open — this editor is draft-scoped.
      </span>
      <button type="button" disabled={busy} onClick={() => void run(() => api.openDraft(id))}>
        Open a draft
      </button>
    </div>
  );

  return (
    <div className="text-station">
      <div className="editor-block">
        <div className="row">
          <strong>Name</strong>
          {record.persona.name_safety ? (
            <span className="chip-tag">
              name safety: {record.persona.name_safety}
            </span>
          ) : null}
        </div>
        <input
          aria-label="Name"
          value={name}
          disabled={busy}
          onChange={(event) => setName(event.target.value)}
        />
        <div className="row">
          <button
            type="button"
            disabled={busy}
            onClick={() => void run(() => api.setName(id, name))}
          >
            Set name
          </button>
          <button
            type="button"
            disabled={busy || record.persona.name === undefined}
            onClick={() => void run(() => api.revalidateName(id))}
          >
            Revalidate
          </button>
        </div>
        {stampFor("name")}
      </div>

      <div className="editor-block">
        <div className="row">
          <strong>Looks text</strong>
          <span className="chip-tag">draft-scoped</span>
        </div>
        {hasDraft ? (
          <>
            <textarea
              aria-label="Looks text"
              rows={4}
              value={looks}
              disabled={busy}
              onChange={(event) => setLooks(event.target.value)}
            />
            <div className="row">
              <button
                type="button"
                disabled={busy}
                onClick={() => void run(() => api.setLooksText(id, looks))}
              >
                Save looks text
              </button>
              <button
                type="button"
                disabled={busy || record.draft_identity?.looks_text === undefined}
                onClick={() => void run(() => api.clearLooksText(id))}
              >
                Clear
              </button>
            </div>
          </>
        ) : (
          openDraft
        )}
        {stampFor("looks_text")}
      </div>

      <div className="editor-block">
        <div className="row">
          <strong>Story text</strong>
        </div>
        <textarea
          aria-label="Story text"
          rows={4}
          value={story}
          disabled={busy}
          onChange={(event) => setStory(event.target.value)}
        />
        <div className="row">
          <button
            type="button"
            disabled={busy}
            onClick={() => void run(() => api.setStoryText(id, story))}
          >
            Save story text
          </button>
          <button
            type="button"
            disabled={busy || record.persona.story_text === undefined}
            onClick={() => void run(() => api.clearStoryText(id))}
          >
            Clear
          </button>
        </div>
        {stampFor("story_text")}
      </div>

      <div className="editor-block">
        <div className="row">
          <strong>Appearance paragraph</strong>
          <span className="chip-tag">draft-scoped</span>
        </div>
        {hasDraft ? (
          <>
            <textarea
              aria-label="Appearance paragraph"
              rows={6}
              value={paragraph}
              disabled={busy}
              onChange={(event) => setParagraph(event.target.value)}
            />
            <div className="row">
              <button
                type="button"
                disabled={busy}
                onClick={() =>
                  void run(() => api.editAppearanceParagraph(id, paragraph))
                }
              >
                Save paragraph edit
              </button>
            </div>
          </>
        ) : (
          openDraft
        )}
        {stampFor("appearance_paragraph")}
      </div>
    </div>
  );
}
