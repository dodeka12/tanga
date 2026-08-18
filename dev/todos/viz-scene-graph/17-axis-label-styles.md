# Phase 17 — Split axis label styling (name label vs value labels)

**Status:** Planned

## Goal

Separate the `Axis` name label from its numeric value labels, both in content
and in style, and give each a canonical default style.

Today `Axis` mixes content/geometry with rendering parameters, and a single
`AxisStyle.label_style` styles only the numeric value labels. The axis *name*
label (`Axis.label`, e.g. `"X"`) has no style of its own — it is hard-coded in
`axis.js` (bold, anchored at the axis end).

After this phase:

- `AxisStyle.label_style` styles the **axis name label** (`Axis.label`),
  consistent with the entity-level `label` + `label_style` pair used everywhere
  else (`viz.add(Point(...), label=..., label_style=...)`).
- `AxisStyle.value_style` (new) styles the **numeric value labels**.
- Both get canonical defaults in `_DEFAULT_STYLE_FOR_KIND["Axis"]`; the name
  label defaults to the axis midpoint, hanging below it.

## Current state (why this change)

### `Axis` (`py/pytanga/viz/_scene_objects.py`)

| Field | Role | Problem |
|---|---|---|
| `start`, `end` | geometry | fine |
| `major_interval`, `minor_interval`, `show_ticks` | ticks | fine |
| `value_start`, `value_step` | numeric scale | fine |
| `label` | axis **name** label text | name is conflated with value labels |
| `label_format` | value-label format spec | "label" is ambiguous |
| `label_at_major` | show value labels? | duplicated in `AxisStyle` |
| `label_size` | value-label font size | a style param living on content |

### `AxisStyle` (`py/pytanga/viz/_styles/_entity_styles.py`)

`color`, `opacity`, `line_thickness`, `label_at_major` (dup), `label_style`
(styles **value** labels only).

### Wire format (`serializer.py`) and frontend (`axis.js`)

- `_serialize_axis` emits `labelAtMajor`, `labelFormat`, `labelSize`, `label`,
  and the resolved `style` (with `style.label_style`).
- `_axis_entry` (Axes2D/3D group path) hard-codes `labelFormat: ".1f"` and
  reads `label_at_major` from the style.
- `axis.js` reads `style.label_style` for value labels and hard-codes the name
  label (bold, at `end`).

## Target design

### `Axis` — geometry + data only

| Current | Proposed | Notes |
|---|---|---|
| `start`, `end` | unchanged | geometry |
| `major_interval`, `minor_interval`, `show_ticks` | unchanged | |
| `value_start`, `value_step` | unchanged | numeric scale |
| `label` | **unchanged** | axis name label ("X") |
| `label_format` | **`value_format`** | format spec for value labels |
| `label_at_major` | **`show_value_labels`** | single source of truth |
| `label_size` | **removed** | → `AxisStyle.value_style.font_size` |

`Axes2D` / `Axes3D` gain the same two passthrough params
(`show_value_labels: bool = True`, `value_format: str = ".1f"`) so group axes
expose identical controls and `_axis_entry` stops hard-coding `.1f`.

### `AxisStyle` — line style + two label styles

| Current | Proposed | Notes |
|---|---|---|
| `color`, `opacity`, `line_thickness` | unchanged | line |
| `label_at_major` | **removed** | → `Axis.show_value_labels` |
| `label_style` (today: value labels) | **`label_style`** — reassigned to the **name label** | matches `Axis.label` |
| — | **`value_style`** (new) | `LabelStyle` for value labels |

Both are plain `LabelStyle` instances (no new class).

### Canonical default (`_DEFAULT_STYLE_FOR_KIND["Axis"]`)

```python
"Axis": AxisStyle(
    color="#888888",
    opacity=1.0,
    line_thickness=2.0,
    # Axis name label: centered along the axis, hanging below it.
    label_style=LabelStyle(along=0.5, align=(0.5, 0.0), offset_2d=(0.0, 10.0)),
    # Numeric value labels: 12 px, centered on the tick, color inherited.
    value_style=LabelStyle(font_size=12, align=(0.5, 0.5)),
),
```

- `value_style.color` stays `None` → value labels inherit the axis line color.
- No default perpendicular offset (value labels stay centered on the axis).
- Name label stays **bold** via the existing `bold: true` flag in `axis.js`
  (not via a `font_weight` default).

The non-`None` overlay in `_merge_style` means a sparse `AxisStyle(color=...)`
still inherits both label-style defaults, through `_apply_defaults`
(standalone `Axis`) and `_resolve_group_axis_styles` (`Axes2D`/`Axes3D`).

### Wire format

| Current | Proposed |
|---|---|
| `"label"` | unchanged (axis name) |
| `"labelAtMajor"` | `"showValueLabels"` |
| `"labelFormat"` | `"valueFormat"` |
| `"labelSize"` | *(removed)* |
| `style.label_style` | now = **name label** style |
| — | `style.value_style` = value labels |

## Changes

### 1. Scene objects — `py/pytanga/viz/_scene_objects.py`

- `Axis`: rename `label_format` → `value_format`, `label_at_major` →
  `show_value_labels`; delete `label_size`; keep `label`; update the docstring.
- `Axes2D` / `Axes3D`: add `show_value_labels: bool = True` and
  `value_format: str = ".1f"`; thread them through `expand()` / `_expand_dir()`
  into each `Axis`.

### 2. Styles — `py/pytanga/viz/_styles/_entity_styles.py`

- `AxisStyle`: delete `label_at_major`; keep `label_style` (now documented as
  the **name label** style); add `value_style: LabelStyle | None = None`.
- Update `to_dict()` to emit `label_style` and `value_style`.

### 3. Styles registry — `py/pytanga/viz/_styles/__init__.py`

- Update `_DEFAULT_STYLE_FOR_KIND["Axis"]` to the block in *Target design*.

### 4. Serializer — `py/pytanga/viz/serializer.py`

- `_serialize_axis`: emit `showValueLabels` (from `ent.show_value_labels`),
  `valueFormat` (from `ent.value_format`); drop the `labelSize` emission.
- `_build_axes_entries` / `_axis_entry`: take `show_value_labels` and
  `value_format` from the group (passed from `_serialize_axes2d` /
  `_serialize_axes3d`) instead of `style.get("label_at_major", True)` and the
  hard-coded `".1f"`.

### 5. Visualizer — `py/pytanga/viz/visualizer.py`

- No code change expected: the default axes use color-only `AxisStyle`s
  (`_add_default_scene_objects`), and the new label-style defaults flow from
  the canonical `"Axis"` style. Verify only.

### 6. Frontend — `py/pytanga/viz/templates/renderers/axis.js`

- Value labels: read `style.value_style` instead of `style.label_style`;
  read `axis.valueFormat` and `axis.showValueLabels` (fallback `true`).
- Name label: read `style.label_style`; anchor at
  `start + dir · length · (along ?? 0.5)`; apply `align` (default `(0.5, 0)`),
  `offset_2d` (default `(0, 10)`), `rotation`, `font_size`, `color`; keep
  `bold: true`. Replace the hard-coded `label.position.copy(end)`.

### 7. Examples — `py/examples/viz/`

- `demo_axes_custom.py`: `AxisStyle(label_style=LabelStyle(rotation=-90))`
  → `AxisStyle(value_style=LabelStyle(rotation=-90))` (it rotates value
  labels).
- Grep for `AxisStyle(label_style=`, `label_size=`, `label_format=`,
  `label_at_major=` and update any other demos (`demo_camera_axes_grid_2d.py`,
  `demo_camera_axes_grid.py`, …). `demo_labels.py` is unaffected (entity-level
  `label_style` on `Point`).

### 8. Tests — `py/tests/viz/`

- `test_scene_session.py`: update `test_axes_label_style_flows_into_entries`
  and `test_axes_label_style_rotation_flows_into_entries` to use `value_style`
  and assert `style.value_style` (rename the methods to `..._value_style_...`).
- Add tests: name-label default flows (`style.label_style` carries
  `along=0.5`, `align=[0.5, 0]`, `offset_2d=[0, 10]`) for a standalone `Axis`
  and a group axis; `value_style` default flows (`font_size=12`,
  `align=[0.5, 0.5]`).
- `test_node_serialization.py`: `Axis(..., label="X")` / `Axes2D(labels=...)`
  are unaffected (no `label_style`/`label_size`); verify.
- `test_export_static.py`: unaffected (entity label, not axis).

### 9. Docs — `docs/py/viz/`

- `axes-grid.md`: update the `Axis` parameter table and the `AxisStyle` text
  (two label styles, name-label default position).
- `styles.md`: update the `AxisStyle` row to `color`, `opacity`,
  `line_thickness`, `label_style`, `value_style`.

### 10. Changelog — edit existing entry (do **not** create a new file)

The branch has not been released, so the changes are folded into the current
latest changelog `docs/changelog/2026-08-17_13b30f7.md` rather than a new file
(`docs/changelog/index.md` already points at this entry and needs no change):

- **Breaking Changes** bullet: `AxisStyle.label_style` now styles the axis
  *name* label (was: value labels); `Axis.label_at_major` →
  `Axis.show_value_labels`; `Axis.label_format` → `Axis.value_format`;
  `Axis.label_size` removed (use `value_style.font_size`).
- **New Features** bullet: `AxisStyle.value_style` styles the numeric value
  labels; the axis name label is now styleable via `label_style` and defaults
  to the axis midpoint, hanging below it (`along=0.5`, `align=(0.5, 0)`,
  `offset_2d=(0, 10)`).

## Verification

- `uv run ruff check py/pytanga/viz py/tests/viz py/examples/viz`
- `uv run ruff format --check py/pytanga/viz py/tests/viz py/examples/viz`
- `uv run pytest py/tests/viz -q`
- `node --check py/pytanga/viz/templates/renderers/axis.js`
- Smoke (headless): serialize a standalone `Axis` and an `Axes2D` and confirm
  the resolved `style` carries `label_style` (along/align/offset_2d) and
  `value_style` (font_size/align); export an HTML and confirm the name label
  transform includes the midpoint anchor + offset and the value-label path
  reads `value_style`.
