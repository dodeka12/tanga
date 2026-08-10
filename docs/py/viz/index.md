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

viz = Visualizer()
viz.add(Point(1, 2, 3), color="#ff4444")
viz.add(Sphere(Point(0, 0, 0), radius=2.5), wireframe=True, opacity=0.4)
viz.add(Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1)), opacity=0.3)
viz.run()  # Opens browser, blocks until Ctrl+C
```

### Multiple Scenes

```python
# Create additional named scenes
details = viz.scene("details")
details.add(Sphere(Point(0, 0, 0), radius=2), opacity=0.3)
details.set_title("Close-up Detail")

# Side-by-side display in Jupyter
viz.display_row(
    (viz.scene(""), None),        # main scene
    (details, "browser-right"),   # named scene
)
```

## Topics

| Guide | What you will learn |
|-------|---------------------|
| [Visualizer API](visualizer.md) | `Visualizer` class, constructor, `add()`, MV input, multi-scene support, server lifecycle |
| [Camera & Controls](camera.md) | `CameraConfig`, auto-fit vs explicit vs partial camera, orbit controls, Ctrl+S screenshots |
| [Style System](styles.md) | `*Style` dataclasses, `default_styles`, `set_default_color()`, `CrossHairPointStyle` |
| [Labels](labels.md) | `Label` dataclass, `LabelStyle`, local-frame positioning, `update_label()` |
| [PointPath](point-path.md) | Connected line segments, object trails, per-point colors, FIFO capping, gradient utilities |
| [Title & Annotation](title-annotation.md) | Title overlay, Markdown annotation panel, LaTeX math with KaTeX |
| [Animation](animation.md) | Frame streaming, keyframe tweening (`animate_to`), scene-aware `Timeline` sequencer |
| [Export & Capture](export.md) | `SceneExporter`: HTML/glTF/figure export, screenshots, video capture, animated HTML |
| [Jupyter Notebooks](jupyter.md) | Auto-detection, inline iframe, multi-scene `display_row()`, `start()`/`flush()`/`stop()` pattern |
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
| [`demo_camera_config.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_camera_config.py) | Auto-fit, explicit, and partial camera modes |
| [`demo_custom_defaults.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_custom_defaults.py) | Global default styles, per-call overrides |
| [`demo_operators.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_operators.py) | Rotor, Translator, Motor, Dilator visualization |
| [`demo_animation_orbit.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_animation_orbit.py) | Frame-by-frame animation at ~60 FPS |
| [`demo_animation_timeline.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_animation_timeline.py) | Keyframe timeline with fade-in and move |
| [`demo_title_annotation.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_title_annotation.py) | Title overlay and Markdown + LaTeX annotation |
| [`demo_screenshot.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_screenshot.py) | Programmatic PNG screenshot |
| [`demo_multi_scene.py`](https://github.com/dodeka12/tanga/blob/main/dev/src/test_viz_multi_scene.py) | Multi-scene viewer with browser targeting and navigation |
| [`demo_export_html.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_export_html.py) | Self-contained HTML and glTF export |
| [`demo_export_figure.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_export_figure.py) | Presentation figure export with `FigureStyle` |
| [`demo_animated_export.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/demo_animated_export.py) | Animated HTML export with JS playback engine |
| [`two_spheres_interact.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/two_spheres_interact.py) | `VisualizerApp` with IPNS spheres, slider, dropdown, reset button |
| [`two_body_gravity.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/two_body_gravity.py) | Gravitational two-body simulation using `Point`/`Direction` arithmetic |

## Dependencies

`aiohttp` (Python). Three.js, OrbitControls, marked, KaTeX, and html2canvas
load automatically from CDN in the browser — no additional installs needed.

```bash
uv add aiohttp