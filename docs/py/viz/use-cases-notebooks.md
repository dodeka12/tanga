# Use Cases — Notebooks

The visualizer detects Jupyter automatically: `show()` renders inline instead
of opening a browser tab, and `run()` is unavailable (it would block the
kernel). For a deep dive, see [Jupyter notebooks](jupyter/index.md).

## Interactive Visualizer

The context manager is the simplest pattern — it clears the scene and shows it
on entry (then flushes on exit):

```python
from pytanga.geometry import Point, Sphere
from pytanga.viz import SphereStyle, Visualizer

viz = Visualizer()

with viz:  # clear + show on entry, flush on exit
    viz(Point(1, 2, 3), color="#ff4444")
    viz(Sphere(Point(0, 0, 0), radius=2.5), style=SphereStyle(wireframe=True), opacity=0.3)
```

### Executed repeatedly

`Visualizer()` is a **singleton under Jupyter** — re-running a cell that
re-creates it returns the same instance (one server, one scene host) instead of
trying to bind the port again.  Re-running a construction cell also **clears
the default scene** and re-adds axes/grid according to the `add_default_axes` /
`add_default_grid` flags:

```python
from pytanga.geometry import Point
from pytanga.viz import Visualizer

viz = Visualizer()  # safe to re-run: clears the default scene and re-seeds axes/grid
```

The cell you edit and re-run only *adds entities* and calls `show()`.
Re-running it does **not** open a second viewer — it flushes the latest state
into the already-open one. `viz(...)` is shorthand for `viz.new(...)`:

```python
viz(Point(1, 2, 3), color="#ff4444")
viz.show()          # opens the inline viewer (starts the server)

viz(Point(4, 5, 6), color="#44ff44")
viz.show()          # no new viewer — just flushes the update
```

!!! info "Building up a scene across re-runs"
    Re-running a cell that only *adds* and `show()`s accumulates entities in
    the default scene.  For a clean slate each run, use the context manager
    (`with viz:`) or call `viz.clear()` first.

## Animation

Pre-create objects once, then update them in place each frame (only changed
entities are pushed):

```python
import math
from pytanga.geometry import Point
from pytanga.viz import Visualizer

viz = Visualizer()
viz.show()  # start the server and render inline
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
before the loop persists). This is concise for **quick, short scripts** and
one-off demos, but **less performant** than updating in place above (each frame
removes and recreates the previous frame's objects):

```python
import math
from pytanga.geometry import Point
from pytanga.viz import Visualizer

viz = Visualizer()
viz.show()  # start the server and render inline
viz(Point(0, 0, 0), color="#ffffff")  # persists across frames

angle = 0.0
for dt in viz.animate(fps=30, auto_clear=True):
    angle += 3.0 * dt
    viz(Point(3 * math.cos(angle), 3 * math.sin(angle), 0), color="#ff4444")
    viz.flush()
    if angle > 2 * math.pi:  # stop after one orbit
        break
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

## Caveats

- **Jupyter-only.** The singleton, the re-run reset, and the `scene(name)`
  same-cell clear only apply inside a notebook.  Plain scripts and
  `VisualizerApp` keep constructing independent viewers.
- **First call wins for scene config.** On a re-run, only `add_default_axes` /
  `add_default_grid` are re-applied; `camera`, `title`, `space_dim`, and the
  other constructor options keep the first call's values.
- **`scene(name)` re-run.** Creating a scene in a cell is safe to re-run: the
  same cell re-running clears that scene and re-adds its defaults.  A
  *different* cell that calls `viz.scene(name)` gets the existing scene without
  clearing, so you can build on it.
- **`stop_server()` is kernel-wide.** There is one server per kernel; stopping
  it affects every scene and cell in that kernel.
- **Port still matters across kernels.** The singleton is per-process; a second
  kernel (or a stale server) on port 8765 can still conflict.

## Notebook examples

Runnable notebooks are listed in the
[Examples → Jupyter Notebooks](../examples/viz/jupyter/index.md) section.
