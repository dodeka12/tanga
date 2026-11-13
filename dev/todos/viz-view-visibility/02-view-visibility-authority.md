# Phase 2 — `View` is the visibility/size authority

**Depends on:** 01 | **Status:** Done

## Problems

1. Hidden containers still reported a size: `GroupView`, `ToolbarView` and
   `ParamsView` overrode the **public** `minSizePx`/`preferredPx`/
   `maxSizePx`, so the base `_hidden` guard was bypassed; `stack-size.js` also
   summed hidden children and counted their gaps.
2. `View.setHidden(false)` restored `display: ''`, wiping the inline
   `display:flex` that `StackView._applyFlex` and `GroupView._setupChrome` set —
   a group came back as a plain block (lost gap/direction).

## Change

`views/view.js`

- Public `minSizePx` / `maxSizePx` / `preferredPx` now only guard `_hidden` and
  delegate to protected hooks `_minSizePx` / `_maxSizePx` / `_preferredPx`
  (default implementation = the explicit `Size` constraints).
- `setHidden` remembers the view's own inline `display` before hiding and
  restores it verbatim on show (`_applyHiddenCss`), and emits a new
  `visibilitychange { hidden }` event (documented in the class header).

Subclasses renamed their overrides to the protected hooks (and dropped their own
`_hidden` checks): `control-view.js`, `stack-view.js`, `toolbar-view.js`,
`group-view.js`, `params-view.js`, `split-view.js`.

`views/stack-size.js`

- `stackMinSize` / `stackPreferredSize` filter hidden children through a new
  `visibleChildren()` helper: no size **and** no gap for a hidden child.

`views/split-view.js`

- `_relayout` no longer stashes the resolved `0` size of a hidden pane, so
  showing it again does not leave it collapsed.

## Checks

- `cd js/dev && node --test tests/view-visibility.test.mjs`
- `uv run pytest py/tests/viz -q`
- Playwright smoke: "Show group" restores `display:flex` with non-zero height.
