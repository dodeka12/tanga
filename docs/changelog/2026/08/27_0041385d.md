# Changes since version 1.8.0

## New Features
- **In-place control value updates** — `Visualizer.set_control_value` and
  `Visualizer.set_control_view_value` (plus `VizSceneHandle.set_control_value`)
  update a control's value after creation via a lightweight `control_update`
  message, preserving panel collapse/drag/focus state instead of rebuilding.
- **Value-edit (stepper) control** — `add_value_edit` / `ValueEditView` add a
  numeric stepper with `min`/`max`/`step`/`digits`, up/down buttons,
  arrow-key / scroll-wheel stepping, and optional direct text editing
  (`editable=True`).

## Breaking Changes
- **`default` renamed to `value`** — the control value field is now `value`
  everywhere: the `Slider` / `Dropdown` / `ColorPicker` / `Checkbox`
  dataclasses, the `SliderView` / `DropdownView` / `ColorPickerView` /
  `CheckboxView` layout controls, the `add_slider` / `add_dropdown` /
  `add_color_picker` / `add_checkbox` APIs, and the serialized `"value"` wire
  field.  The old `default=` keyword no longer works.
