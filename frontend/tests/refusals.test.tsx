// §H refusal tests: field-anchored stamp for a group-subject refusal
// (and the §F.6 finalize deep-link), toast for an unmatched subject,
// the 401 full-screen fault — codes verbatim throughout (§F.7).
import { describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "../src/App";
import { Atelier } from "../src/surfaces/Atelier";
import {
  fixture,
  groupFrom,
  mockSpine,
  recordRoutes,
  stationPattern,
  viewFixture,
} from "./helpers";
import type { RecordPayload, Refusal } from "../src/spine/types";

const id = fixture<RecordPayload>("record_payload_fresh").body.record.character_id;
const explicit = viewFixture("creator_view_explicit");

function mountAtelier() {
  render(
    <Atelier
      characterId={id}
      onRoster={() => {}}
      onGuided={() => {}}
      onToast={() => {}}
    />,
  );
}

describe("field-anchored stamp (§F.7) + finalize deep-link (§F.6)", () => {
  it("anchors REQUIRED_GROUP_UNFILLED at the named group's widget", async () => {
    const refusal = fixture<Refusal>("refusal_required_group");
    const named = groupFrom(explicit, refusal.body.subject);
    mockSpine([
      {
        method: "POST",
        path: `/spine/records/${id}/finalize`,
        respond: refusal,
      },
      ...recordRoutes(id, { view: "creator_view_explicit" }),
    ]);
    mountAtelier();

    await userEvent.click(await screen.findByRole("button", { name: "Finalize…" }));
    await userEvent.click(
      screen.getByRole("button", { name: "Finalize this version" }),
    );

    // deep-link: the named group's widget is on canvas with the stamp
    await waitFor(() => {
      const widget = screen.getByLabelText(named.label);
      expect(widget).toBeInTheDocument();
      const alert = screen.getByRole("alert");
      expect(alert).toHaveTextContent("REQUIRED_GROUP_UNFILLED"); // verbatim
      expect(alert).toHaveTextContent(refusal.body.message);
    });
  });
});

describe("unmatched subject → toast (§F.7)", () => {
  it("shows the refusal as a toast when no rendered subject matches", async () => {
    const toasts: unknown[] = [];
    const race = groupFrom(viewFixture("creator_view_after_selection"), "race");
    mockSpine([
      {
        method: "DELETE",
        path: `/spine/records/${id}/selections/race`,
        respond: fixture("refusal_unmatched_subject"),
      },
      ...recordRoutes(id, { view: "creator_view_after_selection" }),
    ]);
    render(
      <Atelier
        characterId={id}
        onRoster={() => {}}
        onGuided={() => {}}
        onToast={(toast) => toasts.push(toast)}
      />,
    );
    const stationButton = await screen.findByRole("button", {
      name: stationPattern(race.section!),
    });
    await userEvent.click(stationButton);
    await userEvent.click(screen.getByRole("button", { name: "Clear" }));
    await waitFor(() => {
      expect(toasts).toHaveLength(1);
      expect(toasts[0]).toMatchObject({
        kind: "refusal",
        refusal: { code: "UNKNOWN_GROUP", subject: "no_such_group" },
      });
    });
  });
});

describe("401 → full-screen fault (§D.3)", () => {
  it("names the code and calls the wiring broken, not the user", async () => {
    mockSpine([
      { method: "GET", path: "/spine/records", respond: fixture("auth_missing") },
    ]);
    render(<App />);
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("AUTH_INVALID");
      expect(screen.getByRole("alert")).toHaveTextContent(/host wiring is broken/);
    });
  });
});
