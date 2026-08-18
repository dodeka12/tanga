# Jupyter Notebook Support

The `Visualizer` detects Jupyter/IPython automatically and adapts behaviour
for notebook environments.

## Auto-Detection

- `open_browser` defaults to `False` (no popup).
- `run()` is **not** available — it would block the kernel indefinitely.
- Use the `start_server()` / `flush()` / `stop_server()` non-blocking pattern
  instead (or `show()` to also open a browser).
- When the `Visualizer` object is the last expression in a notebook cell,
  it renders an inline `<iframe>` via the `_repr_html_()` method.

## Notebook Workflow

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

## How It Works

- `start_server()` launches the aiohttp server in a background daemon thread.
  The server survives across notebook cells until `stop_server()` is called.
- `flush()` pushes scene state to all connected browsers — call it after
  adding or modifying entities.
- `_repr_html_()` returns an `<iframe>` pointing to the server URL. Jupyter
  calls this automatically when the `Visualizer` object is the last expression
  in a cell.
- `stop_server()` releases the port and terminates the background thread.
  Always call it when done to free resources.

## Serverless Display — ``display_snapshot()``

For quick static snapshots — **no WebSocket server, no daemon threads** —
use :meth:`display_snapshot()`.  It generates a self-contained Three.js HTML
document from the current scene state and renders it inline in Jupyter
(or opens it in a browser tab outside Jupyter).

```python
viz = Visualizer()
viz.add(Point(1, 2, 3), color="#ff4444")
viz.add(Sphere(0, 0, 0, 2), opacity=0.3)

# In Jupyter — renders inline HTML
viz.display_snapshot()

# Outside Jupyter — opens a browser tab
viz.display_snapshot(width=800, height=600)
```

### When to Use

| Scenario | Use |
|----------|-----|
| Live interaction (rotate, zoom, animate) | ``start_server()`` + ``flush()`` + ``_repr_html_()`` |
| Quick static visualization | ``display_snapshot()`` |
| Export to HTML/PDF (nbconvert) | ``display_snapshot()`` |
| Progressive figure building | Call ``display_snapshot()`` after each add |

Each call snapshots the current scene — entities added later appear in
subsequent calls but not in earlier ones.  Works independently of
``start_server()``/``stop_server()`` — the live server can be running or not.

## Multi-Scene Display — ``display_row()``

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

To display **static** (serverless) snapshots side by side, pass
``mode="static"``:

```python
viz.display_row((overview, None), (detail, None), mode="static")
```

## Scene-Specific Inline Display — ``VizSceneHandle.display()``

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

## Limitations

- **Remote Jupyter** (Colab, Binder, remote kernels): The iframe points to
  `localhost`, which is the **server machine**, not your local browser. The
  viewer won't be reachable. Open the printed URL in a separate browser tab
  on the machine running the kernel.
- **Port conflicts:** `start_server()` defaults to port 8765; pass `port=...`
  to choose another, or `port=0` to auto-pick a free port.
- **Multiple scenes:** Create named scenes via ``viz.scene("name")`` instead
  of multiple ``Visualizer`` instances — all scenes share one server on one port.
