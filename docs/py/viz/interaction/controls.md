# Controls

`pytanga.viz` controls are **declarative `*View` classes** — `SliderView`,
`DropdownView`, `ButtonView`, `CheckboxView`, `TextFieldView`, `TextAreaView`,
`ColorPickerView`, `ValueEditView`, `TableView`, `FileChooserView`,
`LabelView`, and `MarkdownView`.  There are no `add_*` facade methods: build a
view, give it a unique `id` and an **async** handler, and place it in a
`GroupView`/`StackView` inside a layout (or mount it with `viz.add(view)`).

```python
layout = GroupView(
    "Controls",
    [
        SliderView(
            "radius", label="Radius", min=0.2, max=5.0, value=1.0,
            on_change=self.on_radius,
        ),
        ButtonView("reset", label="Reset", on_click=self.on_reset),
    ],
)
viz.show(layout=layout)   # registers the layout + control-view handlers
```

- The full constructor signatures and how views fit into split/stack layouts are
  on the [Control Views](control-views.md) page.
- The handler contract and the `VisualizerApp` lifecycle are on
  [Handlers & Lifecycle](../app/handlers.md).

## Quick mapping (former `add_*` facade → view class)

| Former `add_*` facade | View class |
|---|---|
| `add_slider` | [`SliderView`](control-views.md#sliderview) |
| `add_dropdown` | [`DropdownView`](control-views.md#dropdownview) |
| `add_button` | [`ButtonView`](control-views.md#buttonview) |
| `add_text_field` | [`TextFieldView`](control-views.md#textfieldview) |
| `add_text_area` | [`TextAreaView`](control-views.md#textareaview) |
| `add_color_picker` | [`ColorPickerView`](control-views.md#colorpickerview) |
| `add_checkbox` | [`CheckboxView`](control-views.md#checkboxview) |
| `add_value_edit` | [`ValueEditView`](control-views.md#valueeditview) |
| `add_table` | [`TableView`](control-views.md#tableview) |
| `add_file_chooser` | [`FileChooserView`](control-views.md#filechooserview) |
| `add_control_group` | [`GroupView`](control-views.md#groupview) |

Each `*View` constructor takes the same parameters the old `add_*` method did
(``cid`` first, then keyword args); a `SliderView` mirrors `add_slider`
(including `on_press` / `on_release` and `variant`), a `ButtonView` mirrors
`add_button`, and so on.

## `SliderView`

```python
SliderView(
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
| `variant` | `EControlVariant` | `"default"` | Visual variant (`"default"` or `"menu"`) |
| `min` | `float` | `0.0` | Minimum value |
| `max` | `float` | `1.0` | Maximum value |
| `step` | `float` | `0.01` | Step increment |
| `value` | `float` | `min` | Initial value |
| `on_change` | `Callable` | `None` | Async callback: `(value: float, event: ControlEvent) -> None` |
| `on_press` | `Callable` | `None` | Async callback on drag start: `(value: float, event) -> None` |
| `on_release` | `Callable` | `None` | Async callback on drag end: `(value: float, event) -> None` |

## `DropdownView`

```python
DropdownView(
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

## `ButtonView`

```python
ButtonView(
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
| `variant` | `EControlVariant` | `"default"` | Visual variant (`"default"` or `"menu"`) |
| `icon` | `Icon` | `None` | Optional icon (see [Icons](#icons)) |
| `icon_only` | `bool` | `False` | Render only the icon as a small square button |
| `tooltip` | `str` | `""` | Hover tooltip |
| `on_click` | `Callable` | `None` | Async callback: `(value: None, event: ControlEvent) -> None` |

## `TextFieldView`

Single-line text input:

```python
TextFieldView(
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

## `TextAreaView`

Multi-line text input:

```python
TextAreaView(
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

## `ColorPickerView`

Native color input (hex value):

```python
ColorPickerView(
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

## `CheckboxView`

Boolean checkbox:

```python
CheckboxView(
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
| `variant` | `EControlVariant` | `"default"` | Visual variant (`"default"` or `"menu"`) |
| `value` | `bool` | `False` | Initial checked state |
| `tooltip` | `str` | `""` | Hover tooltip |
| `on_change` | `Callable` | `None` | Async callback: `(value: bool, event: ControlEvent) -> None` |

## `ValueEditView`

A numeric stepper with up/down buttons; arrow keys (while the pointer hovers
over the control) and the scroll wheel also step the value.  By default the
value can also be typed directly (`editable=True`); set `editable=False` to
restrict input to the buttons, keys, and wheel:

```python
ValueEditView(
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

## `TableView`

An editable tabular-data grid (rendered with Tabulator). The backend defines
the columns and initial rows; the user can edit any cell and, when enabled,
append rows and columns. **Double-click** a cell to edit it (a single click or
drag selects cells instead). Each change is reported back to a distinct handler:

```python
TableView(
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
| `on_change` | `Callable` | `None` | Async callback: `(value: dict, event) -> None` — fires once with the full `{"columns", "rows"}` on undo/redo |

The handler payloads are `TableCellChange(row, col, value)`,
`TableRowAdd(row, values)`, `TableColumnAdd(col, header, values)`, and
`TableRowsDelete(rows)` (all zero-based). Cell values are strings on the wire —
coerce in the handler as needed. Replace the grid and push it to the browser
with `table_view.set_value({"columns": [...], "rows": [...]})`.

### Undo and redo

The grid keeps a backend-side undo history (one snapshot per *committed* edit —
entering a cell and pressing Enter/Tab, adding a row/column, or deleting rows;
not per keystroke). In the browser, **Ctrl+Z** undoes and **Ctrl+Shift+Z** (or
**Ctrl+Y**) redoes. The same operations are available on the view:

```python
table_view.undo()               # -> bool (restores + pushes the grid)
table_view.redo()               # -> bool (restores + pushes the grid)
table_view.can_undo             # -> bool
table_view.can_redo             # -> bool
table_view.control.clear_history()
```

`max_history` bounds the number of retained undo steps (default 100). A
programmatic `set_value` full-replace clears the history.  `undo()` and
`redo()` restore the previous grid **and push it to the browser**, so the
rendered grid updates in place (no need to call `set_value`).

Register a single coarse-grained callback with `on_change` to be notified when
many cells change at once — it fires **once** with the full table value
(`{"columns": [...], "rows": [[...]]}`) on every undo/redo (browser Ctrl+Z /
Ctrl+Shift+Z / Ctrl+Y), instead of one `on_cell_change` per cell.

## `FileChooserView`

A backend-driven directory-listing view (no path field or "Browse…" button —
compose those yourself, or use `FileChooserDialog`).  See
[File Chooser](../app/file-chooser.md).

## `LabelView` / `MarkdownView`

Read-only display views: `LabelView("id", value="…", font_size=14)` renders a
single text line and `MarkdownView("id", value="…")` renders markdown with
optional KaTeX math.  Both carry a settable `value` (use `view.set_value(...)`).
See [Control Views](control-views.md) for the full signatures.

## Grouping (`GroupView`)

Group controls into a titled, collapsible [`GroupView`](control-views.md#groupview),
anchored over a scene (or attached to a 3D object) or used as a split pane:

```python
GroupView(
    "Controls",
    [sphere_b_x_view, mode_view, reset_view],
    position="bottom-right",
)
```

`position` anchors the group over a scene canvas (`top-left` / `top-right` /
`bottom-left` / `bottom-right`, or centered edges `top` / `bottom` / `left` /
`right`); `parent_id` attaches it to a 3D entity instead.  See the full
signature on the [Control Views](control-views.md#groupview) page.

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

ButtonView("delete", icon=EIconMaterial.DELETE, icon_only=True)
GroupView("Settings", [settings_view], icon=EIconUC.GEAR)
```

## Tooltips

Every control — and the `GroupView` title bar — accepts a `tooltip` string,
rendered as a native `title` hover tooltip. Icon-only buttons show their
tooltip (or label) as the button's accessible name.

## Updating control values

A control view can be updated from the backend **in place** — the layout is not
rebuilt, so collapse, drag, and focus state are preserved:

```python
radius_view.set_value(3.0)            # sets + pushes control_update to the browser

value = radius_view.control.get_value()   # read the current value
radius_view.control.set_value(3.0)        # model-only (no push)
```

`view.set_value(...)` is the push path: it mutates the wrapped control and sends
a `control_update`, so the browser reflects the change immediately. `view.control`
exposes the raw model (`get_value` / `set_value`, and `Table` `undo` / `redo` /
`clear_history`).

## Example

- `py/examples/viz/ui/controls/all_controls.py` — one of every control kind in
  a single app.
- `py/examples/viz/ui/controls/table_data.py` — an editable table control with
  cell / row / column handlers.
