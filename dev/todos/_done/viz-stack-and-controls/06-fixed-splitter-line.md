# Phase 6 — Fixed splitter draws a thin line

## Goal

A non-movable splitter should still be visible — a thin line, not transparent.

## Steps

- [x] **6.1 — `templates/views/split-view.js`**
  - In `_syncSplitterBars`, for `sp.movable === false` render a thin divider
    (1px line centered in the reserved gap) instead of `background: transparent`.
    Keep the reserved `SPLITTER_SIZE` layout width unchanged so math stays stable.
  - Keep `cursor: default` and `data-movable="0"`; movable splitters stay as the
    filled bar.

- [x] **6.2 — Smoke / visual**
  - Confirm in `split-view-smoke.html` + the example that fixed vs movable is now
    clearly distinguishable (thin line vs filled bar).

## Validation

`node --input-type=module --check` on `split-view.js` + browser smoke page.
