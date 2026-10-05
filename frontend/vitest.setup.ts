import "@testing-library/jest-dom/vitest";

// Node >= 25 defines a global `localStorage` that is undefined unless Node runs
// with --localstorage-file, and it shadows jsdom's implementation. Restore jsdom's.
const jsdomWindow = (globalThis as { jsdom?: { window: Window } }).jsdom?.window;
if (jsdomWindow && !globalThis.localStorage) {
  Object.defineProperty(globalThis, "localStorage", {
    value: jsdomWindow.localStorage,
    configurable: true,
  });
}
