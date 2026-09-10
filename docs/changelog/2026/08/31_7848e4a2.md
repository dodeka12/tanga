# Changes since version 1.12.0

## New Features
- **Scrollable `StackView`/`GroupView` panes** — a new `scrollable=True` flag lets
  a stack/group pane scroll its overflowing content instead of clipping, with a
  custom thin dark scrollbar that appears only on overflow, so a control group in
  a split pane can be shrunk and still reach every control.

## Breaking Changes
- **Banner `on_close` now receives the value, not the banner id** — banner and
  editor "close" are unified into one `close` event carrying the control's
  `value` (the editor's text, or `None` for the value-less banner). Capture the
  id from `show_banner`'s return value instead.

## Bug Fixes
- **`FileChooserView` shows the selected path** — selecting a file in the modal
  browser now writes the chosen absolute path back to the control (panel **and**
  layout view) and pushes a `control_update`, so the text input updates instead
  of staying empty.
- **`FileChooserView` Browse honours `root=`** — directory navigation now
  resolves the control from a layout view as well as the panel, so listings are
  clamped to the control's `root` (previously layout views browsed unclamped).
- **`controls_define` no longer wipes layout view controls** — the frontend
  control registry is now owner-scoped (`panel`/`attached`/`layout`/`banner`),
  so a panel rebuild no longer drops the `TableView`/`FileChooserView` update
  entries and later `control_update` messages are applied again.
- **Banner button clicks dispatch again** — banner `Button` handlers are
  registered under the `click` event, matching the click dispatch path.

## Refactor
- **Unified control addressing** — `Visualizer` resolves any control (panel or
  layout view) by id via `_resolve_control` and updates it via the new
  `set_control`/`get_control` primitives.
- **Event-keyed handler registry** — `ControlHandlerRegistry` keys handlers by
  `(id, event)` instead of bare id plus magic `__row_add__`/`__press__`/
  `__release__`/`__group__` prefixes.
- **Single dispatch tail** — control, banner, and editor events route through one
  `_dispatch_event` helper; the ad-hoc `_banner_close_handlers` /
  `_editor_close_handlers` dicts are folded into the registry under
  `(id, "close")`.
- **Single control model** — every `ControlView` now wraps a
  `pytanga.viz._controls.Control` (exposed as `view.control`) and serializes its
  fields from it, removing the duplicated `set_control_view_value` /
  `get_control_view_value` helpers and the parallel `Control`/`ControlView`
  field definitions.
- **Interactions share the registry** — `on_interaction` registers handlers in
  the same `(id, event)` registry as controls; `InteractionHandlerRegistry`
  delegates handler storage to it while keeping drag-move coalescing and camera
  caching.
- **Unified event envelope** — control/banner/editor/file-browser actions go
  through one `sendEvent(target, event, data)` helper (`{type:"event", target,
  event, data}`); the server routes it by `event` name. Banner/editor close are
  collapsed into a single `close` event. (Interactive objects still send
  `interaction:*` directly — recorded as a follow-up in the architecture doc.)
- **Architecture documented** — `docs/dev/architecture/viz-controls-and-interactions.md`
  records the contract, and `.clinerules` points new frontend elements at it.
