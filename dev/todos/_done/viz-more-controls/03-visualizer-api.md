# Phase 3 — Visualizer API + exports

## Goal

Expose the new controls and the new options (tooltip, button icon/icon_only,
group icon/tooltip) through the public `Visualizer` / `VizSceneHandle` API.

## Steps

- [x] **3.1 — `visualizer.py` `add_*` methods**
  - Add `tooltip: str = ""` to `add_slider`, `add_dropdown`, `add_button`,
    `add_file_chooser` and their `_add_scene_*` variants.
  - Add `icon: Icon | None = None`, `icon_only: bool = False` to
    `add_button`/`_add_scene_button`.
  - Add `add_text_field`, `add_text_area`, `add_color_picker`, `add_checkbox`
    (each with `label`, the control's own fields, `on_change`, `tooltip`,
    `parent_id`) + `_add_scene_*` variants, registering `on_change` in
    `_handler_registry` and calling `_push_controls`.

- [x] **3.2 — Group API**
  - Add `icon: Icon | None = None` and `tooltip: str = ""` to
    `add_control_group`/`_add_scene_group`.

- [x] **3.3 — `_scene_handle.py`**
  - Forwarding methods for the four new controls, and the new params on the
    existing `add_slider`/`add_dropdown`/`add_button`/`add_file_chooser`/
    `add_control_group` methods.

- [x] **3.4 — Exports `__init__.py`**
  - Add `TextField`, `TextArea`, `ColorPicker`, `Checkbox`, `EIconMaterial`,
    `EIconUC` to imports and `__all__`.

- [x] **3.5 — Validate**
  - `uv run python -c "from pytanga.viz import TextField, ColorPicker, EIconMaterial"`.

## Validation

`uv run pytest py/tests/viz/test_file_chooser.py -q` (regression) plus the
import smoke check above.

## Notes

- Reuse the existing `add_file_chooser` pattern (dataclass + registry +
  `_push_controls`) for the four new `add_*` methods.
- `parent_id` is stored on the control for symmetry with existing methods, even
  though per-control `parent_id` is not serialized (attachment is group-level).
