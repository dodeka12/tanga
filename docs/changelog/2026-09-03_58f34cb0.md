# Changes since version 1.17.0

## New Features

- **Scene/layout/overlay model** — scenes, layouts, and overlays now flow
  through a single hierarchy (`LayoutHost` → `Layout` → `Scene`);
  `add_scene(name)` auto-creates a same-named single-`SceneView` layout so
  scene URLs come for free.
- **Polymorphic `Visualizer.add`** — `viz.add(entity)` targets the main scene
  and `viz.add(view)` mounts the view in the default layout's overlay;
  `viz.add_layout` and `viz.layout[name]` expose the layout registry.
- **Control-owned value & history** — `Control.set_value`/`get_value` and
  `Table.undo`/`redo`/`can_undo`/`can_redo`/`clear_history` live on the control
  classes (forwarded through `*View`).
- **`SliderView` gains `on_press` / `on_release`** — sliders accept press
  (drag-start) and release (drag-end) handlers in addition to `on_change`.
- **`SliderView` / `ButtonView` / `CheckboxView` gain `variant`** — the view
  classes expose `EControlVariant` (`"default"` / `"menu"`).
- **`ToolbarView` and shared `EStack*` layout enums** — a horizontal toolbar
  container (a bordered `StackView` with an inner `margin`, a `border` toggle,
  and `gap`/`align`/`justify`) aligns a row of controls left, right,
  block-centered, or equally spaced; `EStackDirection` / `EStackAlign` /
  `EStackJustify` replace the `StackView`/`GroupView`/`MenuView` string
  literals (plain strings remain valid).
- **`LabelView` / `MarkdownView` / `LogView` display views** — three read-only
  content views render inside a layout tree: `LabelView` (text with a
  configurable `font_size`), `MarkdownView` (rendered markdown with KaTeX
  math), and `LogView` (a live, auto-scrolling two-column time/message log
  with a history cap and JSON-lines file I/O).  `LabelView` / `MarkdownView`
  are settable in place via `set_value`; `LogView` appends lines
  programmatically via `log()` / `clear()` / `load_file()` and pushes
  `log_update`.
- **`SeparatorView`** — a thin 1px divider line with configurable `spacing`,
  usable in toolbars, menus, and stacks.  `orientation` is the line's
  orientation (`"horizontal"` / `"vertical"`); the default `"auto"` derives the
  perpendicular orientation from the enclosing container.
- **`Table.on_change` bulk-change handler** — `TableView` accepts an
  `on_change` callback that fires once with the full `{columns, rows}` table on
  undo/redo (Ctrl+Z / Ctrl+Shift+Z / Ctrl+Y and `TableView.undo()` / `.redo()`),
  complementing the per-cell `on_cell_change`.
- **`Expression.bind()` / `Expression.evaluate()`** — intent-specific
  evaluation entry points (also on `AffineExpression`) that narrow the wide
  `MV | Expression | list` `__call__` return type: `bind()` asserts a partial
  evaluation (returns `Expression`), `evaluate()` asserts a full collapse
  (returns `MV`), each raising `ValueError` when the caller's stated intent is
  wrong.
- **`Transform.from_operator()` + public `Transform`** — `Transform` is now
  importable from `pytanga.viz` and can be built from a GA operator
  (`Translator`/`Rotor`/`GeneralRotor`/`Motor`/`Dilator`), so a body's static
  placement can be baked into a `VizGroup` at construction time.
- **Smooth SDF CSG** — `smooth_union`/`smooth_intersection`/`smooth_subtract`
  combine modes with a per-member `smoothness` blend radius on
  `Composed`/`SdfGroup`/`Combine` (and a `SdfStyle(smoothness=…)` default) give
  rounded, blended joins instead of hard seams.

## Breaking Changes

- **`add_*` control facades removed** — `add_slider`/`add_button`/`add_table`/…,
  `add_control_group`, and `add_menu` are gone; declare controls as `*View`
  objects and mount them with `set_layout` or `viz.add(view)`.
- **`control_position` removed** — the implicit orphan control panel and its
  per-scene anchors are gone; position controls via `GroupView(position=...)`.
- **Runtime value API removed** — `set_control`/`get_control`/`set_control_value`/
  `undo_table`/`redo_table`/`update_control` are gone; call `set_value`/`undo`/
  `redo` on the control view instead.
- **The legacy `controls_define` orphan-panel path is removed** — controls are
  no longer emitted through a separate fixed-panel (`controls_define`) pipeline
  with its own toggle button; they render as layout views through `view_layout`.

## Bug Fixes

- **Reflected `MV` wedge/inner product** — `constant_mv ^ variable` and
  `constant_mv | variable` (constant on the left) now build the expected
  `Expression` via the existing reflected dunders, instead of raising
  `AttributeError`; `MV.__xor__`/`MV.__or__` return `NotImplemented` for
  non-`MV` operands.

## Refactor

- **Scene/layout/overlay ownership reworked** — scenes moved into `LayoutHost`,
  layouts are first-class `Layout` objects (`base` + `overlay`), and the entity
  API moved into `Scene` (`add_viz`); `Visualizer`/`VizSceneHandle` become
  "pick the right scene" delegates.
- **Banners/dialogs/editor folded into `OverlayContainer`** — `BannerHost`/
  `DialogHost`/`EditorHost` are merged into the per-layout overlay container.
- **Tree-walk dispatch** — inbound control events resolve ids by walking layout
  trees and dialogs (the `_control_views` index is deleted).
- **Control event handling moved onto the controls** — a polymorphic
  `Control.handle_event(event, payload) -> Dispatch` seam means each control
  kind owns its own event → mutation → handler mapping; the visualizer only
  resolves a control and delegates.
- **Explicit `Visualizer` facade** — `__getattr__` is replaced by thin
  forwarders so the public API is introspectable.
