// Component-test helpers: captured-fixture loading (§E.4 — fixtures
// come from a real spine run, never hand-written) and a routed fetch
// mock that replays those captures.
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { vi } from "vitest";
import type { CreatorView, ViewGroup } from "../src/spine/types";

const DIR = dirname(fileURLToPath(import.meta.url));

export interface Captured<T = unknown> {
  status: number;
  body: T;
}

export function fixture<T = unknown>(name: string): Captured<T> {
  return JSON.parse(
    readFileSync(join(DIR, "fixtures", `${name}.json`), "utf-8"),
  ) as Captured<T>;
}

export function viewFixture(name: string): CreatorView {
  return fixture<CreatorView>(name).body;
}

export function groupFrom(view: CreatorView, id: string): ViewGroup {
  const group = view.groups.find((entry) => entry.id === id);
  if (!group) throw new Error(`fixture has no group '${id}'`);
  return group;
}

/** Accessible-name pattern for a rail station button: its title plus
 * the set/total count ("Identity 0/8") — anchored so sibling sections
 * sharing a prefix cannot collide. */
export function stationPattern(title: string): RegExp {
  const escaped = title.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return new RegExp(`^${escaped}\\s*\\d+/\\d+$`);
}

export interface SpineCall {
  method: string;
  path: string;
  body: unknown;
}

export interface Route {
  method: string;
  path: string | RegExp;
  respond: Captured | ((call: SpineCall) => Captured);
}

/** Install a fetch mock that answers /spine/* from routes, first
 * match wins; records every call for refetch-law assertions. */
export function mockSpine(routes: Route[]): SpineCall[] {
  const calls: SpineCall[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const path = String(input);
      const method = init?.method ?? "GET";
      const call: SpineCall = {
        method,
        path,
        body: init?.body ? JSON.parse(String(init.body)) : undefined,
      };
      calls.push(call);
      const route = routes.find(
        (candidate) =>
          candidate.method === method &&
          (typeof candidate.path === "string"
            ? candidate.path === path
            : candidate.path.test(path)),
      );
      if (!route) throw new TypeError(`unmocked ${method} ${path}`);
      const { status, body } =
        typeof route.respond === "function" ? route.respond(call) : route.respond;
      return new Response(JSON.stringify(body), {
        status,
        headers: { "Content-Type": "application/json" },
      });
    }),
  );
  return calls;
}

/** The standard route set for an open record over captured fixtures;
 * pass overrides first — first match wins. */
export function recordRoutes(
  id: string,
  names: {
    record?: string;
    view?: string | ((call: SpineCall) => Captured);
    staleness?: string;
    grade?: string;
  } = {},
): Route[] {
  const viewRespond = names.view;
  return [
    {
      method: "GET",
      path: `/spine/records/${id}`,
      respond: fixture(names.record ?? "record_payload_fresh"),
    },
    {
      method: "GET",
      path: `/spine/records/${id}/creator-view`,
      respond:
        typeof viewRespond === "function"
          ? viewRespond
          : fixture(viewRespond ?? "creator_view_fresh"),
    },
    {
      method: "GET",
      path: `/spine/records/${id}/staleness`,
      respond: fixture(names.staleness ?? "staleness"),
    },
    {
      method: "GET",
      path: `/spine/records/${id}/grade`,
      respond: fixture(names.grade ?? "grade"),
    },
  ];
}
