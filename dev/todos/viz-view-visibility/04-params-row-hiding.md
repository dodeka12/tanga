# Phase 4 — Whole-row hiding in `ParamsView`

**Depends on:** 02, 03 | **Status:** Done

## Problems

- `addRow` subscribed to `constraintschange`/`preferredchange` but never synced
  the child's **current** state, so a control built with `visible: false` (the
  `applyNodeState` path runs before `addRow`) kept its key label visible.
- `_measureHeight` summed every row and reserved `rowGap` for hidden rows too.

## Change

`py/pytanga/viz/templates/views/params-view.js`

- `addRow` subscribes to the new `visibilitychange` event and calls
  `_syncRowVisibility(key)` immediately, so the initial state is honoured.
- `removeChild` unsubscribes `visibilitychange`.
- `_measureHeight` skips hidden rows and counts the row gap only between the
  rows it actually measured.

## Checks

- `cd js/dev && node --test tests/params-row-visibility.test.mjs`
- Playwright smoke: the `Alpha` row (built with `SliderUI(visible=False)`) is
  `display:none` including its `.tanga-params-key`; "Hide row" hides `Beta` and
  the measured content height shrinks; "Show row" brings `Alpha` back.
