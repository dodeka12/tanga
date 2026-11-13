# Phase 3 — Route `control_state` to the view

**Depends on:** 01, 02 | **Status:** Done

## Problem

`viewer.js` resolved `control_state` targets through `_viewRegistry`, the
layout-reconciliation map.  It only exists for layout builds (a dialog content
subtree is built with `buildViewTree(node, ws)` and no registry), and it mixed
two concerns: reuse planning and runtime state lookup.

## Change

New `py/pytanga/viz/templates/views/view-state.js`

- `registerStatefulView(view)` / `unregisterStatefulView(view)` /
  `unregisterStatefulTree(view)` / `getStatefulView(id)` — one global
  `id → view` map, no imports (so `controls-panel.js` can use it without a
  cycle).
- `applyViewState(view, msg)` routes `visible`, `collapsed`, `enabled`,
  `tooltip`, `title` and `row`+`title` to the view methods that exist, and
  reports whether anything was applied.
- `clearStatefulViews()` test hook.

Wiring

- `build.js:registerView` registers every built view (containers included), so
  dialog subtrees are reachable too.
- `View.destroy` unregisters (guarded: a replaced id is not deleted).
- `DialogView.destroy` calls `unregisterStatefulTree` on its content subtree —
  those child views are not destroyed individually.
- `viewer.js` `_buildLayout` unregisters global overlay (menu) trees before
  destroying them.
- `viewer.js` `control_state` handler collapses to
  `applyControlState(msg.id, msg); applyViewState(getStatefulView(msg.id), msg);`.
- `controls-panel.js:applyControlState` strips `visible` from the widget state
  when a hosting view exists, so the DOM no longer fights the layout (the
  widget-level `display` fallback stays for a widget with no view).

## Checks

- `cd js/dev && node --test tests/view-visibility.test.mjs`
- Playwright smoke: `control_state` from the toolbar hides/shows the group and
  the params row.
