# Split Views

Split views let a **single browser page** show multiple scenes (or control
panels) in separate panes, arranged with horizontal or vertical splits. Each split can hold **any number
of panes** in one direction (N panes → N − 1 splitters), splits can be nested to
any depth, and each divider is draggable when a non-fixed pane sits on each
side of it. The existing per-scene URLs keep working
unchanged — a split view is just an additional layout served at one URL
(`/?view=<name>`).

A single scene is also a layout: a per-scene URL (`/` or `/{name}`) is served as
a one-`SceneView` stack, so overlays (control groups, menus, dialogs) mount and
update identically in single-scene and split-view modes.

## The View Hierarchy

Everything in a layout is a `View`. Two containers arrange their children, and
the leaves render content:

| Class | Purpose |
|-------|---------|
| `View` | Base for every pane/container. Exposes per-axis preferred/min/max sizes. |
| `SplitView` | A container that lays children out along one axis with draggable splitters. |
| `StackView` | A flex container that stacks children vertically, horizontally, or wraps. |
| `ToolbarView` | A horizontal `StackView` row with a thin border, inner margin, and configurable alignment. |
| `SceneView` | A pane that renders a named scene (`scene` name or handle), optionally with overlay views. |
| `GroupView` | A titled `StackView` (panel chrome) for grouping control views; usable as a pane or a scene overlay. |
| `MenuView` | A hamburger dropdown or a permanent horizontal `bar` of options, with nestable sub-menus. |
| `SliderView` / `ButtonView` / `DropdownView` / `TableView` | A single HTML control rendered as a `View`. |
| `LabelView` / `MarkdownView` | Read-only display text / rendered markdown (with KaTeX math) as a `View`. |
| `LogView` | A live, auto-scrolling two-column (time \| message) log with a history cap and JSON-lines file I/O. |
| `SeparatorView` | A thin 1px divider line with spacing; auto-oriented perpendicular to its container. |
| `SpacerView` | An empty, fully-flexible filler pane. |

Containers are themselves `View`s, so layouts nest freely.

## Sizes and Units

Every `View` accepts per-axis constraints via `Size` values. `Size` supports four
units:

| Unit | Meaning |
|------|---------|
| `px` | Absolute CSS pixels — `Size.px(280)`. |
| `%`  | A fraction of the parent extent along that axis — `Size.percent(50)`. |
| `fr` | A flexible share (preferred sizes only, never min/max) — `Size.fr(2)`. |
| `auto` | Unconstrained (min → 0, max → ∞, preferred → natural). |

`View` constructor arguments: `size` (sets both preferred axes), and the
per-axis `preferred_width/height`, `min_width/height`, `max_width/height`.

A `GroupView` adds its title bar and panel padding to the derived content size,
so its natural `preferred_height` is its controls plus that chrome. The chrome
is measured from the rendered DOM, so it follows the active theme's fonts and
paddings; collapsing a `GroupView` sizes it to just the title bar's bottom
border (the drawn rule).

## Display Views

Three read-only content views render text, markdown, and a live log inside a
layout (no scene required):

| Class | Purpose |
|-------|---------|
| `LabelView` | A single line of text with a configurable `font_size` (default `14` px). |
| `MarkdownView` | A multi-line block of rendered markdown with KaTeX math (`$…$` / `$$…$$`). |
| `LogView` | A live, auto-scrolling two-column (time \| message) log. |

`LabelView` and `MarkdownView` are **display-only controls**: they carry a
`value` and can be updated in place after creation via `view.set_value(value)`,
which pushes the same `control_update` message used by every other control:

```python
label = LabelView("label", value="hello", font_size=20)
markdown = MarkdownView("md", value="# Title\n\n$E = mc^2$")
```

`LogView` is not a control — its lines are appended from the backend, so it has
its own `log_update` push.  `log()` captures a UTC timestamp and accepts either
a string (stored as `message`) or a dict (whose keys are folded into the line);
the frontend shows `message`, falling back to JSON of the other keys:

```python
log = LogView(id="log", max_history=1000)   # None = unlimited
log.log("plain line")
log.log({"message": "structured", "level": "info"})
log.get_log()          # -> list[dict] (copies)
log.write_file(path)   # JSON lines (one dict per line)
log.load_file(path)    # replace (truncated to max_history)
log.clear()
```

Rows alternate shading, new lines auto-scroll into view (unless the user has
scrolled up), and `max_history` drops the oldest lines on both the backend and
the browser.

## Fixed vs. Movable Splitters

A view is **fixed** along an axis when its `min` and `max` are equal
(`View.fixed_x` / `View.fixed_y`). A splitter is draggable when there is a
**non-fixed pane on each side** of it, searching across any fixed panes in
between. Dragging trades space between the **nearest non-fixed** panes on each
side, so a fixed pane keeps its size without walling off the panes beyond it:
in `[A, fixed_B, C]` both splitters stay movable (`A↔B` borrows from `C`, and
`B↔C` borrows from `A`) while `fixed_B` never changes. A splitter with no
non-fixed pane on one side (e.g. `[fixed_A, B]` or `[A, fixed_B]`) is locked.
Even a movable splitter is clamped so the resized panes stay within their
`[min, max]` ranges. `SplitView(movable=False)` locks every splitter in that
split; the default `movable=None` auto-detects.

If a split is given more space than its fixed/maxed children can use, the
leftover is filled by an implicit `SpacerView`.

`SceneView` defaults to a 120 px minimum on both axes, so a scene pane can never
be collapsed to nothing (override `min_width`/`min_height`, or pass `None` to
disable the floor). A **fixed** splitter draws a thin line; a **movable** one
draws a filled bar.

## Any Number of Splits

A single `SplitView` lays out **any number** of children along one axis — three
panes make two splitters, four panes make three, and so on (N panes → N − 1
splitters). No need to nest binary splits to get a 3+ way row or column:

```python
SplitView(
    orientation="horizontal",
    sizes=[Size.percent(35), Size.percent(30), Size.percent(35)],
    children=[SceneView("left"), SceneView("middle"), SceneView("right")],
)
```

Each divider between neighboring panes is independently draggable when a
non-fixed pane sits on each side of it. `sizes`, when given, needs one entry
per child. See `py/examples/viz/ui/layout/multi_split.py` for a runnable
three-pane example.

## Stacks and Controls

A `StackView` lays children out in normal flow (no splitters):

```python
StackView("vertical", [SliderView("s", label="Radius"), ButtonView("b", label="Go")])  # column
StackView("horizontal", [...])                                                          # row
StackView("wrap", [...])                                                                # row, wraps to new lines
```

Controls are just views. `SliderView` / `ButtonView` / `DropdownView` each render
one HTML control and send its value back through `on_change` / `on_click`
handlers (registered automatically when the layout is set):

```python
async def on_reset(_value, _event):
    print("reset")

GroupView(
    "Actions",
    [
        SliderView("radius", label="Radius", min=0.1, max=5.0, value=2.0),
        ButtonView("btn_reset", label="Reset view", on_click=on_reset),
    ],
)
```

`GroupView` is a `StackView` with a title bar (and collapse toggle); by default it
stacks its children vertically.

### Spacing, alignment, and flexible children

`StackView`, `GroupView`, and `ToolbarView` accept three layout-policy keywords:

- `gap` — spacing between children in pixels. `None` uses the default `4` px;
  `0` removes the spacing.
- `align` — cross-axis alignment: `"start"`, `"center"`, `"end"`, or
  `"stretch"` (default).
- `justify` — main-axis packing: `"start"` (default), `"center"`, `"end"`,
  `"space-between"`, `"space-around"`, or `"space-evenly"`.

`direction`, `align`, and `justify` also accept the `EStackDirection`,
`EStackAlign`, and `EStackJustify` enums (the same names with an `E` prefix);
the plain strings above remain valid and equivalent.

A child's `preferred_*` along the container's **main** axis maps to CSS flex
(`flex: <grow> <shrink> <basis>`):

| `preferred_<main>`      | flex        | meaning                                  |
|-------------------------|-------------|------------------------------------------|
| `None` / `Size.auto()`  | `0 1 auto`  | natural size, may shrink to `min`        |
| `Size.fr(n)`            | `n 1 0`     | grow to fill leftover, weighted by `n`   |
| `Size.px(v)`            | `0 0 <v>px` | fixed basis, no grow/shrink              |
| `Size.percent(v)`       | `0 0 <v>%`  | fixed basis, no grow/shrink              |

`min_*`/`max_*` still clamp the result (applied as CSS `min-*`/`max-*`). For
`fr`, the container also sets `min-<main>` to `0` when the child has no
explicit `min_<main>`, so a growing child can shrink below its content size.
Cross-axis "fill" is the container's `align` (`stretch` by default), matching
HTML's `align-items`.

```python
StackView(
    "horizontal",
    [
        TextAreaView("notes", label="Notes", preferred_width=Size.fr(1)),
        ButtonView("send", label="Send"),
    ],
    gap=8,
)
```

### Horizontal stacks & toolbars

`StackView("horizontal", ...)` lays its children side by side, so it doubles as a
**toolbar**; a horizontal stack nests inside a vertical stack to any depth:

```python
toolbar = StackView(
    "horizontal",
    [
        ButtonView("btn_fit", label="Fit camera", on_click=on_fit),
        ButtonView("btn_reset", label="Reset view", on_click=on_reset),
        DropdownView("dd_mode", label="Mode", options=["Wire", "Solid"], value="Wire"),
    ],
)

controls = StackView(
    "vertical",
    [
        toolbar,                                                       # toolbar row
        SliderView("radius", label="Radius", min=0.1, max=5.0, value=2.0),
    ],
)
```

Add `scrollable=True` to a toolbar row to scroll horizontally instead of
clipping when it is too narrow. See `py/examples/viz/ui/controls/toolbar.py` for a
runnable toolbar example.

### ToolbarView

`ToolbarView` is a dedicated horizontal toolbar: a `StackView("horizontal", ...)`
with a thin border and an inner margin, plus one setting to align its controls
left / right / block-centered / equally spaced:

```python
ToolbarView(
    [ButtonView("cut", label="Cut"), ButtonView("copy", label="Copy"), ButtonView("paste", label="Paste")],
    gap=8,
    justify=EStackJustify.SPACE_EVENLY,
)
```

- `margin` — the inner spacing between the border and the controls (a `Size`,
  default `Size.px(6)`; `None` removes it).
- `border` — whether to draw the thin outline (default `True`).
- `gap` — spacing between the controls (px, default `None` → `4`).
- `align` — vertical alignment of the controls (`EStackAlign.CENTER` by default).
- `justify` — horizontal placement of the controls; the four toolbar alignments
  are `EStackJustify.START` (left), `END` (right), `CENTER` (block-centered),
  and `SPACE_EVENLY` (equally spaced).

See `py/examples/viz/ui/controls/toolbar.py` for a four-pane example showing all four
alignments.

## Overlays

A `SceneView` can host overlay views that float over its canvas, anchored by each
child's `position` (an `EAnchor` — a corner such as `top-right`, or a centered
edge such as `top` / `bottom` / `left` / `right`):

```python
SceneView(
    "main",
    overlay=[GroupView("Legend", [ButtonView("btn", label="…")], position="top-left")],
)
```

## Per-Pane Camera

`SceneView(scene, camera=…)` gives a single pane a different **initial** camera
than the scene's own camera (or the auto-fit default). This is how the same
scene is shown in several panes from different viewpoints:

```python
from pytanga.viz import CameraConfig3d

layout = SplitView(
    "horizontal",
    [
        SceneView("main", camera=CameraConfig3d(position=(0, 0, 8), target=(0, 0, 0))),
        SceneView("main", camera=CameraConfig3d(position=(8, 0, 0), target=(0, 0, 0))),
    ],
)
```

`camera` accepts a `CameraConfig` (or a `View2DConfig` / `View3dConfig`, which is
converted). Each pane still keeps its **own** orbit/zoom/pan, so the camera is
only the starting viewpoint — the user can move each pane independently.
Passing `None` (the default) uses the scene's camera.

### Changing a pane's camera at runtime

Keep a reference to the `SceneView` and call `Visualizer.set_view_camera` from a
control handler to move a single pane without touching the scene (or the other
panes of that scene):

```python
top = SceneView("main")

async def on_topdown(_value, _event):
    viz.set_view_camera(top, CameraConfig3d(position=(0, 0, 8), target=(0, 0, 0)))

layout = SplitView("vertical", [
    top,
    GroupView("Controls", [ButtonView("btn", label="Top-down", on_click=on_topdown)]),
])
```

`SceneView` also accepts an optional `id` (auto-assigned `"svN"` when omitted);
it is the stable key used to route the runtime camera message to the matching
pane.

## Per-Pane Interaction

Pointer interaction (draggable `ActPoint`s, hover, click, scroll) is independent
per pane: each pane keeps its own camera, canvas, and interactive-object
registry, so an `ActPoint` in one pane can be dragged without affecting the
others. See `py/examples/viz/app/split_view_app.py` for a multi-pane example
with draggable points in two panes.

For 2D panes the orthographic frustum is computed from the **pane's** aspect
ratio (not the whole window's), so `CoordinateSystem` plots keep their correct
scale inside a split.

## Building a Layout

```python
from pytanga.geometry import Point, Sphere
from pytanga.viz import (
    ButtonView, GroupView, SceneView, Size, SliderView, SplitView, Visualizer,
)

viz = Visualizer()

# Main scene (default name "") — content in the top pane.
viz.add(Sphere(Point(0, 0, 0), radius=2), color="#4488ff", opacity=0.3)

side = viz.scene("side")
detail = viz.scene("detail")
side.add(Point(2, 0, 0), color="#44ff44")
detail.add(Sphere(Point(0, 1, 0), radius=1), color="#ffcc00", opacity=0.8)

layout = SplitView(
    orientation="horizontal",
    children=[
        GroupView(
            "Actions",
            [
                SliderView("radius", label="Radius", min=0.1, max=5.0, value=2.0),
                ButtonView("btn_fit", label="Fit camera"),
            ],
        ),
        SplitView(
            orientation="vertical",
            sizes=[Size.percent(70), Size.percent(30)],
            children=[
                SceneView(""),
                SplitView(
                    orientation="horizontal",
                    children=[SceneView("side"), SceneView("detail")],
                ),
            ],
        ),
    ],
)

viz.show(layout=layout)
viz.wait()
```

`SceneView("")` references the **main** scene (the default scene named `""`).
`viz.show(layout=...)` (or `viz.run(layout=...)`) registers the layout and opens
it under a single URL (`/?view=<name>`, default name `""`).

## See Also

- [Multi-Scene](multi-scene.md) — named scenes and their per-scene URLs
- [Visualizer API](visualizer.md) — the full `Visualizer` method reference
- [Animation](animation.md) — frame streaming and keyframe timelines
