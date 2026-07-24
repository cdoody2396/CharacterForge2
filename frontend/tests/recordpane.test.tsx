// §H record-pane tests: the committed-paragraph vs captioned-preview
// distinction (§F.3) — plus the empty-menu narrowing gate ruling
// (recorded in SESSION_REPORT_O6): a served group with an empty menu
// and no held value does not render at standard, and appears after
// the rating raise re-cut.
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Atelier } from "../src/surfaces/Atelier";
import { fixture, groupFrom, mockSpine, viewFixture, recordRoutes } from "./helpers";
import type { RecordPayload } from "../src/spine/types";

const finalized = fixture<RecordPayload>("record_payload_finalized");
const id = finalized.body.record.character_id;
const paragraph = finalized.body.record.identity_versions[0].appearance_paragraph;

function mount() {
  render(
    <Atelier
      characterId={id}
      onRoster={() => {}}
      onGuided={() => {}}
      onToast={() => {}}
    />,
  );
}

describe("prose block (§F.3)", () => {
  it("shows the committed appearance paragraph when the active version carries one", async () => {
    mockSpine(
      recordRoutes(id, {
        record: "record_payload_finalized",
        view: "creator_view_explicit",
        grade: "grade_after_finalize",
      }),
    );
    mount();
    expect(await screen.findByText(paragraph)).toBeInTheDocument();
    expect(
      screen.getByText(/committed appearance paragraph · v1/),
    ).toBeInTheDocument();
    expect(screen.queryByText(/not the paragraph/)).toBeNull();
  });

  it("otherwise assembles a pick summary captioned as a preview — never as the paragraph", async () => {
    mockSpine(
      recordRoutes(id, {
        record: "record_payload_fresh",
        view: "creator_view_after_selection",
      }),
    );
    mount();
    expect(
      await screen.findByText("a preview assembled from the picks — not the paragraph"),
    ).toBeInTheDocument();
    expect(screen.queryByText(/committed appearance paragraph/)).toBeNull();
  });
});

describe("grade honesty (§F.3)", () => {
  it("renders the served grade verbatim and says so when the provider cannot know", async () => {
    const grade = fixture<{ grade: string | null; notes: string }>("grade");
    mockSpine(recordRoutes(id, { view: "creator_view_after_selection" }));
    mount();
    expect(await screen.findByText("none yet")).toBeInTheDocument();
    if (grade.body.notes) {
      expect(screen.getByText(grade.body.notes)).toBeInTheDocument();
    }
  });
});

describe("empty-menu narrowing (gate ruling, §B/§I.4)", () => {
  // the real tree serves `genitalia` with zero admissible options at
  // standard rating (explicit-file group, no visible_when)
  it("does not render the group at standard (empty menu, no value) — no teaser", async () => {
    const fresh = groupFrom(viewFixture("creator_view_fresh"), "genitalia");
    expect(fresh.options).toHaveLength(0); // the served fact this ruling narrows
    mockSpine(recordRoutes(id, { view: "creator_view_fresh" })); // standard
    mount();
    await userEvent.click(await screen.findByRole("button", { name: /^Unfiled/ }));
    expect(document.getElementById("group-genitalia")).toBeNull();
  });

  it("renders it after the rating raise re-cuts the menus", async () => {
    mockSpine(recordRoutes(id, { view: "creator_view_explicit" }));
    mount();
    await userEvent.click(await screen.findByRole("button", { name: /^Unfiled/ }));
    await screen.findByRole("navigation");
    expect(document.getElementById("group-genitalia")).not.toBeNull();
  });
});
