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
from pytanga.viz import Visualizer
from pytanga.geometry import Point, Sphere, Plane, Direction

with Visualizer() as viz:  # clear + show on entry, flush on exit
    viz(Point(1, 2, 3), color="#ff4444")
    viz(Sphere(Point(0, 0, 0), radius=2.5), wireframe=True, opacity=0.4)
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

Runnable example: [`demo_multi_scene.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_multi_scene.py).

## Use Cases

- **Python script** — [Use Cases — Scripts](use-cases-scripts.md)
    - **One-off demo**
        - **No animation** — context manager (`with viz: …`), see [Interactive Visualizer](use-cases-scripts.md#interactive-visualizer)
        - **Animation** — `animate(auto_clear=True)` for quick short scripts, see [Animation](use-cases-scripts.md#animation)
    - **Performance / long-running**
        - **No animation** — build the scene, then `show()` + `wait()`
        - **Animation** — pre-create with `viz(...)` and update `.entity` in place, see [Frame streaming](use-cases-scripts.md#frame-streaming-python-driven)
    - **Interactive** — [VisualizerApp](app.md)
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
    - **Interactive** — [VisualizerApp](app.md)
    - **Static snapshot**
        - **Single snapshot** — `viz.display_snapshot()` (embedded inline), see [Serverless Display](jupyter.md#serverless-display-display_snapshot)
        - **Animation recording** — record a loop and export standalone animated HTML, see [Animated HTML](export/html.md#animated-html)

## Topics

| Guide | What you will learn |
|-------|---------------------|
| [Use Cases — Scripts](use-cases-scripts.md) | Interactive viewer, animation, and export in plain Python scripts |
| [Use Cases — Notebooks](use-cases-notebooks.md) | Interactive viewer (re-run), animation, and export in Jupyter |
| [Visualizer App](app.md) | `VisualizerApp` base class for interactive apps with controls and a managed lifecycle |
| [Visualizer API](visualizer.md) | `Visualizer` class, constructor, `add()`, MV input, multi-scene support, server lifecycle |
| [Camera & Controls](camera.md) | `CameraConfig2d`/`CameraConfig3d`, `View2DConfig`, `View3dConfig`, auto-fit vs explicit, orbit controls, Ctrl+S screenshots |
| [Axes & Grid](axes-grid.md) | `Axis`, `Grid`, `Axes3D`, `Axes2D` as explicit scene objects, intervals, value labels, defaults |
| [Style System](styles.md) | `*Style` dataclasses, `styles`, `set_default_color()`, `CrossHairPointStyle` |
| [Texture Labels](texture-labels.md) | Text, KaTeX formulas, and mixed content on entity surfaces (Sphere, Plane) |
| [Labels](labels.md) | `Label` dataclass, `LabelStyle`, local-frame positioning, `update_label()` |
| [Scene Graph & Transforms](scene-graph.md) | `VizGroup`, `VizObjectRef`, parent/child hierarchy, transforms, aspect patches |
| [PointPath](point-path.md) | Connected line segments, object trails, per-point colors, FIFO capping, gradient utilities |
| [Title & Annotation](title-annotation.md) | Title overlay, Markdown annotation panel, LaTeX math with KaTeX |
| [Animation](animation.md) | Frame streaming, keyframe tweening (`animate_to`), scene-aware `Timeline` sequencer |
| [Export](export/index.md) | Standalone HTML (static + animated), glTF, figure snippets, screenshots, MP4 video |
| [Jupyter Notebooks](jupyter.md) | Auto-detection, inline iframe, multi-scene `display_row()`, `start()`/`flush()`/`stop()` pattern |
| [Object Interaction](object-interaction.md) | Pointer-based 3D object interaction: click, drag, scroll; `Camera` projection; event dispatch |
| [Active Elements](active-elements/index.md) | Simplified high-level API: `ActPoint` and future self-registering interactive entities |
| [Interactive Controls](interactive.md) | `VisualizerApp` base class, sliders, dropdowns, buttons, groups, lifecycle hooks |

## Example Scripts

All viz examples live under `py/examples/viz/` and can be run with:

```
uv run python py/examples/viz/<script>.py
```

| Script | Topic |
|--------|-------|
| [`demo_all_entities.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_all_entities.py) | All entity types in one scene |
| [`demo_labels.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_labels.py) | Labels with custom styling, dynamic update, removal |
| [`demo_mv_visualization.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_mv_visualization.py) | MV input from PGA3 and N3, OPNS vs IPNS |
| [`demo_camera_config.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_camera_config.py) | Auto-fit, explicit 3D, 2D, and plane-based camera modes |
| [`demo_camera_2d.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_camera_2d.py) | `View2DConfig` with min/max world bounds |
| [`demo_camera_3d_plane.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_camera_3d_plane.py) | `View3dConfig` with a tilted plane and a custom `up` |
| [`demo_camera_axes_grid_2d.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_camera_axes_grid_2d.py) | `View2DConfig` + `Axes2D` + `Grid` basics in 2D |
| [`demo_axes_custom.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_axes_custom.py) | Custom `Axis` intervals, value labels, and `Grid` |
| [`demo_custom_defaults.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_custom_defaults.py) | Global default styles, per-call overrides |
| [`demo_operators.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_operators.py) | Rotor, Translator, Motor, Dilator visualization |
| [`demo_animation_orbit.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_animation_orbit.py) | Frame-by-frame animation at ~60 FPS |
| [`demo_animation_timeline.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_animation_timeline.py) | Keyframe timeline with fade-in and move |
| [`demo_scene_graph.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_scene_graph.py) | `VizGroup` + `VizObjectRef` transforms and compound animation |
| [`demo_title_annotation.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_title_annotation.py) | Title overlay and Markdown + LaTeX annotation |
| [`demo_screenshot.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_screenshot.py) | Programmatic PNG screenshot |
| [`demo_multi_scene.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_multi_scene.py) | Two named scenes, each opened in its own browser tab via context managers |
| [`demo_export_html.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_export_html.py) | Self-contained HTML and glTF export |
| [`demo_export_figure.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_export_figure.py) | Presentation figure export with `FigureStyle` |
| [`demo_animated_export.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_animated_export.py) | Animated HTML export with JS playback engine |
| [`demo_texture_label_sphere.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_texture_label_sphere.py) | Plain text, KaTeX, and mixed content on spheres |
| [`demo_texture_label_plane.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_texture_label_plane.py) | Align modes (stretch/fit/repeat) and mixed content on planes |
| [`two_spheres_interact.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/two_spheres_interact.py) | `VisualizerApp` with IPNS spheres, slider, dropdown, reset button |
| [`demo_drag_point.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_drag_point.py) | Interactive point dragging with four constraint planes (low-level API) |
| [`demo_act_point.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_act_point.py) | Interactive point dragging with `ActPoint` convenience class |
| [`two_body_gravity.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/two_body_gravity.py) | Gravitational two-body simulation using `Point`/`Direction` arithmetic |

Jupyter notebook examples live under `py/examples/jupyter/` — see
[Use Cases — Notebooks](use-cases-notebooks.md).

## Dependencies

`aiohttp` (Python). Three.js, OrbitControls, marked, KaTeX, and html2canvas
load automatically from CDN in the browser — no additional installs needed.

```bash
uv add aiohttp
```
