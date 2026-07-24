// §H roster tests: served-field rendering (nothing invented) and the
// open handoff.
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "../src/App";
import { fixture, mockSpine, recordRoutes } from "./helpers";
import type { RecordPayload, RosterResponse } from "../src/spine/types";

const roster = fixture<RosterResponse>("roster");
const entry = roster.body.records[0];
const id = fixture<RecordPayload>("record_payload_fresh").body.record.character_id;

describe("roster cards render served fields only (§F.1)", () => {
  it("shows Unnamed, rating, version state, grade, and no orphan chip at 0", async () => {
    mockSpine([
      { method: "GET", path: "/spine/records", respond: roster },
      ...recordRoutes(id),
    ]);
    render(<App />);
    expect(await screen.findByText("Unnamed")).toBeInTheDocument();
    expect(
      screen.getByText(`rating: ${entry.rating}`),
    ).toBeInTheDocument();
    expect(screen.getByText("no version yet")).toBeInTheDocument();
    expect(screen.getByText("grade: none yet")).toBeInTheDocument();
    expect(entry.orphan_count).toBe(0);
    expect(screen.queryByText(/^orphans:/)).toBeNull();
  });

  it("open lands in the Atelier on that record", async () => {
    mockSpine([
      { method: "GET", path: "/spine/records", respond: roster },
      ...recordRoutes(entry.character_id, { view: "creator_view_explicit" }),
    ]);
    render(<App />);
    await userEvent.click(await screen.findByRole("button", { name: "Open" }));
    expect(await screen.findByRole("navigation")).toBeInTheDocument();
  });
});
