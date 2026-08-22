# Use Cases — Notebooks

The visualizer detects Jupyter automatically: `show()` renders inline instead
of opening a browser tab, and `run()` is unavailable (it would block the
kernel). For a deep dive, see [Jupyter notebooks](jupyter.md).

## Interactive Visualizer

The context manager is the simplest pattern — it clears the scene on entry and
shows it on exit:

```python
from pytanga.geometry import Point, Sphere
from pytanga.viz import Visualizer

viz = Visualizer()

with viz:  # clear scene on entry, show() inline on exit
    viz(Point(1, 2, 3), color="#ff4444")
    viz(Sphere(Point(0, 0, 0), radius=2.5), wireframe=True, opacity=0.3)
```

### Executed repeatedly

Re-running a cell that calls `display()` does **not** open a second viewer — it
flushes the latest state into the already-open one. `viz(...)` is shorthand for
`viz.new(...)`:

```python
viz = Visualizer()
viz(Point(1, 2, 3), color="#ff4444")
viz.display()          # opens the inline viewer

viz(Point(4, 5, 6), color="#44ff44")
viz.display()          # no new viewer — just flushes the update
```

## Animation

Pre-create objects once, then update them in place each frame (only changed
entities are pushed):

```python
import math
from pytanga.geometry import Point
from pytanga.viz import Visualizer

viz = Visualizer()
viz.display()  # open the inline viewer first
p = viz(Point(3, 0, 0), color="#ff4444")

angle = 0.0
for dt in viz.animate(fps=30):
    angle += 3.0 * dt
    p.entity = Point(3 * math.cos(angle), 3 * math.sin(angle), 0)
    viz.flush()
    if angle > 2 * math.pi:  # stop after one orbit
        break
```

To add fresh objects each frame instead, use `auto_clear=True` (anything added
before the loop persists):

```python
for dt in viz.animate(fps=30, auto_clear=True):
    viz(Point(3 * math.cos(angle), 3 * math.sin(angle), 0), color="#ff4444")
    viz.flush()
```

## Export

Exports read from the in-memory scene — no server needed, and they work even
while the live viewer is running:

```python
viz.export_snapshot("scene.html")   # self-contained HTML
viz.export_glb("scene.glb")         # glTF binary
viz.export_figure("figure.html")     # presentation snippet
```

For a static, serverless inline view use `display_snapshot()`:

```python
viz.display_snapshot()  # renders standalone HTML inline (no server)
```

## Notebook examples

Runnable notebooks live under `py/examples/jupyter/`:

| Notebook | Topic |
|----------|-------|
| [`interactive.ipynb`](https://github.com/dodeka12/tanga/blob/main/py/examples/jupyter/interactive.ipynb) | Context manager + idempotent `display()` |
| [`animation.ipynb`](https://github.com/dodeka12/tanga/blob/main/py/examples/jupyter/animation.ipynb) | Pre-create + update, and `auto_clear` |
| [`export.ipynb`](https://github.com/dodeka12/tanga/blob/main/py/examples/jupyter/export.ipynb) | HTML / glTF / figure export |
