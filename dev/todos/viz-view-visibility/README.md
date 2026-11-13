# Viz view visibility — Overview

**Created:** 2026-11-13 | **Status:** Done | **Branch:** `fix/view-visibility`

## Goal

Make `visible: false` mean the same thing for **every** view node, and make a
hidden view actually free its layout space:

1. a hidden `GroupView`/`StackView`/`ToolbarView`/`ParamsView` collapses its
   whole pane (title included) instead of being rendered visible;
2. a hidden control also hides its `ParamsView` row — key label included — and
   the row stops reserving height and a row gap;
3. `control_state {visible}` reaches containers and dialog subtrees, not just
   widgets that happened to be built with a layout registry;
4. showing a view again restores its own inline `display` (a group keeps its
   `display:flex` shell), including after a layout re-push;
5. Python symmetry: `set_control_visible` / `set_control_enabled` accept a group
   id, and `GroupUI(visible=…, enabled=…)` reaches a nested sub-panel.

Reported symptom: setting `visible: false` on a group left the row title (and
the whole pane chrome) visible, because containers ignored the flag.

## Root causes

- `views/build.js`: every container branch (`split`, `stack`, `group`,
  `toolbar`, `menu`, `params_view`, `scene_view`, `log_view`) returned straight
  from `registerView`, so only the generic leaf tail consulted `node.visible`.
- `View.setHidden(false)` restored `display: ''`, destroying the inline
  `display:flex` that `StackView._applyFlex` / `GroupView._setupChrome` set.
- Hidden containers sized themselves: `GroupView`/`ToolbarView`/`ParamsView`
  overrode the public `minSizePx`/`preferredPx` **after** the base guard, and
  `stack-size.js` counted hidden children (and their gaps).
- `ParamsView.addRow` never applied the child's initial hidden state, and
  `control_state` was routed through `_viewRegistry`, which only exists for
  layout builds (dialogs build without one).
- Python: `set_control_visible`/`set_control_enabled` only resolved controls,
  and `ParamsView._build_group` dropped `GroupUI.visible`/`enabled`.

## Architecture (short)

- **Visibility belongs to the `View`, never the widget DOM.**  One code path:
  `build.js:applyNodeState` → `views/node-state.js:applyNodeVisibility` →
  `View.setHidden`.
- `View` owns the collapse: public `minSizePx`/`maxSizePx`/`preferredPx` guard
  `_hidden`, subclasses override the protected `_minSizePx`/`_maxSizePx`/
  `_preferredPx` hooks.  `stack-size.js` filters hidden children (size **and**
  gap).
- `views/view-state.js` is the global `id → view` registry used by
  `viewer.js` for `control_state` (`applyViewState`), covering controls,
  containers and dialog subtrees; `View.destroy` unregisters.
- `View.setHidden` emits `visibilitychange`; `ParamsView` uses it to hide a
  whole row and skips hidden rows in its height maths.
- No wire change: a node serializes `visible: false` only when hidden, so
  "absence = visible".

## Decisions (confirmed)

- No new message type and no serialization change; `visible` stays a lazily
  serialized flag.
- Sizing is guarded in the base class via template-method hooks rather than
  repeating `if (this._hidden) return 0` in every subclass.
- A split pane hidden at runtime keeps its splitter slot (zero-size pane) but
  remembers its last visible size, so it does not stay collapsed when shown.
- The DOM `display` fallback in `applyControlStateToElement` is kept only for
  widgets with no hosting view.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-build-funnel.md](./01-build-funnel.md) | One state tail for every `node.type` in `build.js` |
| 2 | [02-view-visibility-authority.md](./02-view-visibility-authority.md) | `View` owns hidden-aware sizing + display round-trip; hidden-aware gap maths |
| 3 | [03-control-state-routing.md](./03-control-state-routing.md) | `views/view-state.js` registry + `applyViewState` in `viewer.js` |
| 4 | [04-params-row-hiding.md](./04-params-row-hiding.md) | Whole-row hiding and hidden-aware height in `ParamsView` |
| 5 | [05-python-symmetry.md](./05-python-symmetry.md) | Group ids in `set_control_visible`/`set_control_enabled`; `GroupUI` visible/enabled |
| 6 | [06-tests-docs-gate.md](./06-tests-docs-gate.md) | Unit tests, Playwright smoke, docs, changelog, full gate |

## Testing as you go

- Node: `cd js/dev && npm test` (`view-visibility`, `params-row-visibility`,
  `stack-size`).
- Python: `uv run pytest py/tests/viz -q`.
- Bundle: `uv run python tools/build-viewer-js.py` then `--check`.
- Browser: `uv run python js/dev/tests/serve-visibility-smoke.py`, then
  `node js/dev/tests/visibility-smoke.mjs <printed-url>`.
- Gate: `uv run ruff check py/ tools/ js/dev/tests`,
  `uv run ruff format --check …`, `uv run mkdocs build --strict`.

## Non-goals

- No change to the `view_layout` wire format or to `view_visibility`
  (per-pane entity visibility), which is unrelated.
- No new Python runtime API for hiding arbitrary stacks/toolbars by id (only
  controls and groups; add when a use case appears).
- No redesign of `SplitView` allocation for hidden panes beyond remembering
  their last visible size.
