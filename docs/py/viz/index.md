# 3D Visualizer

The `pytanga.viz` submodule provides interactive 3D visualization of geometric
entities in a web browser using **Three.js** and WebGL. Users can rotate, pan,
and zoom the camera, apply per-entity styles, animate geometric constructions,
and export self-contained HTML or glTF files.

## Architecture

The visualizer uses a lightweight Python WebSocket server (aiohttp) that pushes
JSON scene updates to a static HTML/JS frontend. Three.js, KaTeX, and marked
load from CDN — zero frontend build step, no npm, no bundler.

## Quick Start

```python
from pytanga.viz import SphereStyle, Visualizer
from pytanga.geometry import Point, Sphere, Plane, Direction

with Visualizer() as viz:  # clear + show on entry, flush on exit
    viz(Point(1, 2, 3), color="#ff4444")
    viz(Sphere(Point(0, 0, 0), radius=2.5), style=SphereStyle(wireframe=True), opacity=0.4)
    viz(Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1)), opacity=0.3)
```

### Multiple Scenes

A `Visualizer` owns one server; named scenes are just additional URL paths on
that server (`http://localhost:8765/<name>`). You get a scene handle with
`viz.scene("name")` and use it like the main visualizer — `add()`, styles,
labels, controls, and animation all work per scene:

```python
from pytanga.geometry import Point, Sphere
from pytanga.viz import Visualizer

viz = Visualizer(reuse_existing=False)

overview = viz.scene("overview")
detail = viz.scene("detail")

with overview:  # reset + show() this scene, then flush on exit
    overview.set_title("Overview")
    overview.add(Sphere(Point(0, 0, 0), radius=2), color="#4488ff", opacity=0.3)

with detail:    # reset + show() this scene in its own tab, then flush
    detail.set_title("Detail")
    detail.add(Sphere(Point(2, 1, 0), radius=1), color="#ffcc00", opacity=0.8)

viz.wait()  # keep running until Ctrl+C
```

`VizSceneHandle` is a context manager, so `with scene:` clears the scene,
opens it in a browser, and flushes on exit — the same ergonomics as the main
`Visualizer`.

!!! info "Does `show()` open a new tab?"
    With `reuse_existing=False`, yes — each scene's `show()` opens a fresh tab
    for that scene's URL immediately.

    The default is `reuse_existing=True`, where `show()` prints a prompt and
    waits for an already-open tab to reconnect (press Enter to open a new tab
    instead of waiting). Pass `Visualizer(reuse_existing=False)` for the
    open-a-tab-per-scene behaviour shown above.

    In Jupyter, `show()` renders inline instead of opening a browser tab — use
    `viz.display_row((overview, None), (detail, None))` for side-by-side views.

Runnable example: [`multi_scene.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/scenes/multi_scene.py).

## Use Cases

- **Python script** — [Use Cases — Scripts](use-cases-scripts.md)
    - **One-off demo**
        - **No animation** — context manager (`with viz: …`), see [Interactive Visualizer](use-cases-scripts.md#interactive-visualizer)
        - **Animation** — `animate(auto_clear=True)` for quick short scripts, see [Animation](use-cases-scripts.md#animation)
    - **Performance / long-running**
        - **No animation** — build the scene, then `show()` + `wait()`
        - **Animation** — pre-create with `viz(...)` and update `.entity` in place, see [Frame streaming](use-cases-scripts.md#frame-streaming-python-driven)
    - **Interactive** — [VisualizerApp](visualizerapp/app.md)
    - **Static snapshot**
        - **Single snapshot** — `viz.export_snapshot("scene.html")` (standalone HTML file), see [Standalone HTML](export/html.md)
        - **Animation recording** — record a loop with `start_animation_recording()` and export standalone animated HTML, see [Animated HTML](export/html.md#animated-html)
- **Jupyter notebook** — [Use Cases — Notebooks](use-cases-notebooks.md)
    - **One-off demo**
        - **No animation** — context manager, see [Interactive Visualizer](use-cases-notebooks.md#interactive-visualizer)
        - **Animation** — `animate(auto_clear=True)`, see [Animation](use-cases-notebooks.md#animation)
    - **Performance / long-running**
        - **No animation** — idempotent `show()`/`display()` re-renders
        - **Animation** — pre-create with `viz(...)` and update `.entity` in place, see [Animation](use-cases-notebooks.md#animation)
    - **Interactive** — [VisualizerApp](visualizerapp/app.md)
    - **Static snapshot**
        - **Single snapshot** — `viz.display_snapshot()` (embedded inline), see [Serverless Display](jupyter/static.ipynb)
        - **Animation recording** — record a loop and export standalone animated HTML, see [Animated HTML](export/html.md#animated-html)

## Topics

| Guide | What you will learn |
|-------|---------------------|
| [Use Cases — Scripts](use-cases-scripts.md) | Interactive viewer, animation, and export in plain Python scripts |
| [Use Cases — Notebooks](use-cases-notebooks.md) | Interactive viewer (re-run), animation, and export in Jupyter |
| [Visualizer App](visualizerapp/app.md) | `VisualizerApp` base class for interactive apps with controls and a managed lifecycle |
| [Visualizer API](visualizer/visualizer.md) | `Visualizer` class, constructor, `add()`, MV input, multi-scene support, server lifecycle |
| [Camera & Controls](visualizer/camera.md) | `CameraConfig2d`/`CameraConfig3d`, `View2DConfig`, `View3dConfig`, auto-fit vs explicit, orbit controls, Ctrl+S screenshots |
| [Axes & Grid](scene-objects/axes-grid.md) | `Axis`, `Grid`, `Axes3D`, `Axes2D` as explicit scene objects, intervals, value labels, defaults |
| [Coordinate System](scene-objects/coordinate-system.md) | Plotting helper: axes/grid/plane in one group, scales, `size`/`align`/`axis_origin`, live trails |
| [Style System](styles/styles.md) | `*Style` dataclasses, `styles`, `set_default_color()`, `CrossHairPointStyle` |
| [Texture Labels](styles/texture-labels.md) | Text, KaTeX formulas, and mixed content on entity surfaces (Sphere, Plane) |
| [Labels](styles/labels.md) | `Label` dataclass, `LabelStyle`, local-frame positioning, `update_label()` |
| [Scene Graph & Transforms](visualizer/scene-graph.md) | `VizGroup`, `VizObjectRef`, parent/child hierarchy, transforms, aspect patches |
| [PointPath](scene-objects/point-path.md) | Connected line segments, object trails, per-point colors, FIFO capping, gradient utilities |
| [Title & Annotation](styles/title-annotation.md) | Title overlay, Markdown annotation panel, LaTeX math with KaTeX |
| [Animation](visualizer/animation.md) | Frame streaming, keyframe tweening (`animate_to`), scene-aware `Timeline` sequencer |
| [Export](export/index.md) | Standalone HTML (static + animated), glTF, figure snippets, screenshots, MP4 video |
| [Jupyter Notebooks](jupyter/index.md) | Auto-detection, inline iframe, multi-scene `display_row()`, `start()`/`flush()`/`stop()` pattern |
| [Object Interaction](visualizer/object-interaction.md) | Pointer-based 3D object interaction: click, drag, scroll; `Camera` projection; event dispatch |
| [Active Elements](scene-objects/active-elements/index.md) | Simplified high-level API: `ActPoint` and future self-registering interactive entities |
| [Controls](visualizerapp/controls.md) | Sliders, dropdowns, buttons, groups; scene-scoped controls |
| [SDF Viewer](sdf-viewer.md) | Ray-marched signed-distance-function viewer: analytic + algebra paths, distance/opacity functions, boolean combine modes |

## Example Scripts

All viz examples live under `py/examples/viz/`, grouped by topic, and can be
run with:

```
uv run python py/examples/viz/<folder>/<script>.py
```

### Camera

- [`camera/2d_view.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/camera/2d_view.py) — `View2DConfig` with min/max world bounds
- [`camera/3d_plane.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/camera/3d_plane.py) — `View3dConfig` with a tilted plane and a custom `up`
- [`camera/modes.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/camera/modes.py) — auto-fit, explicit 3D, 2D, and plane-based camera modes
- [`camera/fit_2d.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/camera/fit_2d.py) — 2D fit-camera keeps the axes/grid undistorted
- [`camera/axes_grid_2d.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/camera/axes_grid_2d.py) — `View2DConfig` + `Axes2D` + `Grid` basics in 2D

### Plotting

- [`plotting/axes_custom.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/plotting/axes_custom.py) — custom `Axis` intervals, value labels, and `Grid`
- [`plotting/cs_annotations.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/plotting/cs_annotations.py) — annotations in a `CoordinateSystem` data frame
- [`plotting/log_plot.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/plotting/log_plot.py) — logarithmic plotting with `CoordinateSystem`
- [`plotting/plot_3d.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/plotting/plot_3d.py) — a plot on a tilted background plane in 3D
- [`plotting/pendulum_plot.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/plotting/pendulum_plot.py) — a swinging pendulum with a live angle-vs-time plot

### Entities

- [`entities/all_entities.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/entities/all_entities.py) — all entity types in one scene
- [`entities/viz_entities.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/entities/viz_entities.py) — the visualization-only `Cylinder` and `Arc` entities
- [`entities/operators.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/entities/operators.py) — Rotor, Translator, Motor, Dilator visualization
- [`entities/multivector.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/entities/multivector.py) — MV input from PGA3 and N3, OPNS vs IPNS

### Labels

- [`labels/basic.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/labels/basic.py) — labels with custom styling, dynamic update, removal
- [`labels/texture_plane.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/labels/texture_plane.py) — align modes (stretch/fit/repeat) and mixed content on planes
- [`labels/texture_sphere.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/labels/texture_sphere.py) — plain text, KaTeX, and mixed content on spheres
- [`labels/title_annotation.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/labels/title_annotation.py) — title overlay and Markdown + LaTeX annotation

### Animation

- [`animation/orbit.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/animation/orbit.py) — frame-by-frame animation at ~60 FPS
- [`animation/timeline.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/animation/timeline.py) — keyframe timeline with fade-in and move
- [`animation/nested_sweep.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/animation/nested_sweep.py) — nested animation loops honoring Ctrl+C
- [`animation/point_path_trail.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/animation/point_path_trail.py) — moving point with a color-gradient trail
- [`animation/double_pendulum.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/animation/double_pendulum.py) — a chaotic double pendulum from nested `VizGroup`s
- [`animation/two_body_gravity.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/animation/two_body_gravity.py) — gravitational two-body simulation using `Point`/`Direction` arithmetic

### Interaction

- [`interaction/drag_point.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/interaction/drag_point.py) — interactive point dragging with four constraint planes (low-level API)
- [`interaction/act_point.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/interaction/act_point.py) — interactive point dragging with `ActPoint` convenience class
- [`interaction/two_spheres_interact.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/interaction/two_spheres_interact.py) — `VisualizerApp` with IPNS spheres, slider, dropdown, reset button

### Scenes

- [`scenes/scene_graph.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/scenes/scene_graph.py) — `VizGroup` + `VizObjectRef` transforms and compound animation
- [`scenes/nested_groups.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/scenes/nested_groups.py) — nested `VizGroup` hierarchies
- [`scenes/multi_scene.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/scenes/multi_scene.py) — two named scenes, each opened in its own browser tab via context managers
- [`scenes/split_view.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/scenes/split_view.py) — a single page showing multiple scenes in split panes

### Export

- [`export/html_export.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/export/html_export.py) — self-contained HTML and glTF export
- [`export/figure.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/export/figure.py) — presentation figure export with `FigureStyle`
- [`export/animated.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/export/animated.py) — animated HTML export with JS playback engine
- [`export/animated_camera_2d.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/export/animated_camera_2d.py) — 2D animated export with a moving camera
- [`export/animated_camera_3d.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/export/animated_camera_3d.py) — 3D animated export with a moving camera
- [`export/screenshot.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/export/screenshot.py) — programmatic PNG screenshot

### Styling

- [`styling/custom_defaults.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/styling/custom_defaults.py) — global default styles, per-call overrides

Jupyter notebook examples live under `py/examples/ga/jupyter/` — see
[Use Cases — Notebooks](use-cases-notebooks.md).

## Dependencies

`aiohttp` (Python). Three.js, OrbitControls, marked, KaTeX, and html2canvas
load automatically from CDN in the browser — no additional installs needed.

```bash
uv add aiohttp
```
