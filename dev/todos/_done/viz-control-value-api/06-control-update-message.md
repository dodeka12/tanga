# Phase 6 — `control_update` wire message + in-place frontend update

## Goal

Ship the lightweight update message end-to-end and apply it in the browser
without rebuilding the panel.

## Steps

- [x] **6.1 — Python push**
  - `_push_control_update(scene_name, cid, value)` in `visualizer.py`
    (mirrors `_push_controls`); `server.py::_ws_msg_brief` gains a
    `control_update` case.

- [x] **6.2 — `controls-panel.js` registry**
  - `controlId → { kind, apply(value) }` map; each `create*` factory registers
    an `apply` closure (no `control:change` fired). Clear on `_destroyAll` /
    `handleControlsClear`. Export `applyControlValue(id, value)`.

- [x] **6.3 — `viewer.js` routing**
  - Handle `control_update` at top level (next to `view_camera`), calling
    `applyControlValue(msg.id, msg.value)` — covers panel, attached, and layout
    views since all render through the same factories.

- [x] **6.4 — Validate**
  - Manual viewer smoke: add a slider, set its value from a handler, confirm
    the DOM updates in place (collapse/drag state preserved).

## Validation

Manual browser smoke + `uv run pytest py/tests/viz/test_frontend_version.py -q`.

## Notes

- Id-keyed lookup matches the existing app-wide control-id namespace
  (`ControlHandlerRegistry`); browsers that don't render the control no-op.
