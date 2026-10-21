# Changes since version 2.22.0 (2.23.0-rc1)

## New Features

- **ParamsView can replace hand-built control panels** — nested dataclasses
  render as collapsible sub-groups (`GroupUI`), `RowSpec`/`extra_rows` add
  non-parameter button/status rows above or below the parameters, and per-field
  `on_change` handlers plus `ControlEvent.key`/`value` expose the changed field.
- **Runtime row API** — `set_visible`/`set_enabled`/`set_title`/`set_options`
  act on a whole row (title + control); `set_state`/`add`/`remove` replace or
  mutate rows; `ControlUI` gains `visible`, `coerce`, `validate`, `integer`,
  `unit`, and `on_change`.
- **Type inference + coercion** — `Enum`/`Literal`/`Optional[X]` fields infer
  dropdowns, annotations are resolved (so `from __future__ import annotations`
  works), and values are coerced to the field type (an `int` stays an `int`).
- **Dropdown `(value, label)` options** — options serialize as
  `{"value", "label"}` pairs so a label can differ from its value.
- **Tooltips + theme ergonomics** — `metadata["description"]` and
  `title_from_name=True` fill titles/tooltips; `Visualizer(theme=…)` /
  `VisualizerApp(theme=…)` select the theme before the browser connects; and
  `ParamsView(dense=True)` applies a per-view compact density.

## Breaking Changes

- **Dropdown options serialize as objects** — the `options` wire list now uses
  `{"value", "label"}` entries instead of bare strings.  Bare strings are still
  accepted as input and serialize to `{"value": s, "label": s}`.
