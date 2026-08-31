# Control Views (`xxxView`)

`pytanga.viz` offers two ways to put controls in front of the user, backed by
the **same async handler contract** — `(value, event)`:

- **Panel controls** — `viz.add_slider` / `add_dropdown` / `add_button` / …
  (a floating panel overlaid on the scene). See [Panel Controls](controls.md).
- **Control views** — the declarative `xxxView` classes documented here, placed
  inside a `GroupView`/`StackView` as a pane of a split-view layout. See
  [Layouts](../app/layouts.md).

Every control view is a plain `View` (no scene) that renders a single HTML
control and sends its value back through an `on_change`/`on_click` handler
(registered automatically when the layout is set). A handler written for one
surface works unchanged with the other.

## Two control surfaces

| Panel control (`viz.add_*`) | View class |
|-----------------------------|------------|
| `add_slider` | [`SliderView`](#sliderview) |
| `add_dropdown` | [`DropdownView`](#dropdownview) |
| `add_button` | [`ButtonView`](#buttonview) |
| `add_file_chooser` | [`FileChooserView`](#filechooserview) |
| `add_text_field` | [`TextFieldView`](#textfieldview) |
| `add_text_area` | [`TextAreaView`](#textareaview) |
| `add_color_picker` | [`ColorPickerView`](#colorpickerview) |
| `add_checkbox` | [`CheckboxView`](#checkboxview) |
| `add_value_edit` | [`ValueEditView`](#valueeditview) |
| `add_table` | [`TableView`](#tableview) |
| `add_control_group` | [`GroupView`](#groupview) |

The panel API (parameter tables for each `add_*` method) is documented in
[Panel Controls](controls.md). The view classes below use the same parameter
names and defaults, so a `SliderView` mirrors `add_slider`, a `ButtonView`
mirrors `add_button`, and so on.

## Layout containers

Every view is a `View`. Containers arrange their children; the leaves render
content. For the full view model — `Size` units, splitters, per-pane cameras —
see [Split Views](../visualizer/split-views.md).

### View

Base for every pane/container in a layout. Split-agnostic.

```python
View(
    *,
    size=None,               # SizeSpec — sets both preferred axes
    preferred_width=None,    # SizeSpec
    preferred_height=None,   # SizeSpec
    min_width=None,          # SizeSpec
    min_height=None,         # SizeSpec
    max_width=None,          # SizeSpec
    max_height=None,         # SizeSpec
)
```

All sizes are `SizeSpec` values (see `Size.px` / `Size.percent` / `Size.fr` /
`auto` in [Split Views](../visualizer/split-views.md)). The computed
properties `fixed_x` / `fixed_y` are `True` when `min == max` along that axis,
which is how a container decides whether a splitter next to this view is
draggable. `_node_type` is `"view"`.

### SceneView

A pane that renders a named scene.

```python
SceneView(
    scene,            # str name or scene handle
    *,
    id=None,          # str | None — stable pane id (auto "svN")
    camera=None,      # CameraConfig | View2DConfig | View3dConfig | None
    overlay=None,     # list[View] | None — views floating over the canvas
    **kwargs,         # forwarded to View (sizes)
)
```

- `scene` — the scene name (or a `VizSceneHandle`). `SceneView("")` is the
  main scene.
- `id` — the stable key used to address the pane at runtime
  (`Visualizer.set_view_camera`); auto-generated as `"svN"` when omitted.
- `camera` — overrides the scene's camera **for this pane only**, so the same
  scene can be shown from different viewpoints in separate panes. `None` uses
  the scene's camera.
- `overlay` — views that float over the canvas (e.g. a `GroupView`), anchored
  by each child's `position`.

Scene panes default to a 120 px minimum on both axes so a splitter cannot
collapse them to nothing (override `min_width`/`min_height`, or pass `None` to
disable the floor). `_node_type` is `"scene_view"`.

### SpacerView

An empty, fully-flexible filler pane. `_node_type` is `"spacer"`.

### SplitView

A container that lays its children out along one axis with draggable
splitters.

```python
SplitView(
    orientation,       # "horizontal" | "vertical"
    children=None,     # list[View] | None
    *,
    movable=None,      # bool | None — None auto-detects
    sizes=None,        # list[SizeSpec] | None — must match children
    **kwargs,          # forwarded to View (sizes)
)
```

Requires at least 2 children. `sizes`, when given, must have one entry per
child. `movable=False` locks every splitter; the default `None` auto-detects
(an implicit `SpacerView` fills leftover space). `_node_type` is `"split"`.

### StackView

A flow container that stacks children vertically, horizontally, or wraps —
normal document order, no splitters, sizes to its content along the stack
axis.

```python
StackView(
    direction,         # "vertical" | "horizontal" | "wrap"
    children=None,     # list[View] | None
    **kwargs,          # forwarded to View (sizes)
)
```

`_node_type` is `"stack"`.

### GroupView

A titled `StackView` (panel chrome), usable as a split pane or as an overlay
child of a `SceneView` (where `position` anchors it over the canvas). This is
the view form of the panel `add_control_group`.

```python
GroupView(
    title="",          # str
    children=None,     # list[View] | None
    *,
    direction="vertical",  # StackDirection
    position=None,     # str | None — "top-left" | "top-right" | "bottom-left" | "bottom-right"
    collapsed=False,   # bool
    **kwargs,          # forwarded to View (sizes)
)
```

`_node_type` is `"group"`.

## Control views

Every control view derives from `ControlView`, which is a plain `View` whose
`id` doubles as the WebSocket event key.

### ControlView

```python
ControlView(
    cid,               # str — unique control id (event key)
    *,
    label="",          # str
    tooltip="",        # str
    **kwargs,          # forwarded to View (sizes)
)
```

The control `cid` must be unique across the app. `_node_type` is `"control"`.

### SliderView

A numeric slider. `_node_type` is `"slider_view"`.

```python
SliderView(
    cid,
    *,
    label="",
    min=0.0,
    max=1.0,
    step=0.01,
    value=None,        # float | None — defaults to min
    on_change=None,    # Handler — async (value: float, event)
    **kwargs,
)
```

### ButtonView

A clickable button (with optional icon). Carries **no value** — see the
runtime-helpers note below. `_node_type` is `"button_view"`.

```python
ButtonView(
    cid,
    *,
    label="",
    icon=None,         # Icon | None
    icon_only=False,   # bool
    on_click=None,     # Handler — async (value: None, event)
    **kwargs,
)
```

### DropdownView

A dropdown/select. `_node_type` is `"dropdown_view"`.

```python
DropdownView(
    cid,
    *,
    label="",
    options=(),        # list[str] | tuple[str, ...]
    value="",          # str
    on_change=None,    # Handler — async (value: str, event)
    **kwargs,
)
```

### FileChooserView

A file-path control (text field + backend file browser). `_node_type` is
`"file_chooser_view"`.

```python
FileChooserView(
    cid,
    *,
    label="",
    value="",          # str
    placeholder="",    # str
    root=None,         # str | None — browse root
    accept="",         # str
    on_change=None,    # Handler — async (value: str, event)
    **kwargs,
)
```

### TextFieldView

A single-line text input. `_node_type` is `"text_field_view"`.

```python
TextFieldView(
    cid,
    *,
    label="",
    value="",          # str
    placeholder="",    # str
    tooltip="",        # str
    on_change=None,    # Handler — async (value: str, event)
    **kwargs,
)
```

### TextAreaView

A multi-line text input. `_node_type` is `"text_area_view"`.

```python
TextAreaView(
    cid,
    *,
    label="",
    value="",          # str
    placeholder="",    # str
    rows=4,            # int
    tooltip="",        # str
    on_change=None,    # Handler — async (value: str, event)
    **kwargs,
)
```

### ColorPickerView

A color picker (hex value). `_node_type` is `"color_picker_view"`.

```python
ColorPickerView(
    cid,
    *,
    label="",
    value="#ffffff",   # str
    tooltip="",        # str
    on_change=None,    # Handler — async (value: str, event)
    **kwargs,
)
```

### CheckboxView

A boolean checkbox. `_node_type` is `"checkbox_view"`.

```python
CheckboxView(
    cid,
    *,
    label="",
    value=False,       # bool
    tooltip="",        # str
    on_change=None,    # Handler — async (value: bool, event)
    **kwargs,
)
```

### ValueEditView

A numeric stepper (up/down buttons; arrow keys and the scroll wheel also
step). `_node_type` is `"value_edit_view"`.

```python
ValueEditView(
    cid,
    *,
    label="",
    min=0.0,
    max=1.0,
    step=0.1,
    digits=2,          # int — decimal places shown
    value=0.0,
    editable=True,     # bool — allow direct text editing
    tooltip="",        # str
    on_change=None,    # Handler — async (value: float, event)
    **kwargs,
)
```

### TableView

An editable tabular-data grid. `_node_type` is `"table_view"`.

```python
TableView(
    cid,
    *,
    label="",
    columns=(),             # list[str] | tuple[str, ...]
    rows=(),                # list[list[str]] | tuple[tuple[str, ...], ...]
    allow_add_rows=True,    # bool
    allow_add_columns=True, # bool
    tooltip="",             # str
    on_cell_change=None,    # Handler
    on_row_add=None,        # Handler
    on_column_add=None,     # Handler
    **kwargs,
)
```

Cell values are strings on the wire. See [Panel Controls](controls.md) for the
handler payloads (`TableCellChange` / `TableRowAdd` / `TableColumnAdd`).

## Runtime helpers

These free functions mirror the panel-control value API for view controls.

### `set_control_view_value(view, value)`

Coerce and set *value* on a control view, mirroring
`pytanga.viz._controls.set_control_value`. Coercion matches the control kind:
`SliderView`/`ValueEditView` → `float`, `CheckboxView` → `bool`,
`DropdownView`/`ColorPickerView`/`TextFieldView`/`TextAreaView`/
`FileChooserView` → `str`, and `TableView` → a
`{"columns": [...], "rows": [...]}` dict.

### `get_control_view_value(view)`

Return the current value of a value-bearing control view (`TableView` returns
the `{"columns": ..., "rows": ...}` dict).

!!! note "`ButtonView` carries no value"
    `ButtonView` raises `TypeError` from both `set_control_view_value` and
    `get_control_view_value` — a button has no value to set or read.

### `iter_control_views(root)`

Yield every `ControlView` in the tree in DFS order (descending through
`children` and `overlay`).

### `serialize_layout(root, name="")`

Serialize a view tree to the `view_layout` message (the message consumed by
the browser frontend). `name` is the layout name used in the URL
(`/?view=<name>`).

## Minimal example

A `SplitView` with a `GroupView` sidebar holding a `SliderView` and a
`ButtonView`, next to the main scene:

```python
from pytanga.viz import (
    ButtonView, GroupView, SceneView, SliderView, SplitView, Visualizer,
)

viz = Visualizer()
viz.add(Point(0, 0, 0), color="#ff4444")  # scene content

layout = SplitView(
    orientation="horizontal",
    children=[
        SceneView(""),
        GroupView(
            "Controls",
            [
                SliderView("radius", label="Radius", min=0.2, max=5.0, value=1.0),
                ButtonView("reset", label="Reset"),
            ],
        ),
    ],
)

viz.show(layout=layout)  # registers the layout + control-view handlers
viz.wait()
```

Handlers are registered automatically when the layout is set, so a
`SliderView`/`ButtonView` behaves exactly like a panel control. For a complete
app, see the [Layouts](../app/layouts.md) guide and
[`all_controls.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/interaction/all_controls.py)
(one of every control kind in a single app).
