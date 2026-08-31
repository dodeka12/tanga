# Multi-Scene

A single `Visualizer` owns one HTTP + WebSocket server, but it can manage
multiple **named scenes** at the same time. Each scene is served at its own URL
path on that server, runs concurrently in memory, and can be shown in its own
browser tab or inline Jupyter iframe. This enables reveal.js presentations,
side-by-side notebook comparisons, and control-driven scene switching without
spinning up multiple servers on different ports.

## The Scene Model

| Concept | Description |
|---------|-------------|
| Main scene | The built-in scene named `""`, served at `/`. The plain `Visualizer` API targets it. |
| Named scene | Created with `viz.scene("name")`, served at `/<name>`. |
| `VizSceneHandle` | Proxy returned by `viz.scene()` that scopes every operation to a single scene. |

The main scene always exists. Named scenes are created lazily the first time
`viz.scene("name")` is called; the call is idempotent and returns a handle to
the same underlying scene on later calls.

Scene names may contain slashes for grouping, e.g. `"slides/intro"`.

Each scene is an independent `Scene` object with its own entities, styles,
controls, camera, title, and annotation. Named scenes inherit the visualizer's
default styles, `space_dim`, and `background_color`, and each receives its own
default axes/grid (controlled by the `add_default_axes` / `add_default_grid`
constructor flags).

For a plot-only scene backed by a `CoordinateSystem` — which draws its own,
correctly-scaled grid and axes — opt out of the default placeholder grid/axes at
creation:

```python
plots = viz.scene("plots", add_axes=False, add_grid=False)
```

The main scene `""` is created in `__init__`, so suppress its defaults with the
`add_default_axes` / `add_default_grid` constructor flags instead.

## Creating and Using Scenes

```python
from pytanga.geometry import Point, Sphere
from pytanga.viz import Visualizer

viz = Visualizer()

overview = viz.scene("overview")
detail = viz.scene("detail")

overview.add(Sphere(Point(0, 0, 0), radius=2), color="#4488ff", opacity=0.3)
detail.add(Sphere(Point(2, 1, 0), radius=1), color="#ffcc00", opacity=0.8)
```

A `VizSceneHandle` exposes the same API as `Visualizer`, scoped to its scene:

| Method | Description |
|--------|-------------|
| `add(obj, *, ...)` | Add an entity, operator, MV, or label to this scene |
| `new(obj, *, ...)` | Like `add()`, but returns a `VizObjectRef` |
| `add_group(name)` | Create a scene-graph group, returning a `VizObjectRef` |
| `update(entity_id, **props)` | Update rendering properties |
| `update_style(entity_id, style)` | Update an entity's style |
| `update_entity(entity_id, obj)` | Replace an entity's geometry |
| `update_label(object_id, *, text, style)` | Update a label's text/style |
| `remove(entity_id)` | Remove an entity |
| `clear()` | Remove all entities from this scene |
| `flush(*, fit_camera=False)` | Push this scene's dirty state to its viewers |
| `set_title(title)` | Update the title overlay |
| `set_annotation(text, *, style)` | Update the annotation panel |
| `set_camera(camera)` | Update the camera at runtime |
| `add_slider` / `add_dropdown` / `add_button` | Add interactive controls |
| `add_control_group` / `remove_control` / `remove_control_group` / `clear_controls` | Control management |
| `set_interaction` / `on_interaction` | Low-level pointer interaction |
| `animate_to(entity_id, *, ...)` | Animate an entity in this scene |
| `timeline()` | Create a scene-aware `Timeline` |
| `animate(*, fps, stop_key, stop_modifiers, auto_clear)` | Frame loop scoped to this scene |
| `interrupted()` / `sleep_ms(ms)` | Interrupt-aware pacing |
| `enable_server_stop_key(...)` | Opt this scene into the global browser stop key |
| `navigate_to(scene_name)` | Navigate browsers viewing *this* scene to another scene |
| `show()` / `open_browser()` / `display()` | Show this scene (browser tab or Jupyter iframe) |
| `display_snapshot()` / `export_snapshot()` / `export_figure()` / `export_glb()` | Static / export output |

Properties: `name`, `url`, `scene`, `styles`.

## URL Structure

The server serves `viewer.html` at `/` and every scene path; the frontend reads
`window.location.pathname` and requests that scene over WebSocket.

| Scene | URL |
|-------|-----|
| Main (`""`) | `http://localhost:8765/` |
| `"overview"` | `http://localhost:8765/overview` |
| `"slides/intro"` | `http://localhost:8765/slides/intro` |

`viz.url` is the base URL; `scene.url` is the full URL for that scene (equal to
`viz.url` for the main scene).

## Showing Scenes

`VizSceneHandle` is a context manager, mirroring `Visualizer`: on entry it
resets the scene and calls `show()`, then `flush()`es on exit.

```python
with overview:  # reset + show the overview tab, flush on exit
    overview.set_title("Overview")
    overview.add(Sphere(Point(0, 0, 0), radius=2), color="#4488ff", opacity=0.3)

with detail:    # reset + show the detail tab, flush on exit
    detail.set_title("Detail")
    detail.add(Sphere(Point(2, 1, 0), radius=1), color="#ffcc00", opacity=0.8)
```

Outside Jupyter, `show()` opens a browser tab. With the default
`reuse_existing=True`, `show()` waits for an already-open tab to reconnect;
pass `Visualizer(reuse_existing=False)` to open a fresh tab per scene
immediately.

Runnable example: [`multi_scene.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/scenes/multi_scene.py).

## Jupyter: Side-by-Side Scenes

In Jupyter, a `VizSceneHandle` renders inline as an iframe when it is the last
expression in a cell:

```python
overview  # inline <iframe> pointing at /overview
detail    # inline <iframe> pointing at /detail
```

For side-by-side layout in one cell, use `viz.display_row()`:

```python
viz.display_row(
    (overview, "left-browser"),
    (detail, "right-browser"),
    width="100%",
    height=500,
    gap=12,
)
```

Each tuple is a `(handle, viewer_name)` pair; the optional `viewer_name` is
passed as a `?viewer=` URL parameter and can be targeted later with
`navigate_to`. Pass `mode="static"` for serverless snapshots instead of live
views. See [Jupyter Notebooks](../jupyter/index.md) for details.

## Navigation

`viz.navigate_to()` redirects connected browser sessions to another scene URL:

```python
viz.navigate_to("")                                            # everyone -> main scene
viz.navigate_to("detail", target="scene:overview")             # browsers viewing overview -> detail
viz.navigate_to("slide2", target="browser:abc123")             # one browser -> slide2
viz.navigate_to("intro", target="viewer:presenter-laptop")     # named viewer -> intro
```

| Target | Matches |
|--------|---------|
| `"all"` | Every connected browser |
| `"scene:<name>"` | Browsers currently viewing scene `<name>` |
| `"browser:<id>"` | The single browser with that session id |
| `"viewer:<name>"` | Browsers whose `?viewer=` label is `<name>` |

`VizSceneHandle.navigate_to(name)` is shorthand for
`viz.navigate_to(name, target="scene:<this-scene>")` — navigate every browser
that is currently viewing this scene.

## Inspecting Scenes and Browsers

```python
viz.list_scenes()      # ['', 'overview', 'detail']
viz.list_browsers()    # [{'id': ..., 'scene': ..., 'remote_addr': ..., 'viewer_name': ...}, ...]
```

`list_browsers()` returns an empty list when the server is not running.

## Browser Identity and Control-Driven Switching

Every WebSocket connection receives a unique `browser_id` on handshake, and
every client-to-server message includes it. Control handlers receive a
`ControlEvent` whose `browser_id` attribute identifies the originating browser,
so a dropdown can navigate only the tab that triggered it:

```python
async def on_scene_change(selected_scene, event):
    if event.browser_id:
        viz.navigate_to(selected_scene, target=f"browser:{event.browser_id}")

viz.add_dropdown(
    "scene_selector",
    options=["overview", "detail"],
    value="overview",
    on_change=on_scene_change,
)
viz.flush()
```

Controls are per scene: the dropdown above belongs to whichever scene (or the
main visualizer) you attach it to.

## Scene-Aware Animation

Animation and timeline APIs are scoped to the scene handle:

```python
detail.timeline() \
    .animate_to("detail_point", position=(3, 2, 0), duration=1.5) \
    .play()

for dt in detail.animate(fps=30, auto_clear=True):
    detail.add(Point(...), color="#ff4444")
    detail.flush()
```

See [Animation](animation.md) for the full animation reference.

## Exporting a Scene

All export and static helpers are available through the handle:

```python
detail.export_snapshot("detail.html")
detail.export_glb("detail.glb")
detail.display_snapshot()  # serverless inline view
```

## Complete Example

[`multi_scene.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/scenes/multi_scene.py)
shows two named scenes, each opened in its own browser tab via context
managers:

```python
from pytanga.geometry import Point, Sphere
from pytanga.viz import Visualizer

viz = Visualizer(reuse_existing=False, title="Tanga — Multi-Scene")

overview = viz.scene("overview", enable_server_stop_key=True)
detail = viz.scene("detail")

with overview:
    overview.set_title("Overview")
    overview.add(Sphere(Point(0, 0, 0), radius=2), color="#4488ff", opacity=0.3)
    overview.add(Point(1, 1, 1), color="#ff4444")

with detail:
    detail.set_title("Detail")
    detail.add(Sphere(Point(2, 1, 0), radius=1), color="#ffcc00", opacity=0.8)

viz.wait()
```

## See Also

- [Visualizer API](visualizer.md) — the full `Visualizer` method reference
- [Animation](animation.md) — frame streaming and keyframe timelines
- [Jupyter Notebooks](../jupyter/index.md) — inline display and `display_row()`
- [Camera & Controls](camera.md) — per-scene `set_camera()`



