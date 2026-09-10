# Changes since version 1.7.0

## New Features
- **Four new interactive controls** — single-line text (`add_text_field`),
  multi-line text (`add_text_area`), color picker (`add_color_picker`), and
  checkbox (`add_checkbox`), available on `Visualizer`, `VizSceneHandle`, and
  as control views in layouts.
- **Button icons** — `Button`/`add_button` accept an optional icon (rendered
  before the label) and an `icon_only` mode (a small square button).
- **Icon model** — icons are `family:name` strings (`material:settings`,
  `uc:▶`); `EIconMaterial` and `EIconUC` enums provide autocompletion, and
  Material icons are loaded from the online Google Fonts stylesheet.
- **Tooltips** — every control and the control-group title bar accepts a
  `tooltip` string rendered as a native hover tooltip.
- **Group title-bar icon/tooltip** — `ControlGroup`/`add_control_group`
  accept an icon and tooltip for the title bar.
- **Reusable text editor** — `open_editor()` opens a transient multi-line
  editor overlay in the viewer; `on_close(text, event)` receives the edited
  text (or `None` on discard) and may write it back, e.g. via
  `set_annotation`.
- **`ActPoint` drag-mode constraint** — `ActPoint(..., drag_mode=...)` accepts
  an optional `DragMode` that constrains the unmodified left-button drag to a
  single plane (e.g. `DragMode.XY_PLANE`); when omitted, the unmodified drag
  automatically uses `XY_PLANE` in 2D visualizers and the four standard
  modifier-switched triggers in 3D, preventing Z drift in 2D.
