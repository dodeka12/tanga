# Controls

Controls are created on the `Visualizer` instance (`self.viz`) and appear as an
overlaid control panel in the browser. Each control takes a unique id and an
**async** handler callback.

For the handler contract and the `VisualizerApp` lifecycle, see
[Handlers & Lifecycle](../app/handlers.md).

## `add_slider`

```python
self.viz.add_slider(
    "sphere_b_x",
    label="X Position",
    min=-3.5,
    max=3.5,
    step=0.02,
    value=2.5,
    on_change=self.on_slider,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cid` | `str` | *(required)* | Control ID (unique string) |
| `label` | `str` | `""` | Label text displayed above the slider |
| `min` | `float` | `0.0` | Minimum value |
| `max` | `float` | `1.0` | Maximum value |
| `step` | `float` | `0.01` | Step increment |
| `value` | `float` | `min` | Initial value |
| `on_change` | `Callable` | `None` | Async callback: `(value: float, event: ControlEvent) -> None` |

## `add_dropdown`

```python
self.viz.add_dropdown(
    "mode",
    label="Display",
    options=["Both", "Sphere A only", "Sphere B only"],
    value="Both",
    on_change=self.on_mode,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cid` | `str` | *(required)* | Control ID |
| `label` | `str` | `""` | Label text |
| `options` | `list[str]` | `[]` | Dropdown choices |
| `value` | `str` | `""` | Initial selection |
| `on_change` | `Callable` | `None` | Async callback: `(value: str, event: ControlEvent) -> None` |

## `add_button`

```python
self.viz.add_button(
    "reset",
    label="Reset",
    icon=EIconMaterial.REFRESH,
    on_click=self.on_reset,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cid` | `str` | *(required)* | Control ID |
| `label` | `str` | `""` | Button text |
| `icon` | `Icon` | `None` | Optional icon (see [Icons](#icons)) |
| `icon_only` | `bool` | `False` | Render only the icon as a small square button |
| `tooltip` | `str` | `""` | Hover tooltip |
| `on_click` | `Callable` | `None` | Async callback: `(value: None, event: ControlEvent) -> None` |

## `add_text_field`

Single-line text input:

```python
self.viz.add_text_field(
    "name",
    label="Name",
    placeholder="Enter a name…",
    on_change=self.on_name,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cid` | `str` | *(required)* | Control ID |
| `label` | `str` | `""` | Label text |
| `value` | `str` | `""` | Initial value |
| `placeholder` | `str` | `""` | Placeholder text |
| `tooltip` | `str` | `""` | Hover tooltip |
| `on_change` | `Callable` | `None` | Async callback: `(value: str, event: ControlEvent) -> None` |

## `add_text_area`

Multi-line text input:

```python
self.viz.add_text_area(
    "notes",
    label="Notes",
    rows=6,
    on_change=self.on_notes,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cid` | `str` | *(required)* | Control ID |
| `label` | `str` | `""` | Label text |
| `value` | `str` | `""` | Initial value |
| `placeholder` | `str` | `""` | Placeholder text |
| `rows` | `int` | `4` | Visible rows |
| `tooltip` | `str` | `""` | Hover tooltip |
| `on_change` | `Callable` | `None` | Async callback: `(value: str, event: ControlEvent) -> None` |

## `add_color_picker`

Native color input (hex value):

```python
self.viz.add_color_picker(
    "color",
    label="Color",
    value="#ff0000",
    on_change=self.on_color,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cid` | `str` | *(required)* | Control ID |
| `label` | `str` | `""` | Label text |
| `value` | `str` | `"#ffffff"` | Initial hex color |
| `tooltip` | `str` | `""` | Hover tooltip |
| `on_change` | `Callable` | `None` | Async callback: `(value: str, event: ControlEvent) -> None` |

## `add_checkbox`

Boolean checkbox:

```python
self.viz.add_checkbox(
    "wireframe",
    label="Wireframe",
    value=False,
    on_change=self.on_wireframe,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cid` | `str` | *(required)* | Control ID |
| `label` | `str` | `""` | Label text |
| `value` | `bool` | `False` | Initial checked state |
| `tooltip` | `str` | `""` | Hover tooltip |
| `on_change` | `Callable` | `None` | Async callback: `(value: bool, event: ControlEvent) -> None` |

## `add_value_edit`

A numeric stepper with up/down buttons; arrow keys (while the pointer hovers
over the control) and the scroll wheel also step the value.  By default the
value can also be typed directly (`editable=True`); set `editable=False` to
restrict input to the buttons, keys, and wheel:

```python
self.viz.add_value_edit(
    "zoom",
    label="Zoom",
    min=0.5,
    max=4.0,
    step=0.25,
    digits=2,
    value=1.0,
    on_change=self.on_zoom,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cid` | `str` | *(required)* | Control ID |
| `label` | `str` | `""` | Label text |
| `min` | `float` | `0.0` | Minimum value |
| `max` | `float` | `1.0` | Maximum value |
| `step` | `float` | `0.1` | Increment/decrement step |
| `digits` | `int` | `2` | Decimal places shown |
| `value` | `float` | `min` | Initial value |
| `editable` | `bool` | `True` | Allow direct text editing of the value |
| `tooltip` | `str` | `""` | Hover tooltip |
| `on_change` | `Callable` | `None` | Async callback: `(value: float, event: ControlEvent) -> None` |

## `add_table`

An editable tabular-data grid (rendered with Tabulator). The backend defines
the columns and initial rows; the user can edit any cell and, when enabled,
append rows and columns. **Double-click** a cell to edit it (a single click or
drag selects cells instead). Each change is reported back to a distinct handler:

```python
self.viz.add_table(
    "data",
    label="Data",
    columns=["x", "y", "z"],
    rows=[["1", "2", "3"], ["4", "5", "6"]],
    allow_add_rows=True,
    allow_add_columns=True,
    on_cell_change=self.on_cell_change,
    on_row_add=self.on_row_add,
    on_column_add=self.on_column_add,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cid` | `str` | *(required)* | Control ID |
| `label` | `str` | `""` | Label text |
| `columns` | `list[str]` | `[]` | Column headers (length = column count) |
| `rows` | `list[list[str]]` | `[]` | Row-major initial cell data (strings) |
| `allow_add_rows` | `bool` | `True` | Show the "+ Row" button |
| `allow_add_columns` | `bool` | `True` | Show the "+ Column" button |
| `allow_delete_rows` | `bool` | `True` | Show the "− Selected" row-delete button |
| `max_history` | `int` | `100` | Number of undo steps kept (one per committed edit) |
| `tooltip` | `str` | `""` | Hover tooltip |
| `on_cell_change` | `Callable` | `None` | Async callback: `(change: TableCellChange, event) -> None` |
| `on_row_add` | `Callable` | `None` | Async callback: `(add: TableRowAdd, event) -> None` |
| `on_column_add` | `Callable` | `None` | Async callback: `(add: TableColumnAdd, event) -> None` |
| `on_row_delete` | `Callable` | `None` | Async callback: `(delete: TableRowsDelete, event) -> None` |

The handler payloads are `TableCellChange(row, col, value)`,
`TableRowAdd(row, values)`, and `TableColumnAdd(col, header, values)` (all
zero-based). Cell values are strings on the wire — coerce in the handler as
needed. Refresh the grid from the backend with
`self.viz.set_control_value("data", {"columns": [...], "rows": [...]})`.

### Undo and redo

The grid keeps a backend-side undo history (one snapshot per *committed* edit —
entering a cell and pressing Enter/Tab, adding a row/column, or deleting rows;
not per keystroke). In the browser, **Ctrl+Z** undoes and **Ctrl+Shift+Z** (or
**Ctrl+Y**) redoes. The same operations are available programmatically:

```python
self.viz.undo_table("data")          # -> bool
self.viz.redo_table("data")          # -> bool
self.viz.clear_table_history("data")
self.viz.can_undo_table("data")      # -> bool
```

`max_history` bounds the number of retained undo steps (default 100). A
programmatic `set_control_value` full-replace clears the history.

## `add_control_group`

Groups controls into a titled, collapsible
[`GroupView`](control-views.md#groupview) anchored as an overlay (optionally
attached to a 3D object):

```python
self.viz.add_control_group(
    "viewport_controls",
    title="Controls",
    controls=["sphere_b_x", "mode", "reset"],
    position="bottom-right",
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `gid` | `str` | *(required)* | Group ID |
| `title` | `str` | `""` | Group header (empty = no header) |
| `icon` | `Icon` | `None` | Optional title-bar icon (see [Icons](#icons)) |
| `tooltip` | `str` | `""` | Hover tooltip for the title bar |
| `controls` | `list[str]` | `[]` | Ordered list of control IDs |
| `position` | `EAnchor` | `"bottom-right"` | Corner anchors (`top-left`/`top-right`/`bottom-left`/`bottom-right`) or centered edge anchors (`top`/`bottom`/`left`/`right`) |
| `collapsed` | `bool` | `False` | Start collapsed |
| `parent_id` | `str` | `None` | Entity id to attach the group to (follows it in 3D) instead of anchoring it in the overlay |
| `on_toggle` | `Callable` | `None` | Async callback: `(value: bool, event: ControlEvent) -> None` |

Controls must be created **before** the group that references them.

Groups render identically in **single-scene** and **layout** modes: without
`parent_id` they anchor in the overlay (`position`); with `parent_id` they
attach to that entity.  See `py/examples/viz/scenes/control_group_overlay.py`
(layout mode) and `py/examples/viz/scenes/control_group_single.py`
(single-scene mode).

## Icons

Buttons and group title bars accept an optional icon. Icons are addressed as
`family:name` strings:

- `material:<name>` — a Google Material Icons ligature name (e.g.
  `material:settings`, `material:play_arrow`). Loaded on demand from the Google
  Fonts stylesheet, so no icon files are shipped — but an internet connection
  is required to render them.
- `uc:<glyph>` — a Unicode symbol rendered as literal text (e.g. `uc:▶`,
  `uc:⚙`). Always available, no font needed.
- A bare name (no `:`) defaults to `material`.

Use the `EIconMaterial` / `EIconUC` enums for autocompletion, or pass a raw
string such as `"material:home"`:

```python
from pytanga.viz import EIconMaterial, EIconUC

self.viz.add_button("delete", icon=EIconMaterial.DELETE, icon_only=True)
self.viz.add_control_group("g", title="Settings", icon=EIconUC.GEAR)
```

## Tooltips

Every control — and the control-group title bar — accepts a `tooltip` string,
rendered as a native `title` hover tooltip. Icon-only buttons show their
tooltip (or label) as the button's accessible name.

## Removing controls

```python
self.viz.remove_control("sphere_b_x")
self.viz.remove_control_group("viewport_controls")
self.viz.clear_controls()  # remove all
```

## Updating control values

After a control has been created, its value can be updated from the backend
**in place** — the panel is not rebuilt, so collapse, drag, and focus state are
preserved:

```python
# Panel / add_* controls
self.viz.set_control_value("radius", 3.0)

# Scene-scoped controls
detail.set_control_value("radius", 3.0)

# Layout control views
self.viz.set_control_view_value(radius_view, 3.0)
```

`update_control` also accepts a `value=` keyword and routes it through
`set_control_value`:

```python
self.viz.update_control("radius", value=3.0)
detail.update_control("radius", label="Radius (m)")  # scene-scoped
```

## Scene-scoped controls

Controls are scoped per-scene — when using :class:`VizSceneHandle`, controls
are created on the target scene and only appear for browsers viewing that
scene:

```python
detail = viz.scene("detail")
detail.add_slider("radius", label="Radius", min=0.1, max=5.0, on_change=on_radius)
detail.add_button("reset", label="Reset", on_click=on_reset)
detail.add_control_group("detail_controls", controls=["radius", "reset"], title="Detail")
```

Controls and groups are pushed only to browsers viewing the ``"detail"`` scene.
This allows different scenes to have completely independent control panels.

## Example

- `py/examples/viz/interaction/all_controls.py` — one of every control kind in
  a single app.
- `py/examples/viz/interaction/table_data.py` — an editable table control with
  cell / row / column handlers.
