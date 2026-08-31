# Split Views

Split views let a **single browser page** show multiple scenes (or control
panels) in separate panes, arranged with horizontal or vertical splits. Panes
can be nested to any depth, and each split's divider is draggable unless a pane
on either side has a fixed size. The existing per-scene URLs keep working
unchanged — a split view is just an additional layout served at one URL
(`/?view=<name>`).

## The View Hierarchy

Everything in a layout is a `View`. Two containers arrange their children, and
the leaves render content:

| Class | Purpose |
|-------|---------|
| `View` | Base for every pane/container. Exposes per-axis preferred/min/max sizes. |
| `SplitView` | A container that lays children out along one axis with draggable splitters. |
| `StackView` | A flex container that stacks children vertically, horizontally, or wraps. |
| `SceneView` | A pane that renders a named scene (`scene` name or handle), optionally with overlay views. |
| `GroupView` | A titled `StackView` (panel chrome) for grouping control views; usable as a pane or a scene overlay. |
| `SliderView` / `ButtonView` / `DropdownView` / `TableView` | A single HTML control rendered as a `View`. |
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

## Fixed vs. Movable Splitters

A view is **fixed** along an axis when its `min` and `max` are equal
(`View.fixed_x` / `View.fixed_y`). A splitter is draggable only when **both**
neighbors are non-fixed along the split axis; a fixed neighbor pins it. Even a
movable splitter is clamped so neither neighbor leaves its `[min, max]` range.
`SplitView(movable=False)` locks every splitter in that split; the default
`movable=None` auto-detects.

If a split is given more space than its fixed/maxed children can use, the
leftover is filled by an implicit `SpacerView`.

`SceneView` defaults to a 120 px minimum on both axes, so a scene pane can never
be collapsed to nothing (override `min_width`/`min_height`, or pass `None` to
disable the floor). A **fixed** splitter draws a thin line; a **movable** one
draws a filled bar.

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

## Overlays

A `SceneView` can host overlay views that float over its canvas, anchored by each
child's `position` (`top-left` / `top-right` / `bottom-left` / `bottom-right`):

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
