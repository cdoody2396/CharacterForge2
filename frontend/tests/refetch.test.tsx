// §H refetch-law test: a mutation triggers a creator-view refetch and
// a revealed group appears — with NO client prediction (§E.2). The
// mock serves the pre-selection capture until the POST lands, then
// the post-selection capture; the revealed group can only appear if
// the client actually refetched.
import { describe, expect, it } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Atelier } from "../src/surfaces/Atelier";
import {
  fixture,
  groupFrom,
  mockSpine,
  recordRoutes,
  stationPattern,
  viewFixture,
} from "./helpers";
import type { RecordPayload } from "../src/spine/types";

const fresh = viewFixture("creator_view_fresh");
const after = viewFixture("creator_view_after_selection");
const id = fixture<RecordPayload>("record_payload_fresh").body.record.character_id;
const race = groupFrom(fresh, "race");
const revealed = groupFrom(after, "chassis_seams"); // hidden until race=android

describe("the refetch law (§E.2)", () => {
  it("refetches the creator view after a 2xx mutation; the reveal appears", async () => {
    let selected = false;
    const calls = mockSpine([
      {
        method: "POST",
        path: `/spine/records/${id}/selections`,
        respond: () => {
          selected = true;
          return fixture("record_payload_fresh");
        },
      },
      ...recordRoutes(id, {
        view: () =>
          selected
            ? fixture("creator_view_after_selection")
            : fixture("creator_view_fresh"),
      }),
    ]);
    render(
      <Atelier
        characterId={id}
        onRoster={() => {}}
        onGuided={() => {}}
        onToast={() => {}}
      />,
    );

    // open the station that holds the race group
    const stationButton = await screen.findByRole("button", {
      name: stationPattern(race.section!),
    });
    await userEvent.click(stationButton);
    expect(screen.queryByLabelText(revealed.label)).toBeNull(); // not predicted

    // answer race=android through the heavy picker (scoped to the
    // race widget — hybrid_race carries its own heavy kit beside it)
    const raceWidget = within(document.getElementById("group-race")!);
    await userEvent.type(raceWidget.getByLabelText("Filter options"), "android");
    await userEvent.click(raceWidget.getByRole("option", { name: "Android" }));

    // the POST happened, then a FRESH creator-view GET followed it
    await waitFor(() => {
      const postAt = calls.findIndex((call) => call.method === "POST");
      expect(postAt).toBeGreaterThan(-1);
      expect(calls[postAt].body).toEqual({ group_id: "race", value: "android" });
      const refetchAt = calls.findIndex(
        (call, index) =>
          index > postAt &&
          call.method === "GET" &&
          call.path === `/spine/records/${id}/creator-view`,
      );
      expect(refetchAt).toBeGreaterThan(postAt);
    });

    // the revealed group appears only because the refetch served it —
    // its station (absent before the reveal) now exists; open it
    const revealedStation = await screen.findByRole("button", {
      name: stationPattern(revealed.section!),
    });
    await userEvent.click(revealedStation);
    await waitFor(() => {
      expect(document.getElementById(`group-${revealed.id}`)).not.toBeNull();
    });
  });
});
