# Phase 2 — Control-view handler registration

## Goal

When a layout containing control views is registered (`set_layout` /
`show(layout=...)`), register each control's `on_change`/`on_click` into the
existing `ControlHandlerRegistry` so the frontend's `control:*` events reach the
right Python handler.

## Steps

- [x] **2.1 — Tree walk helper**
  - Add `iter_control_views(root) -> Iterator[ControlView]` to `views.py`
    (DFS over `SplitView.children`, `StackView.children`, `GroupView.children`,
    and `SceneView.overlay`), yielding every `ControlView`.

- [x] **2.2 — Registration hook**
  - In `Visualizer.set_layout(...)`, after serializing, walk
    `iter_control_views(layout)` and `self._handler_registry.register(cid, handler)`
    for each control view with a handler (slider/dropdown `on_change`, button
    `on_click`). Re-registering on overwrite should replace cleanly (registry is
    a dict).
  - Ensure `show(layout=...)` (which delegates to `set_layout`) inherits this.

- [x] **2.3 — Event flow (no change to dispatch)**
  - Confirm `_dispatch_control_event` already routes by `control_id` and the
    control views serialize their `id` as the event key (from Phase 1.3).

- [x] **2.4 — Tests (`test_layout_api.py` or new)**
  - `set_layout` with a `SliderView(..., on_change=handler)` → handler reachable
    via `viz._handler_registry.get("cid")`.
  - `set_layout` with a plain `View`/`StackView` → no registrations.
  - Overwrite a layout → old handler replaced / removed.

## Validation

`uv run pytest py/tests/viz/test_layout_api.py py/tests/viz/test_views.py -q`
