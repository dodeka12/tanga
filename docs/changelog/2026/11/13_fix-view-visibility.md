# Changes since version 2.26.1 (2.27.0-rc3)

## Bug Fixes
- **`visible=False` hides whole panes** — a hidden group, stack, toolbar or
  params view now collapses completely (pane chrome and title included) and
  takes no layout space, instead of only hidden leaves being honoured; the
  state survives a layout re-push and restores the view's own `display` (a
  group keeps its flex shell) when shown again.
- **Hidden Parameters rows hide their title** — a control built with
  `visible=False`, or hidden at runtime, hides its key label too, and the row no
  longer reserves height or a row gap, so the panel shrinks instead of leaving a
  blank line.
- **Group ids work in `set_control_visible`/`set_control_enabled`** — both
  resolve a `GroupView` when the id is not a control, and
  `GroupUI(visible=…, enabled=…)` now reaches a nested dataclass sub-panel.

## Refactor
- **Visibility belongs to the view** — `build.js` funnels every `node.type`
  through one state tail, `View` owns hidden-aware sizing through protected
  `_minSizePx`/`_maxSizePx`/`_preferredPx` hooks (so no subclass can bypass a
  hidden view), and a new `views/view-state.js` registry routes `control_state`
  to any built view, containers and dialog subtrees included.  The
  `all_controls.py` example gained a **Visibility** menu that hides a whole
  group pane, a single control, a Parameters row and the nested sub-panel at
  runtime.
