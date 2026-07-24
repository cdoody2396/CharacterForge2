// jsdom test setup: jest-dom matchers, RTL cleanup, and real element
// sizes (jsdom reports zero everywhere; the virtualized picker needs
// a viewport to render rows).
import "@testing-library/jest-dom/vitest";
import { afterEach, vi } from "vitest";
import { cleanup } from "@testing-library/react";

afterEach(() => cleanup());

// jsdom has no ResizeObserver; the virtualizer measures through it.
class ResizeObserverStub {
  constructor(private cb: ResizeObserverCallback) {}
  observe(target: Element) {
    const size = { inlineSize: 800, blockSize: 600 };
    this.cb(
      [
        {
          target,
          contentRect: target.getBoundingClientRect(),
          borderBoxSize: [size],
          contentBoxSize: [size],
          devicePixelContentBoxSize: [size],
        } as ResizeObserverEntry,
      ],
      this as unknown as ResizeObserver,
    );
  }
  unobserve() {}
  disconnect() {}
}
vi.stubGlobal("ResizeObserver", ResizeObserverStub);

Object.defineProperty(HTMLElement.prototype, "clientHeight", {
  configurable: true,
  get() {
    return 600;
  },
});
Object.defineProperty(HTMLElement.prototype, "clientWidth", {
  configurable: true,
  get() {
    return 800;
  },
});
Element.prototype.getBoundingClientRect = function () {
  return {
    width: 800,
    height: 600,
    top: 0,
    left: 0,
    bottom: 600,
    right: 800,
    x: 0,
    y: 0,
    toJSON: () => ({}),
  } as DOMRect;
};
Element.prototype.scrollIntoView = () => {};
