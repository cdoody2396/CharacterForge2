// §E data flow. Opening a record loads four served surfaces in
// parallel (§E.1). After every 2xx mutation the client REFETCHES the
// served state (§E.2) — no optimistic update exists anywhere in this
// app. Hidden groups vanish, revealed groups appear, menus re-cut on
// rating raise — all by refetch, never by prediction.
import { useCallback, useEffect, useRef, useState } from "react";
import { api, SpineFault, SpineRefusal } from "../spine/client";
import type {
  CreatorView,
  GradeDerivation,
  RecordPayload,
  Refusal,
  Staleness,
  ViewGroup,
} from "../spine/types";

export interface RecordBundle {
  view: CreatorView;
  payload: RecordPayload;
  staleness: Staleness;
  grade: GradeDerivation;
}

export type LoadFailure =
  | { kind: "refusal"; status: number; refusal: Refusal }
  | { kind: "fault"; status: number | null; detail: string | null };

export type MutationOutcome =
  | { kind: "ok" }
  | { kind: "refusal"; status: number; refusal: Refusal }
  | { kind: "fault"; status: number | null; detail: string | null };

export function toFailure(error: unknown): LoadFailure {
  if (error instanceof SpineRefusal) {
    return { kind: "refusal", status: error.status, refusal: error.refusal };
  }
  if (error instanceof SpineFault) {
    return { kind: "fault", status: error.status, detail: error.detail };
  }
  throw error;
}

export function useRecordData(characterId: string) {
  const [bundle, setBundle] = useState<RecordBundle | null>(null);
  const [failure, setFailure] = useState<LoadFailure | null>(null);
  const seq = useRef(0);

  const refresh = useCallback(async (): Promise<boolean> => {
    const ticket = ++seq.current;
    try {
      // §E.1 — in parallel: record (+orphans, draft state), creator
      // view, staleness, grade.
      const [payload, view, staleness, grade] = await Promise.all([
        api.getRecord(characterId),
        api.getCreatorView(characterId),
        api.getStaleness(characterId),
        api.getGrade(characterId),
      ]);
      if (ticket === seq.current) {
        setBundle({ payload, view, staleness, grade });
        setFailure(null);
      }
      return true;
    } catch (error) {
      if (ticket === seq.current) setFailure(toFailure(error));
      return false;
    }
  }, [characterId]);

  useEffect(() => {
    setBundle(null);
    setFailure(null);
    void refresh();
  }, [refresh]);

  // Wraps a mutation call: refusals and faults come back as data for
  // §F.7 routing; success triggers the §E.2 refetch before resolving.
  const mutate = useCallback(
    async (call: () => Promise<unknown>): Promise<MutationOutcome> => {
      try {
        await call();
      } catch (error) {
        return toFailure(error);
      }
      await refresh();
      return { kind: "ok" };
    },
    [refresh],
  );

  return { bundle, failure, refresh, mutate };
}

// ---- curation of the served view (§B: narrow or reorder, never widen) ----

/** Gate ruling (O6, recorded): a group whose served menu is empty and
 * which holds no value does not render — §B narrowing in the §I.4
 * no-teaser spirit. It appears after a rating raise via refetch. */
export function visibleGroups(view: CreatorView): ViewGroup[] {
  return view.groups.filter(
    (group) => group.options.length > 0 || group.current.length > 0,
  );
}

export interface Station {
  key: string;
  title: string;
  unfiled: boolean;
  groups: ViewGroup[];
}

export const UNFILED_KEY = "__unfiled__";

/** §F.3: stations = served sections in served (first-appearance)
 * order, groups in `order` within each; a trailing Unfiled station
 * collects section-less groups verbatim. */
export function stationsOf(view: CreatorView): Station[] {
  const sections: Station[] = [];
  const byKey = new Map<string, Station>();
  let unfiled: Station | null = null;
  for (const group of visibleGroups(view)) {
    if (group.section === null) {
      unfiled ??= { key: UNFILED_KEY, title: "Unfiled", unfiled: true, groups: [] };
      unfiled.groups.push(group);
      continue;
    }
    let station = byKey.get(group.section);
    if (!station) {
      station = {
        key: group.section,
        title: group.section,
        unfiled: false,
        groups: [],
      };
      byKey.set(group.section, station);
      sections.push(station);
    }
    station.groups.push(group);
  }
  if (unfiled) sections.push(unfiled);
  for (const station of sections) {
    station.groups = sortByOrder(station.groups);
  }
  return sections;
}

/** Presentation-only ordering by the served `order` key (stable on
 * served order when absent/tied) — a reorder, never a widen. */
export function sortByOrder(groups: ViewGroup[]): ViewGroup[] {
  return [...groups].sort(
    (a, b) =>
      (a.order ?? Number.MAX_SAFE_INTEGER) -
      (b.order ?? Number.MAX_SAFE_INTEGER),
  );
}

export function groupsSetCount(view: CreatorView): {
  set: number;
  total: number;
} {
  const visible = visibleGroups(view);
  return {
    set: visible.filter((group) => group.current.length > 0).length,
    total: visible.length,
  };
}

/** §F.7 anchoring: a refusal subject matches a rendered group when it
 * IS the group id or extends it as "group/option" (the spine's
 * selection refusals carry the compound form — observed in captured
 * fixtures, e.g. "genitalia/vulva"). Display stays verbatim; this
 * only decides where the stamp anchors. */
export function subjectMatches(subject: string, groupId: string): boolean {
  return subject === groupId || subject.startsWith(`${groupId}/`);
}

/** Gate ruling (O6, recorded): raise targets mirror the fixed rating
 * order standard → mature → explicit in copy only — the same
 * mirrored-law status §F.6 grants the RATING_DECREASE copy. The spine
 * still refuses any inadmissible pick. */
export const RATING_LADDER = ["standard", "mature", "explicit"] as const;

export function raiseTargets(current: string): string[] {
  const index = RATING_LADDER.indexOf(
    current as (typeof RATING_LADDER)[number],
  );
  if (index === -1) return [];
  return RATING_LADDER.slice(index + 1);
}
