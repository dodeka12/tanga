# Phase 3 — Visualizer + scene handle API rename

## Goal

Rename the `default` keyword on the public `add_*` methods and their
`_add_scene_*` internals, plus the `VizSceneHandle` wrappers.

## Steps

- [x] **3.1 — `visualizer.py`**
  - `add_slider` / `_add_scene_slider`: `default: float | None = None` →
    `value`; forward `value=value if value is not None else min`.
  - `add_dropdown` / `_add_scene_dropdown`, `add_color_picker` /
    `_add_scene_color_picker`, `add_checkbox` / `_add_scene_checkbox`:
    `default` → `value` in signatures and dataclass construction.

- [x] **3.2 — `_scene_handle.py`**
  - Mirror the rename in `add_slider` / `add_dropdown` / `add_color_picker` /
    `add_checkbox`.

- [x] **3.3 — Regression**
  - `uv run pytest py/tests/viz/test_entry_points.py py/tests/viz/test_layout_api.py
    py/tests/viz/test_file_chooser.py -q`.

## Validation

`uv run pytest py/tests/viz/test_entry_points.py py/tests/viz/test_layout_api.py py/tests/viz/test_file_chooser.py -q`

## Notes

- No docstring change beyond the keyword name; `add_text_field` /
  `add_text_area` / `add_file_chooser` already used `value`.
