# Phase 2 — Theme/runtime invalidation

## Goal

Keep `_chromeY()`'s cache correct when the chrome changes after construction:
a header `ResizeObserver` for runtime header-height changes, and a document
`tanga:themechange` event for theme swaps. Both clear the cache and re-emit
`preferredchange`/`constraintschange` so enclosing containers re-layout.

## Files

- Edit: `py/pytanga/viz/templates/views/group-view.js`
- Edit: `py/pytanga/viz/templates/viewer.js`
- New: `dev/src/js-tests/group-chrome.test.mjs`

## Steps

- [x] **2.1 — Header `ResizeObserver`.**
  - In `_setupChrome()` (after `this._header` is created), create
    `this._headerResizeObserver` observing `this._header`; skip when
    `ResizeObserver` is undefined.
  - In the callback, compare `entry.contentRect.height` to the previously seen
    height; if it changed, clear `this._chromeY` and emit `preferredchange` +
    `constraintschange` (full size field list), then store the new height.

- [x] **2.2 — `tanga:themechange` event + `destroy()` cleanup.**
  - In `viewer.js`'s `theme_define` handler, dispatch
    `document.dispatchEvent(new CustomEvent('tanga:themechange'))` after
    `applyThemeBackgrounds()` runs (in both the `ready.then(...)` and sync
    branches).
  - In `GroupView`, subscribe in the constructor (`_onThemeChange`: clear
    `_chromeY`, emit `preferredchange` + `constraintschange`).
  - Add a `GroupView.destroy()` override that disconnects the header observer
    and removes the `tanga:themechange` listener, then calls `super.destroy()`.

- [x] **2.3 — Focused unit test `group-chrome.test.mjs`.**
  - Reuse the fake-DOM setup (fake `ResizeObserver`, `document`, `makeEl`).
  - Assert `_chromeY()` returns the fallback `{ folded: 38, chrome: 53 }` when
    measurement is unavailable, and `preferredPx('y', 0)` = child pref + 53.
  - Attach stubbed `getBoundingClientRect` (on `el`/`_header`) + a
    `globalThis.getComputedStyle` stub, then assert `_chromeY()` measures the
    expected 38/53 from those numbers.
  - Assert clearing the cache + emitting happens on the theme event: dispatch
    `tanga:themechange` and check `preferredchange`/`constraintschange` fire
    and `_chromeY` is re-measured.

## Validation

```powershell
node --test 'dev/src/js-tests/*.test.mjs'
```

## Notes

- The theme event keeps the chrome correct even when a theme changes padding,
  border, or margin (which the header `ResizeObserver` alone would not catch).
