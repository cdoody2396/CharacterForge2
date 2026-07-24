// §H heavy-kit tests: filter, facet counts from served tags, sort
// modes, pinned current, and the ≥ 24 activation threshold.
import { describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { WidgetHost } from "../src/widgets/WidgetHost";
import { facetCounts } from "../src/widgets/HeavyKit";
import { groupFrom, viewFixture } from "./helpers";

const explicit = viewFixture("creator_view_explicit");
const afterSelection = viewFixture("creator_view_after_selection");
const race = groupFrom(explicit, "race"); // 112 served options, tagged

function mount(group: typeof race) {
  const onSelect = vi.fn();
  render(
    <WidgetHost
      group={group}
      stamp={null}
      busy={false}
      onSelect={onSelect}
      onClear={vi.fn()}
    />,
  );
  return onSelect;
}

describe("activation threshold (≥ 24 served options)", () => {
  it("activates on a real ≥ 24 group", () => {
    mount(race);
    expect(screen.getByLabelText("Filter options")).toBeInTheDocument();
  });

  it("stays off below 24 (the same served group narrowed in-test)", () => {
    mount({ ...race, options: race.options.slice(0, 23) });
    expect(screen.queryByLabelText("Filter options")).toBeNull();
  });

  it("activates at exactly 24", () => {
    mount({ ...race, options: race.options.slice(0, 24) });
    expect(screen.getByLabelText("Filter options")).toBeInTheDocument();
  });
});

describe("type-to-filter on labels", () => {
  it("narrows the list and reports the count", async () => {
    mount(race);
    await userEvent.type(screen.getByLabelText("Filter options"), "android");
    const listbox = screen.getByRole("listbox");
    const options = within(listbox).getAllByRole("option");
    expect(options.map((option) => option.textContent)).toContain("Android");
    expect(screen.getByText(/1 of 112/)).toBeInTheDocument();
  });
});

describe("facet chips from served tags (§G.1)", () => {
  it("shows counts that match the served tag data and filters on toggle", async () => {
    mount(race);
    const counts = new Map(facetCounts(race.options));
    const constructCount = counts.get("construct");
    expect(constructCount).toBeGreaterThan(0);
    const chip = screen.getByRole("button", {
      name: `construct · ${constructCount}`,
    });
    await userEvent.click(chip);
    expect(
      screen.getByText(new RegExp(`${constructCount} of 112`)),
    ).toBeInTheDocument();
    const listbox = screen.getByRole("listbox");
    for (const option of within(listbox).getAllByRole("option")) {
      const served = race.options.find(
        (candidate) => candidate.label === option.textContent,
      );
      expect(served?.tags).toContain("construct");
    }
  });
});

describe("sort modes (presentation only)", () => {
  it("A–Z reorders; catalog restores the served order", async () => {
    mount(race);
    const alphaFirst = [...race.options].sort((a, b) =>
      a.label.localeCompare(b.label),
    )[0];
    await userEvent.click(screen.getByRole("button", { name: "A–Z" }));
    let options = within(screen.getByRole("listbox")).getAllByRole("option");
    expect(options[0].textContent).toBe(alphaFirst.label);
    await userEvent.click(screen.getByRole("button", { name: "Catalog" }));
    options = within(screen.getByRole("listbox")).getAllByRole("option");
    expect(options[0].textContent).toBe(race.options[0].label);
  });
});

describe("pinned current", () => {
  it("keeps the held value visible above the list even when filtered away", async () => {
    const held = groupFrom(afterSelection, "race"); // holds android
    mount(held);
    await userEvent.type(screen.getByLabelText("Filter options"), "vampire");
    // the pinned row survives a filter that excludes it
    expect(
      screen.getAllByRole("button", { name: /Android/ }).length,
    ).toBeGreaterThan(0);
  });
});
