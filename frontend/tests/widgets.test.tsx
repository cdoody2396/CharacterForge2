// §H per-widget component tests against captured fixtures: render,
// select, clear, retired badge, unknown-widget fault card.
import { describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { WidgetHost } from "../src/widgets/WidgetHost";
import { groupFrom, viewFixture } from "./helpers";

const explicit = viewFixture("creator_view_explicit");
const afterSelection = viewFixture("creator_view_after_selection");
const retiredHeld = viewFixture("creator_view_retired_held");

function mount(group: Parameters<typeof WidgetHost>[0]["group"]) {
  const onSelect = vi.fn();
  const onClear = vi.fn();
  render(
    <WidgetHost
      group={group}
      stamp={null}
      busy={false}
      onSelect={onSelect}
      onClear={onClear}
    />,
  );
  return { onSelect, onClear };
}

describe("segmented", () => {
  const group = groupFrom(explicit, "genitalia"); // 5 options → segmented
  it("renders the served menu and re-pick replaces (single value)", async () => {
    const { onSelect } = mount(group);
    expect(group.widget).toBe("segmented");
    for (const option of group.options) {
      expect(screen.getByRole("button", { name: option.label })).toBeInTheDocument();
    }
    await userEvent.click(screen.getByRole("button", { name: "Vulva" }));
    expect(onSelect).toHaveBeenCalledWith("vulva");
  });
});

describe("chips", () => {
  const group = groupFrom(explicit, "eye_features"); // pick_many → chips
  it("toggle sends the FULL new list and shows a live count", async () => {
    expect(group.widget).toBe("chips");
    expect(group.current).toHaveLength(0);
    const { onSelect } = mount(group);
    expect(screen.getByText(/0 selected/)).toBeInTheDocument();
    const first = group.options[0];
    await userEvent.click(screen.getByRole("button", { name: first.label }));
    expect(onSelect).toHaveBeenCalledWith([first.id]);
  });
});

describe("swatch", () => {
  const group = groupFrom(explicit, "skin_tone");
  it("renders circles from served color and labels on selection", async () => {
    expect(group.widget).toBe("swatch");
    const { onSelect } = mount(group);
    const first = group.options[0];
    const circle = screen.getByRole("button", { name: first.label });
    expect(circle).toHaveStyle({ background: first.color ?? "" });
    await userEvent.click(circle);
    expect(onSelect).toHaveBeenCalledWith(first.id);
  });
});

describe("picker", () => {
  it("renders the virtualized list and selects", async () => {
    const group = groupFrom(explicit, "race"); // 112 options
    expect(group.widget).toBe("picker");
    const { onSelect } = mount(group);
    const listbox = screen.getByRole("listbox");
    const options = within(listbox).getAllByRole("option");
    expect(options.length).toBeGreaterThan(0);
    expect(options.length).toBeLessThan(group.options.length); // virtualized window
    await userEvent.click(options[0]);
    expect(onSelect).toHaveBeenCalledWith(group.options[0].id);
  });
});

describe("clear affordance", () => {
  it("appears only with a held value and calls DELETE's handler", async () => {
    const raceHeld = groupFrom(afterSelection, "race"); // holds android
    const { onClear } = mount(raceHeld);
    await userEvent.click(screen.getByRole("button", { name: "Clear" }));
    expect(onClear).toHaveBeenCalled();
  });

  it("is absent when nothing is held", () => {
    mount(groupFrom(explicit, "eye_features"));
    expect(screen.queryByRole("button", { name: "Clear" })).toBeNull();
  });
});

describe("retired held value (captured via the two-phase drop-in run)", () => {
  const group = groupFrom(retiredHeld, "capture_probe");
  it("renders the retired badge and stays functional", async () => {
    expect(group.current[0].retired).toBe(true);
    expect(group.options.map((option) => option.id)).toEqual(["probe_b"]); // menu excludes it
    const { onSelect } = mount(group);
    expect(screen.getByText("retired")).toBeInTheDocument();
    // still functional: the held pick renders and a re-pick replaces
    await userEvent.click(screen.getByRole("button", { name: "Probe B" }));
    expect(onSelect).toHaveBeenCalledWith("probe_b");
  });
});

describe("unknown widget", () => {
  it("renders a visible fault card — fail loud, never skip (§F.4)", () => {
    const group = { ...groupFrom(explicit, "genitalia"), widget: "holo_dial" };
    mount(group);
    expect(screen.getByRole("alert")).toHaveTextContent('unknown widget "holo_dial"');
    expect(screen.getByRole("alert")).toHaveTextContent("genitalia");
  });
});
