# Phase 4 — Thread `on_change` through the table API

## Goal

Expose `on_change` on every table entry point. Registration is already generic:
`_register_control_view_handlers` maps a view's `on_change` → `"change"`, and
`ControlView.__getattr__` delegates `view.on_change` to `self.control.on_change`,
so no registry change is needed — only the constructors/facades.

## Files

- Edit: `py/pytanga/viz/views.py` (`TableView.__init__`, `control_to_view`)
- Edit: `py/pytanga/viz/visualizer.py` (`add_table`, `_add_scene_table`)
- Edit: `py/pytanga/viz/_scene_handle.py` (`VizSceneHandle.add_table`)
- Edit: `py/tests/viz/test_views.py`, `py/tests/viz/test_control_value_api.py`,
  `py/tests/viz/test_file_chooser.py`

## Steps

- [x] **4.1 — `TableView` accepts `on_change`**
  - Add `on_change: Handler | None = None` to `TableView.__init__` and pass it
    into `Table(...)`.

- [x] **4.2 — `add_table` / `_add_scene_table` accept `on_change`**
  - Add `on_change: Any = None` to both, forwarded to `TableView(...)`.

- [x] **4.3 — `VizSceneHandle.add_table`**
  - Add `on_change: Any = None`, forwarded to `self._viz._add_scene_table(...)`.

- [x] **4.4 — `control_to_view`**
  - In the `Table` branch, forward `on_change=ctrl.on_change`.

- [x] **4.5 — Tests**
  - `TableView(..., on_change=...)` exposes `view.on_change` and
    `_register_control_view_handlers` registers `(cid, "change")`.
  - `add_table(..., on_change=...)` registers `(cid, "change")`.
  - Serialization ignores the handler (only control fields are serialized).

## Validation

`uv run pytest py/tests/viz/test_views.py py/tests/viz/test_control_value_api.py py/tests/viz/test_file_chooser.py -q`

## Notes

- Do not add a second `on_change` branch to `_register_control_view_handlers` —
  the existing one (lines ~401–402) already covers tables via attribute
  delegation.
