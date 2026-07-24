// Served shapes, typed one-for-one from the spine's real payloads
// (captured fixtures pin these in tests — §E.4). The client renders
// these facts; it never re-derives them (§B).

/** Every refusal (and the 401s) carries this triple, verbatim. */
export interface Refusal {
  code: string;
  subject: string;
  message: string;
}

/** creator-view menu entry (§G.1: tags served). */
export interface MenuOption {
  id: string;
  label: string;
  rating: string;
  tags: string[];
  color: string | null;
  thumb: string | null;
}

/** creator-view held entry — resolved or orphaned (§G.1: tags served). */
export interface HeldEntry {
  id: string;
  label: string | null;
  retired: boolean;
  orphaned: boolean;
  tags: string[];
  color?: string | null;
  thumb?: string | null;
}

export type SelectionValue = string | string[] | null;

export interface ViewGroup {
  id: string;
  label: string;
  kind: string;
  home: string;
  widget: string;
  required: boolean;
  max_picks: number | null;
  section: string | null;
  order: number | null;
  hint: string | null;
  tags: string[];
  options: MenuOption[];
  value: SelectionValue;
  current: HeldEntry[];
}

export interface CreatorView {
  character_id: string;
  rating: string;
  groups: ViewGroup[];
}

/** GET /records entry. */
export interface RosterGrade {
  grade: string | null;
  determinable: boolean;
  g1_determinable: boolean;
}

export interface RosterEntry {
  character_id: string;
  name: string | null;
  rating: string;
  active_version: number | null;
  grade: RosterGrade;
  orphan_count: number;
}

/** The record file's declared on-disk contract, served verbatim. */
export interface IdentityVersion {
  version: number;
  selections: Record<string, string | string[]>;
  appearance_paragraph: string;
  paragraph_author?: string;
  finalized: string;
  looks_text?: string;
}

export interface DraftIdentity {
  selections: Record<string, string | string[]>;
  looks_text?: string;
  paragraph_edit?: string;
}

export interface PersonaState {
  name?: string;
  name_safety?: string;
  selections: Record<string, string | string[]>;
  story_text?: string;
}

export interface RecordFile {
  format: number;
  character_id: string;
  age: number;
  rating: string;
  created: string;
  active_version?: number;
  identity_versions: IdentityVersion[];
  draft_identity?: DraftIdentity;
  persona: PersonaState;
}

export interface OrphanEntry {
  location: string;
  group_id: string;
  option_id: string | null;
  reason: string;
}

/** {record, orphans} — returned by GET /records/{id} and every mutation. */
export interface RecordPayload {
  record: RecordFile;
  orphans: OrphanEntry[];
}

export interface Staleness {
  identity_stale: string[];
  variable_stale_marked: string[];
}

export interface GradeDerivation {
  character_id: string;
  grade: string | null;
  determinable: boolean;
  g1_determinable: boolean;
  ladder_decided: boolean;
  evidence: Record<string, unknown>;
  notes: string;
}

export interface RosterResponse {
  records: RosterEntry[];
}
