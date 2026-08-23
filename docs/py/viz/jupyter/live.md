# Live inline display

Live display embeds the **running** server in an inline iframe, so you can
rotate, pan, zoom, and animate. It requires the server to be running (and the
kernel to be on the same machine as the browser).

## Notebook workflow

```python
# Cell 1: Setup
from pytanga.viz import Visualizer, CameraConfig3d
from pytanga.geometry import Point, Sphere, Plane, Direction

viz = Visualizer(
    camera=CameraConfig3d(fov=45),
)
viz.start_server()
print(f"Viewer available at {viz.url}")
```

```python
# Cell 2: Add entities
viz.add(Point(2, 0, 0), color="#ff4444", size=0.15, label="P₁")
viz.add(Point(0, 2, 0), color="#44ff44", size=0.15, label="P₂")
viz.add(Sphere(Point(0, 0, 0), radius=2.5), wireframe=True, opacity=0.3)
viz.flush()
print("Entities added and flushed.")
```

```python
# Cell 3: Display the viewer inline
viz  # renders inline <iframe> for the main scene
```

```python
# Cell 4: Add more entities later
viz.add(
    Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0)),
    color="#44ff44", label="L (x-axis)",
)
viz.flush()
viz  # re-render iframe for main scene
```

```python
# Cell 5: Cleanup
viz.stop_server()
print("Server stopped.")
```

## Animation

Pre-create objects once and update them in place each frame — only changed
entities are pushed:

```python
viz.show()  # start the server and render inline
p = viz(Point(3, 0, 0), color="#ff4444")   # viz(...) == viz.new(...)

for dt in viz.animate(fps=30):
    p.entity = Point(...)   # update in place
    viz.flush()
```

Or add fresh objects each frame with `auto_clear=True` (anything added *before*
the loop persists):

```python
for dt in viz.animate(fps=30, auto_clear=True):
    viz(Point(...), color="#ff4444")
    viz.flush()
```

See [Use Cases — Notebooks](../use-cases-notebooks.md) and
[Animation](../visualizer/animation.md) for the full patterns.

## Idempotent `display()` / `show()` and context managers

Re-running a cell that calls `display()` or `show()` does **not** open a
second viewer.  The viewer is identified by an optional `viewer_name`; if you
omit it, the current notebook cell id is used automatically (via the IPython
`pre_run_cell` event), falling back to the scene name.  A repeated call just
flushes the latest scene state into the already-open viewer:

```python
viz = Visualizer()
viz.add(Point(1, 2, 3))
viz.show()          # opens the inline viewer (starts the server)
viz.add(Point(4, 5, 6))
viz.show()          # no new viewer — just flushes the update
```

`Visualizer` and `VizSceneHandle` are also context managers: they clear the
scene and call `show()` on entry, then `flush()` on exit.

```python
with viz:                          # main scene: clear, then show
    viz.add(Point(1, 2, 3))

with viz.scene("detail"):          # named scene: clear, then show
    viz.scene("detail").add(Point(4, 5, 6))
```

Pass an explicit `viewer_name` to keep two cells pointing at the **same**
scene independent of each other:

```python
viz.scene("detail").display(viewer_name="cell-a")
viz.scene("detail").display(viewer_name="cell-b")
```

Outside Jupyter, `display()` returns an HTML `<iframe>` string and `show()`
opens a browser tab, as before.

## Multi-scene display — `display_row()`

For side-by-side comparison of multiple scenes, use :meth:`Visualizer.display_row`:

```python
# Create multiple scenes
overview = viz.scene("overview")
detail = viz.scene("detail")

overview.add(Sphere(Point(0, 0, 0), radius=3), opacity=0.2)
detail.add(Sphere(Point(2, 1, 0), radius=1), opacity=0.8)

viz.flush()

# Display side-by-side in a single cell
viz.display_row(
    (overview, "left-browser"),
    (detail, "right-browser"),
    width="100%",
    height=500,
    gap=12,
)
```

Each element is a ``(handle, viewer_name)`` tuple.  The optional *viewer_name*
is passed as ``?viewer=`` URL parameter and can be used with
:meth:`Visualizer.navigate_to` and :meth:`Visualizer.list_browsers` for
targeted browser control.

For **static** (serverless) side-by-side snapshots, pass ``mode="static"`` —
see [Static inline display](static.ipynb).

## Scene-specific display — `VizSceneHandle.display()`

:meth:`VizSceneHandle.display` renders a single scene inline with an optional
viewer identity:

```python
detail = viz.scene("detail")
detail.display(viewer_name="presenter-laptop", width="100%", height=500)
```

In Jupyter, this returns an :class:`IPython.display.IFrame`. The
``_repr_html_()`` method on ``VizSceneHandle`` also works — put the handle
as the last expression in a cell:

```python
detail  # renders inline <iframe> pointing to /detail
```
