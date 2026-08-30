# Phase 3 — Controls Reference (`control-views.md`)

## Goal

Author `docs/py/viz/interaction/control-views.md` — the missing reference page
that documents every declarative `xxxView` layout/control class in
`py/pytanga/viz/views.py` and its relationship to the panel `add_*` controls.

## Files

- New: `docs/py/viz/interaction/control-views.md`
- Edit: `docs/py/viz/interaction/index.md` (link it), `mkdocs.yml` (already
  listed in the target nav), `docs/py/viz/app/layouts.md` (cross-link)

## Steps

- [ ] **3.1 — Write the "two control surfaces" mapping table**
  - Explain the difference between panel controls (`viz.add_*`) and view
    controls (`xxxView` inside a layout), then a table mapping each panel API to
    its view class: `add_slider`↔`SliderView`, `add_dropdown`↔`DropdownView`,
    `add_button`↔`ButtonView`, `add_file_chooser`↔`FileChooserView`,
    `add_text_field`↔`TextFieldView`, `add_text_area`↔`TextAreaView`,
    `add_color_picker`↔`ColorPickerView`, `add_checkbox`↔`CheckboxView`,
    `add_value_edit`↔`ValueEditView`, `add_table`↔`TableView`,
    `add_control_group`↔`GroupView`.
  - Note both share the same async handler contract `(value, event)`.

- [ ] **3.2 — Document the layout containers**
  - `View` (base; per-axis `preferred_*`/`min_*`/`max_*` sizes via `SizeSpec`),
    `SceneView` (`scene`, `id`, `camera`, `overlay`), `SpacerView`,
    `SplitView` (`orientation`, `children`, `movable`, `sizes`),
    `StackView` (`direction`, `children`), `GroupView` (`title`, `position`,
    `collapsed`, `direction`).
  - Cross-link `../visualizer/split-views.md` and `../app/layouts.md`.

- [ ] **3.3 — Document the control views**
  - `ControlView` (base; `cid`, `label`, `tooltip`), then one subsection per
    class with constructor signature + key params + `_node_type`:
    `SliderView`, `ButtonView` (no value; `icon`, `icon_only`, `on_click`),
    `DropdownView`, `FileChooserView`, `TextFieldView`, `TextAreaView`,
    `ColorPickerView`, `CheckboxView`, `ValueEditView`, `TableView`.
  - Copy the exact parameter names/defaults from `views.py` (do not invent).

- [ ] **3.4 — Document runtime helpers**
  - `set_control_view_value(view, value)`, `get_control_view_value(view)`,
    `iter_control_views(root)`, `serialize_layout(root, name)`.
  - Note `ButtonView` carries no value (both helpers raise `TypeError`).

- [ ] **3.5 — Add a minimal example**
  - A `SplitView` + `GroupView` sidebar with a `SliderView` and `ButtonView`,
    cross-linking `py/examples/viz/interaction/all_controls.py`.

- [ ] **3.6 — Wire it into the nav and index**
  - Confirm `mkdocs.yml` lists `Control Views (xxxView)` under
    `Interaction & Controls` (from Phase 2's target nav).
  - Link it from `interaction/index.md` and from `app/layouts.md`'s
    "Two kinds of controls" table.

## Validation

```powershell
uv run mkdocs build --strict
```

## Notes

- `views.py` exports 17 classes; `__init__.py` re-exports all of them (including
  `TextFieldView`, `TextAreaView`, `ColorPickerView`, `CheckboxView`, which are
  missing from `views.py`'s own `__all__` — a separate cleanup, out of scope).
- Verify parameter lists against `py/pytanga/viz/views.py` as the source of
  truth.
