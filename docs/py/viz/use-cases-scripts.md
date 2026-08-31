# Use Cases — Python Scripts

Typical ways to run the visualizer from a plain Python script. For notebooks,
see [Use Cases — Notebooks](use-cases-notebooks.md); for the full API see
[Visualizer API](visualizer/visualizer.md).

## Interactive Visualizer

The simplest way to show a one-off scene is the context manager. It clears the
scene, shows it on entry, and flushes on exit — no server bookkeeping to
remember:

```python
from pytanga.geometry import Direction, Plane, Point, Sphere
from pytanga.viz import SphereStyle, Visualizer

viz = Visualizer(title="My Scene")

with viz:  # clear + show on entry, flush on exit
    viz(Point(1, 2, 3), color="#ff4444")
    viz(Sphere(Point(0, 0, 0), radius=2.5), style=SphereStyle(wireframe=True), opacity=0.3)
    viz(Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1)), opacity=0.25)
```

`viz(...)` is shorthand for `viz.new(...)` and returns a
`VizObjectRef`; `viz.add(...)` returns a plain entity id string instead.

For a script that must keep running, follow the block with `wait()`, or use the
equivalent `show()` + `wait()` pair:

```python
viz = Visualizer()
viz(Point(1, 2, 3), color="#ff4444")
viz.show()  # serve on port 8765 + open a browser tab
viz.wait()  # block until Ctrl+C; the server stops at interpreter exit
```

## Animation

Two strategies are available; see [Animation](visualizer/animation.md) for the full
reference.

### Frame streaming (Python-driven)

Pre-create the objects once with `viz(...)` and update them in place each
frame — only changed entities are pushed:

```python
import math
from pytanga.geometry import Point
from pytanga.viz import Visualizer

viz = Visualizer()
viz.show()  # open the viewer (browser tab in a script)
p = viz(Point(3, 0, 0), color="#ff4444")

angle = 0.0
for dt in viz.animate(fps=30):  # runs until Q / Ctrl+C
    angle += 3.0 * dt
    p.entity = Point(3 * math.cos(angle), 3 * math.sin(angle), 0)
    viz.flush()
```

### Add fresh objects per frame (`auto_clear`)

When you prefer to `add()` new objects every frame, pass `auto_clear=True` so
the previous frame's objects are removed automatically (anything added *before*
the loop persists). This is concise for **quick, short scripts** and one-off
demos, but **less performant** than updating in place above (each frame removes
and recreates the previous frame's objects):

```python
import math
from pytanga.geometry import Point
from pytanga.viz import Visualizer

viz = Visualizer()
viz.show()  # open the viewer
viz(Point(0, 0, 0), color="#ffffff")  # persists across frames

angle = 0.0
for dt in viz.animate(fps=30, auto_clear=True):
    angle += 3.0 * dt
    viz(Point(3 * math.cos(angle), 3 * math.sin(angle), 0), color="#ff4444")
    viz.flush()
```

### Keyframe tweening (browser-driven)

Smooth transitions without a Python loop:

```python
viz.animate_to(point_id, position=(5, 0, 0), duration=1.5, easing="ease-out")
```

Or sequence several with a `Timeline`:

```python
viz.timeline().wait(0.5).animate_to(p1, position=(3, 2, 0), duration=1.5).play()
```

## Export

Exports read directly from the in-memory scene — no server required:

```python
viz = Visualizer()
viz(Point(1, 2, 3), color="#ff4444")
viz(Sphere(Point(0, 0, 0), radius=2), opacity=0.3)

viz.export_snapshot("scene.html")   # self-contained HTML
viz.export_glb("scene.glb")         # glTF binary for Blender / <model-viewer>
viz.export_figure("figure.html")     # embeddable presentation snippet
```

To record an animation and embed it as a playable HTML file:

```python
from pytanga.viz import AnimStyle

recording = viz.start_animation_recording()
for frame in range(90):
    p.entity = Point(...)
    viz.flush()
    recording.capture_frame()
    viz.sleep_ms(33)

viz.export_snapshot("animated.html", animation=recording,
                    anim_style=AnimStyle(fps=30, loop=True))
```

See [Export](export/index.md) for the full set of options.

## Example scripts

Runnable demos — grouped by topic and searchable by keyword, with full source
on each page — live in the
[Examples → Visualization](../examples/viz/index.md) section.
