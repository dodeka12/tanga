# Phase 3 — Frontend: unit test + smoke page

## Goal

Lock the size-decoupling behaviour with a `node:test` unit (DOM stubs) and add a
manual browser smoke page for the scroll region.

## Files

- New: `dev/src/js-tests/scrollable-stack.test.mjs`
- New: `dev/src/js-tests/scrollable-group-smoke.html`

## Steps

- [x] **3.1 — Unit test (DOM stubs)**
  - Follow `view.test.mjs` / `control-registry.test.mjs`: stub `ResizeObserver`
    and a minimal `document`/`document.createElement` before importing
    `stack-view.js`/`group-view.js`.
  - Assert a scrollable vertical `StackView` reports `minSizePx('y', 0) === 0`
    and `preferredPx('y', 0) === null`, while a non-scrollable one derives from
    content; assert the content element gets `overflow: auto` and the
    `tanga-scroll` class when scrollable.
  - Assert a scrollable `GroupView` still reports a min height along `y` (the
    title-bar contribution) and that scrolling targets its content div, not the
    panel.

- [x] **3.2 — Smoke page**
  - Add `dev/src/js-tests/scrollable-group-smoke.html`: a vertical `SplitView`
    with a fixed-height scrollable `GroupView` holding many control views; verify
    the group shrinks and its content scrolls with a thin dark scrollbar, while a
    non-scrollable sibling still clips.

## Validation

`node --test dev/src/js-tests/scrollable-stack.test.mjs`

## Notes

- Browser smoke is manual (no headless harness in this repo); the `node:test`
  unit is the CI gate.
