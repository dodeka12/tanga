# Phase 5 — Value API onto controls; delete `add_*`/orphan/`_control_views`

## Goal

Move runtime value/history operations onto the control classes themselves, and
delete the `ControlHost` value API + the control `add_*` facades + the orphan
panel + the `_control_views` index.  Inbound dispatch resolves by walking the
layout tree.  (API-breaking: `viz.add_slider(...)` etc. are removed.)

## Files

- Edit: `py/pytanga/viz/_controls.py` (`Table.undo`/`redo`/`can_undo`/`can_redo`/`clear_history`, `set_value`)
- Edit: `py/pytanga/viz/views.py` (`*View` re-expose value/history)
- Edit: `py/pytanga/viz/_hosts.py` (`ControlHost` loses add_*/value API/index)
- Edit: `py/pytanga/viz/visualizer.py` + `_scene_handle.py` + examples/tests

## Steps

- [x] **5.1 — Control value/history ops**
  - Add `set_value` to sliders/dropdowns/… and `undo`/`redo`/`can_undo`/`can_redo`/
    `clear_history` to `Table`; `*View` forward them.
- [x] **5.2 — Delete facades + index**
  - Remove `add_*`, `add_control_group`, `add_menu`, `_add_scene_control`,
    `_KIND_VIEWS`, orphan-group machinery, `control_position`, and `_control_views`.
- [x] **5.3 — Tree-walk dispatch**
  - `ControlHost.dispatch` resolves the control id by walking `layout` trees/dialogs.
- [x] **5.4 — Update examples/tests**
  - Replace `viz.add_slider(...)` with `viz.add(GroupView([SliderView(...)]))`, etc.

## Validation

`uv run pytest py/tests/viz -q`

## Notes

- This is the biggest API break; do it last among the API phases.
