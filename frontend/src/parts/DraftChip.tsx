// §F.6 — versions surface as a header chip only: active version +
// draft state, read from the served record file.
import type { RecordFile } from "../spine/types";

export function draftOpen(record: RecordFile): boolean {
  return record.draft_identity !== undefined;
}

export function DraftChip({ record }: { record: RecordFile }) {
  const version =
    record.active_version !== undefined
      ? `v${record.active_version}`
      : "no version yet";
  const draft = draftOpen(record) ? "draft open" : "no draft";
  return (
    <span className="chip-tag">
      {version} · {draft}
    </span>
  );
}
