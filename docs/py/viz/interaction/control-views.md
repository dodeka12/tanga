# Control Views (`xxxView`)

`pytanga.viz` controls are the **declarative `xxxView` classes** — `SliderView`,
`DropdownView`, `ButtonView`, `FileChooserView`, `TextFieldView`, `TextAreaView`,
`ColorPickerView`, `CheckboxView`, `ValueEditView`, `TableView`, `LabelView`,
and `MarkdownView`.  Build a view, place it inside a `GroupView`/`StackView` as
a pane of a split-view layout (or mount it with `viz.add(view)`), and its value
flows back through an `on_change`/`on_click` handler (registered automatically
when the layout is set).

There are no `add_*` facade methods — every control kind is declared as a view.
For the per-kind parameter tables and handler payloads, see
[Controls](controls.md); for placing views in layouts, see
[Layouts](../app/layouts.md).

Every control view is a plain `View` (no scene) that renders a single HTML
control. A handler written for one control kind works unchanged for the others
— the contract is always `(value, event)`.

### Control variants (`variant`)

`ButtonView`, `CheckboxView`, and `SliderView` accept a `variant=` parameter —
an `EControlVariant` (`"default"` or `"menu"`). The `"menu"` variant renders the
control flat and borderless for menu rows. `MenuView` applies the `"menu"`
variant to its control children automatically (`override_variant=True` by
default), so you usually don't pass `variant=` by hand.

## Layout containers

Every view is a `View`. Containers arrange their children; the leaves render
content. For the full view model — `Size` units, splitters, per-pane cameras —
see [Split Views](../visualizer/split-views.md).

Every control view is a `ControlView`. By default it sets a size floor of
`min_width=Size.px(120)` and `min_height=Size.px(32)` so a `StackView`/`GroupView`
can size to its controls; pass `min_width=None` / `min_height=None` to disable
the floors.

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
  by each child's `position` (an `EAnchor`).

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

Requires at least 2 children; any number ≥ 2 is allowed (N children → N − 1
splitters). `sizes`, when given, must have one entry per
child. `movable=False` locks every splitter; the default `None` auto-detects
(an implicit `SpacerView` fills leftover space). `_node_type` is `"split"`.

### StackView

A flow container that stacks children vertically, horizontally, or wraps —
normal document order, no splitters, sizes to its content along the stack
axis.

```python
StackView(
    direction,            # "vertical" | "horizontal" | "wrap"
    children=None,        # list[View] | None
    *,
    scrollable=False,     # bool — scroll instead of clipping when content overflows
    gap=None,             # int | None — px spacing (None = default 4 px, 0 = none)
    align="stretch",      # "start" | "center" | "end" | "stretch"
    justify="start",      # "start" | "center" | "end" | "space-between" | "space-around" | "space-evenly"
    **kwargs,             # forwarded to View (sizes)
)
```

`_node_type` is `"stack"`. With `scrollable=True`, the stack stops forcing
its content size along the stack axis, so an enclosing `SplitView` may shrink
it and the content scrolls inside the pane (a thin dark scrollbar appears only
on overflow).

### GroupView

A titled `StackView` (panel chrome), usable as a split pane or as an overlay
child of a `SceneView` (where `position` anchors it over the canvas). This is
the declarative grouping view (the former `add_control_group`).

```python
GroupView(
    title="",          # str
    children=None,     # list[View] | None
    *,
    direction="vertical",  # StackDirection
    position=None,     # EAnchor | None — corner or centered-edge anchor (e.g. "top-right", "bottom")
    collapsed=False,   # bool
    scrollable=False,  # bool — scroll the content (title bar stays pinned)
    gap=None,          # int | None — px spacing (None = default 4 px, 0 = none)
    align="stretch",   # "start" | "center" | "end" | "stretch"
    justify="start",   # "start" | "center" | "end" | "space-between" | "space-around" | "space-evenly"
    icon=None,         # Icon | None — leading title-bar icon
    icon_only=False,   # bool — render only the icon (no title text)
    tooltip="",        # str — hover tooltip on the title bar
    parent_id=None,    # str | None — attach to a 3D entity (follow it) instead of anchoring in the overlay
    **kwargs,          # forwarded to View (sizes)
)
```

`_node_type` is `"group"`. With `scrollable=True`, the title bar stays pinned
and the content region scrolls instead of clipping when the pane is smaller
than the controls (a thin dark scrollbar appears only on overflow). The
fold/unfold button in the title bar is a borderless icon.

### MenuView

A menu — a hamburger `dropdown` or a permanent horizontal `bar` of options.
`children` are the options (control views); a child may be another `MenuView`
to form a nested sub-menu. `_node_type` is `"menu"`.

```python
MenuView(
    label="",           # str
    children=None,      # list[View] | None — options (control views / sub-menus)
    *,
    trigger_icon=None,  # Icon | None — optional leading icon (e.g. EIconMaterial.MENU)
    mode="dropdown",    # "dropdown" | "bar"
    direction=None,      # StackDirection | None — "horizontal" for bars, else "vertical"
    position=None,      # EAnchor | None — corner or centered-edge anchor (e.g. "top-right", "bottom")
    override_variant=True,  # bool — auto-set the MENU variant on control children
    **kwargs,           # forwarded to View (sizes)
)
```

- `mode="dropdown"` renders a click-to-toggle trigger with the options in a
  hidden panel (outside-click or `Escape` closes it); a nested `MenuView` opens
  beside its parent as a sub-menu.
- `mode="bar"` renders the options always-visible in a horizontal strip; a
  nested `MenuView` renders as a plain menu-bar label and opens its panel
  downwards (flipping upwards near the bottom of the viewport).
- `override_variant=True` (default) forces every eligible control in the subtree
  to the `MENU` variant, so options render flat without setting `variant=` by
  hand.

Global menus are declared as a `MenuView` in the default layout's overlay (via
`viz.add(menu)` or `viz.set_layout`); per-pane menus are declared with
`SceneView(overlay=[MenuView(...)])`:

```python
menu = MenuView(
    label="Settings",
    trigger_icon=EIconMaterial.MENU,
    children=[
        ButtonView("fit", label="Fit camera", on_click=on_fit),
        SliderView("radius", label="Radius", on_change=on_radius),
    ],
)
viz.add(menu)  # mounts in the default layout's overlay
```

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
    variant="default",  # EControlVariant — "default" | "menu"
    min=0.0,
    max=1.0,
    step=0.01,
    value=None,        # float | None — defaults to min
    on_change=None,    # Handler — async (value: float, event)
    on_press=None,     # Handler — async (value: float, event) on drag start
    on_release=None,   # Handler — async (value: float, event) on drag end
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
    variant="default",  # EControlVariant — "default" | "menu"
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

The bare file-selection view: an embedded directory listing (path bar + entries)
with no path field, no "Browse…" button, and no path display.  Selecting a file
sends `file_browser_select`; directory navigation is clamped to `root`.  The
listing fills its container and scrolls internally, so it keeps a stable size
as entries change. `_node_type` is `"file_chooser_view"`.

```python
FileChooserView(
    cid,
    *,
    value="",          # str — initial path
    root=None,         # str | None — browse root
    accept="",         # str
    on_change=None,    # Handler — async (value: str, event)
    **kwargs,
)
```

A path display / edit field / browse button are intentionally **not** part of
this view.  Compose them yourself (e.g. a `TextFieldView` plus a `ButtonView`
that calls `open_file_chooser`), or use
[`FileChooserDialog`](#filechooserdialog) to show the listing inside a dialog.

### FileChooserDialog

A full file-open dialog — a [`FileChooserView`](#filechooserview) listing plus a
path line and OK/Cancel buttons — rendered as a `DialogView` variant.  Pass it
to `show_dialog`:

```python
viz.show_dialog(
    FileChooserDialog("fc", root="/data", on_accept=...),
    title="Select a file",
)
```

Selecting a file fills the dialog's path line (no close); `OK` fires
`on_accept(path)` and closes, while `Cancel`/✕ fire `on_close` (dismiss).

```python
FileChooserDialog(
    cid,
    *,
    title="Select a file",  # str
    value="",               # str — initial path
    root=None,              # str | None — browse root
    accept="",              # str
    on_accept=None,         # Handler — async (path: str, event) on OK
    on_close=None,          # Handler — async (value, event) on Cancel/✕
    align_x=0.5,            # float
    align_y=0.5,            # float
    dismissable=True,       # bool
    width=None,             # SizeSpec | None — dialog width (default 520px)
    height=None,            # SizeSpec | None — dialog height (default 420px)
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
    variant="default",  # EControlVariant — "default" | "menu"
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
    rows=(),                # list[list[Any]] | tuple[tuple[Any, ...], ...]
    column_types=None,      # per-column hints: None | "number" | "string" | "bool" | [..values]
    json_path=None,         # str | None — auto-save JSON path
    allow_add_rows=True,    # bool
    allow_add_columns=True, # bool
    allow_delete_rows=True, # bool
    max_history=100,        # int
    editable_titles=True,   # bool — double-click a header to rename it
    tooltip="",             # str
    on_cell_change=None,    # Handler
    on_row_add=None,        # Handler
    on_column_add=None,     # Handler
    on_row_delete=None,     # Handler
    on_column_delete=None,  # Handler
    on_column_title_change=None,  # Handler — (change: TableColumnTitleChange, event)
    on_column_type_change=None,   # Handler — (change: TableColumnTypeChange, event)
    on_cell_select=None,    # Handler — (select: TableCellSelect, event)
    on_change=None,         # Handler — (value: dict, event) on undo/redo
    **kwargs,
)
```

Cell values are strings on the wire. See [Controls](controls.md) for the
handler payloads (`TableCellChange` / `TableRowAdd` / `TableColumnAdd` /
`TableRowsDelete`) and for undo/redo (Ctrl+Z / Ctrl+Shift+Z / Ctrl+Y).

Each column has a type — `number`, `string`, `bool`, or an `enum` (a fixed list
of allowed strings).  `column_types` sets them explicitly (one entry per
column: `None` deduces, a scalar name picks a scalar type, a list of strings is
an enum); omitted entries deduce from the initial data (all bools → `bool`, all
numbers → `number`, else `string`).  Numbers right-align and reject non-numeric
input, booleans show an always-on checkbox, enums edit through a dropdown.

`TableView` also exposes `undo()` / `redo()` / `can_undo` / `can_redo`, plus
`insert_row(index, values=None)` / `insert_column(index, header="", values=None,
column_type=None)` / `delete_row(index)` / `delete_column(index)` /
`rename_column(col, title)` / `set_column_format(col, fmt)` /
`convert_column(col, target)` (mutate the model and push the full grid back to
the browser), the selected-cell `active_cell` property (`(row, col)` or
`None`), `save(path)` / `load(path)` (versioned JSON, including types + column
widths + row height + sort) and `to_csv(path)` / `from_csv(path)` (plain data).
Pass `json_path=...` to load the file at construction and auto-save on every
change.  `set_column_format` sets a `number` column's `str.format` display
template; `convert_column` applies (or rejects) a type change and fires
`on_column_type_change` with the result.

`on_change` is a bulk handler that fires once with the full grid value on
undo/redo (see [Controls](controls.md)).

## Runtime helpers

Each `ControlView` wraps a `pytanga.viz._controls.Control`, exposed as
`view.control`.  Values are updated and read through the view and its control:

- `view.set_value(value)` sets the value **and** pushes a `control_update` to
  the browser (the backend-initiated update path).
- `view.control.get_value()` / `view.control.set_value(value)` read/coerce the
  wrapped model directly (no push).

!!! note "`ButtonView` carries no value"
    Setting or reading a value on a `ButtonView` raises `TypeError` — a button
    has no value to set or read.

### `iter_control_views(root)`

Yield every `ControlView` in the tree in DFS order (descending through
`children` and `overlay`).

### `serialize_layout(root, name="", overlay=None)`

Serialize a view tree to the `view_layout` message (the message consumed by
the browser frontend). `name` is the layout name used in the URL
(`/?view=<name>`); `overlay` is an optional list of views mounted into the
full-screen global overlay (used by global menus).

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
[`all_controls.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/ui/controls/all_controls.py)
(one of every control kind in a single app).
