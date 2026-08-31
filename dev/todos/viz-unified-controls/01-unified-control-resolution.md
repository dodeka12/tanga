# Phase 1 — Unified control resolution + value APIs

## Goal

Give `Visualizer` a single primitive to address any control — panel (any scene),
attached, or layout view — by id, and a universal value setter/getter that
pushes `control_update`. Re-implement the file-browser handlers on top of it.

## Files

- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/tests/viz/test_file_chooser.py`

## Steps

- [x] **1.1 — `_resolve_control(cid)`**
  - Returns a small `ControlRef(placement, control, scene)` (or `None`), where
    `placement ∈ {"panel", "view"}`.
  - Panel: iterate `self._scenes` → `scene._controls`; capture the scene name.
  - View: walk `self._layouts` via `iter_control_views`; match `view.id == cid`.
  - Supersedes `_find_control` / `_find_control_view` (update the two
    file-browser callers; keep thin wrappers only if needed).

- [x] **1.2 — Universal `set_control(id, value)` / `get_control(id)`**
  - Resolve via `_resolve_control`.
  - Panel → `_controls.set_control_value` + `_push_control_update(scene, id, …)`;
    view → `views.set_control_view_value` + `_push_control_update("", id, …)`.
  - `get_control` mirrors with `get_control_value`/`get_control_view_value`.
  - Keep `set_control_value`/`set_control_view_value` public names as thin
    backward-compat wrappers around the new primitives.

- [x] **1.3 — File-browser handlers on the new primitive**
  - `_handle_file_browser_select`: `set_control(cid, path)` for panel **and**
    view (fixes select write-back + push).
  - `_handle_file_browser_navigate`: resolve `root` from `_resolve_control`
    (panel or view; fixes `root=` clamping).

- [ ] **1.4 — Tests**
  - Panel select pushes `control_update`; layout `FileChooserView` select sets
    value + pushes; named-scene panel pushes the correct scene; layout
    `FileChooserView(root=…)` navigate clamps.

## Validation

`uv run pytest py/tests/viz/test_file_chooser.py py/tests/viz/test_layout_api.py -q`

## Notes

- Absorbs `dev/todos/viz-file-chooser-path-fix.md` (superseded).
- `_push_control_update` no-ops without `_server`/`_loop`, so no-server tests stay safe.
