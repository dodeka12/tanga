# Phase 1 — One state tail for every node type

**Depends on:** nothing | **Status:** Done

## Problem

`buildViewTree` had a per-type branch for every container, and each one returned
`registerView(...)` directly.  The generic leaf tail was the only place that
consulted `node.visible`, so `GroupView(visible=False)` (serialized as
`"visible": false`) was silently dropped.

## Change

`py/pytanga/viz/templates/views/build.js`

- New `applyNodeVisibility(view, node)` in
  `py/pytanga/viz/templates/views/node-state.js` — a dependency-free module so
  the unit tests can import it without pulling in Three.js:
  `view.setHidden(node.visible === false)`.
  Absence means visible, which also *shows* a reused view an earlier push hid.
- New `applyNodeState(registry, view, node)` — applies `hide_label`, the size
  specs and the visibility, then registers the view.
- Every `node.type` branch (`split`, `stack`, `group`, `toolbar`, `menu`,
  `params_view`, `scene_view`, `log_view`, and the leaf chain) now ends in
  `return applyNodeState(registry, view, node);`.

Side effect (intended): size specs are applied *after* the children are
attached, so a container is not measured with stale child sizes.

## Checks

- `cd js/dev && node tests/check-syntax.mjs`
- `uv run python tools/build-viewer-js.py --check`
- The Playwright smoke asserts the group is `display:none` with zero height on
  first paint.
