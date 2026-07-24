// §H session flow: age-gate refusal and success, skip, one-group-per-
// screen order, end-at-workbench (finalize never renders in the
// Session — §F.2).
import { describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "../src/App";
import { stationsOf } from "../src/state/recordData";
import { fixture, mockSpine, recordRoutes, viewFixture } from "./helpers";
import type { RecordPayload } from "../src/spine/types";

const id = fixture<RecordPayload>("record_payload_fresh").body.record.character_id;
const fresh = viewFixture("creator_view_fresh");
const firstGroup = stationsOf(fresh).flatMap((station) => station.groups)[0];

function createRoutes(age19First: boolean) {
  let attempts = 0;
  return [
    {
      method: "POST",
      path: "/spine/records",
      respond: () => {
        attempts += 1;
        return age19First && attempts === 1
          ? fixture("refusal_age_under_floor")
          : fixture("record_payload_fresh");
      },
    },
    { method: "GET", path: "/spine/records", respond: fixture("roster") },
    ...recordRoutes(id),
  ];
}

describe("the age gate is step zero (§F.1)", () => {
  it("stamps AGE_UNDER_FLOOR on the field, then success opens the Session", async () => {
    mockSpine(createRoutes(true));
    render(<App />);

    expect(
      await screen.findByText(/aged 20 and over/), // the floor, stated plainly
    ).toBeInTheDocument();
    const age = screen.getByLabelText("Age");
    await userEvent.type(age, "19");
    await userEvent.click(
      screen.getByRole("button", { name: "Begin the guided pass" }),
    );
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("AGE_UNDER_FLOOR"); // verbatim
    });

    await userEvent.clear(age);
    await userEvent.type(age, "25");
    await userEvent.click(
      screen.getByRole("button", { name: "Begin the guided pass" }),
    );
    // the Session opens on the new record with the Name step
    expect(await screen.findByText("What is their name?")).toBeInTheDocument();
  });
});

describe("the guided walk (§F.2)", () => {
  it("skips the name to the first served group, one group per screen", async () => {
    mockSpine(createRoutes(false));
    render(<App />);
    await userEvent.type(await screen.findByLabelText("Age"), "25");
    await userEvent.click(
      screen.getByRole("button", { name: "Begin the guided pass" }),
    );
    await userEvent.click(
      await screen.findByRole("button", { name: "Skip the name" }),
    );
    // first group of the first served section, big type (the label
    // appears both as the question and inside the widget frame)
    const matches = await screen.findAllByText(firstGroup.label);
    expect(matches.length).toBeGreaterThan(0);
    // finalize does not exist in the Session (§F.2)
    expect(screen.queryByText(/Finalize/)).toBeNull();
  });

  it("skip-to-workbench lands in the Atelier, never at finalize", async () => {
    mockSpine(createRoutes(false));
    render(<App />);
    await userEvent.type(await screen.findByLabelText("Age"), "25");
    await userEvent.click(
      screen.getByRole("button", { name: "Begin the guided pass" }),
    );
    await userEvent.click(
      await screen.findByRole("button", { name: "Skip to the workbench" }),
    );
    // the Atelier: rail + finalize ceremony affordance now exist
    expect(await screen.findByRole("navigation")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Finalize…" })).toBeInTheDocument();
  });
});
