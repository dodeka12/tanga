# Visualizer API

The `Visualizer` class is the main entry point for the 3D viewer.

## Constructor

```python
from pytanga.viz import Visualizer, CameraConfig3d

Visualizer(
    open_browser=None,  # auto: False in Jupyter, True otherwise
    reuse_existing=True,
    title="Tanga 3D Viewer",
    annotation=None,
    background_color="#1a1a2e",
    camera=None,  # None = auto-fit from entities
    space_dim=None,          # 2 or 3; deduced from camera when None
    add_default_axes=True,   # insert a default Axes3D/Axes2D per scene
    add_default_grid=True,   # insert a default Grid per scene
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `port` | `int \| None` | `None` | *(deprecated)* HTTP + WebSocket server port. Prefer `start_server(port=...)`. |
| `host` | `str \| None` | `None` | *(deprecated)* Bind address. Prefer `start_server(host=...)`. |
| `open_browser` | `bool \| None` | auto | Open viewer URL on start |
| `reuse_existing` | `bool` | `True` | Wait for existing browser tab to reconnect before opening a new one |
| `title` | `str` | `"Tanga 3D Viewer"` | Overlay title and browser tab title (main scene). Defaults to `"Tanga 2D Viewer"` when `space_dim=2`. |
| `annotation` | `str \| None` | `None` | Markdown annotation with LaTeX math (main scene) |
| `space_dim` | `int \| None` | deduced | Spatial dimension: `3` for 3D viewer, `2` for 2D viewer. When `None` (default), it is deduced from the `camera` config (a 2D config implies `2`, a 3D config implies `3`); otherwise it defaults to `3`. See below. |
| `background_color` | `str` | `"#1a1a2e"` | CSS background color |
| `camera` | `CameraConfig \| View2DConfig \| View3dConfig \| None` | `None` | Explicit camera settings. Also accepts a `View2DConfig` / `View3dConfig` input spec, which is converted via `get_camera()` (see [Camera & Controls](camera.md)). |
| `add_default_axes` | `bool` | `True` | Whether each scene gets a default `Axes3D` (or `Axes2D` in 2D). See [Axes & Grid](axes-grid.md). |
| `add_default_grid` | `bool` | `True` | Whether each scene gets a default `Grid`. See [Axes & Grid](axes-grid.md). |

## 2D Visualization

Activate 2D mode by passing `space_dim=2`:

```python
from pytanga.viz import Visualizer
from pytanga.geometry import Point

viz = Visualizer(space_dim=2)
viz.add(Point(3, 4, 0))
viz.run()
```

Alternatively, pass a 2D camera config and the dimension is deduced
automatically:

```python
from pytanga.viz import View2DConfig, Visualizer

viz = Visualizer(camera=View2DConfig(xmin=0, xmax=8, ymin=0, ymax=6))
```

When `space_dim=2`:

- The default title becomes `"Tanga 2D Viewer"` instead of `"Tanga 3D Viewer"`.
- The camera switches to an **orthographic top-down view** looking down from
  `(0, 0, 20)` toward `(0, 0, 0)`.
- Mouse controls adjust for 2D interaction:
    - **Pan:** left-click drag *or* right-click drag
    - **Zoom:** scroll wheel
    - No orbit rotation (rotation around the view axis is locked).
- Grids and axes are explicit scene objects (see [Axes & Grid](axes-grid.md)).
- **Full 3D entities render in 2D mode.** Any 3D entity (e.g. `Sphere`,
  `Plane`, `Circle` with non‑zero `z`) can be added and renders correctly
  from the orthographic top‑down perspective. This works out of the box
  with no additional code — the camera change alone handles it.
- **Z‑coordinate = render order:** In 2D mode, the `z` field of entity
  dataclasses controls draw order, not camera depth. Entities with larger
  positive `z` render on top of those with smaller `z` (e.g.
  `Point(3, 4, 10)` appears above `Point(3, 4, 0)`). This uses
  `renderOrder` with `depthTest=false` on the Three.js materials.
- `SceneConfig`'s `space_dim` property is set to 2, and any sub‑scenes
  created from the main scene inherit this value.

See [Camera & Controls](camera.md) for details on 2D camera behavior and
[`2d_demo.py`](https://github.com/dodeka12/tanga/blob/main/dev/src/viz_2d_demo.py)
for a complete example.

## Adding Entities — `add()`

```python
add(
    obj,                          # Entity, Operator, MV, or Label
    *,
    entity_id=None,               # explicit ID or auto-generated
    color=None,                   # hex string, RGB tuple, or RGBA tuple
    opacity=None,                 # 0.0–1.0
    style=None,                   # PointStyle, SphereStyle, …
    label=None,                   # shortcut: auto-create a Label
    label_style=None,             # style for the auto-created label
) → str
```

`add()` is the universal entry point for the **main scene**. It accepts:

- **Geometry entities:** `Point`, `Direction`, `HPoint`, `PointPair`, `Line`,
  `Plane`, `Circle`, `Sphere`, `Space`
- **Operators:** `Rotor`, `Translator`, `Motor`, `Dilator`, `GeneralRotor`,
  `GeneralRotor`, `ReflectionLine`, `ReflectionPlane`, `ReflectionPoint`,
  `Inversion`
- **Multivectors (MVs):** Objects from `pytanga.algebra` — analyzed internally
  via `pytanga.geometry.analyze()`
- **Labels:** `Label(text="…", position=(x,y,z), parent_id=…)`

**Return values:**

| Input | Returns |
|-------|---------|
| Entity / Operator | Entity ID (`str`) |
| MV → entity | Entity ID (`str`) |
| `Label` instance | Label ID (`str`) |

The label that is created alongside an entity via the ``label="…"`` shortcut
can be retrieved with :meth:`get_label_ids(entity_id)`.  This returns a list
of label IDs attached to the entity.

**Color and opacity priority:**

```
add(color=...)               → explicit per-call (highest)
  ↓ if not provided
style=SphereStyle(color=…)   → user's style fields (non-None)
  ↓ if None in user's style
styles[Sphere]       → canonical default (lowest)
```

## `new()` and the `viz(...)` shorthand

`new()` is like `add()` but returns a `VizObjectRef` (with a mutable `.entity`
and `.style`) instead of a `str` id. `viz(obj, ...)` is shorthand for
`viz.new(...)`:

```python
p = viz(Point(3, 0, 0), color="#ff4444")   # == viz.new(...)
p.entity = Point(4, 0, 0)                  # update in place (marks dirty)
p.opacity = 0.5
viz.flush()
```

This is the idiomatic way to pre-create objects for an animation loop (see
[Animation](animation.md)).

## Multi-Scene Support

The visualizer supports multiple named scenes, each reachable at a unique URL
path and independently manageable via :class:`VizSceneHandle`.

### Creating Named Scenes

```python
from pytanga.viz import Visualizer
from pytanga.geometry import Point, Sphere

viz = Visualizer()
viz.start()

# Main scene (built-in, name="")
viz.add(Point(0, 0, 0), color="#ff4444")

# Create additional scenes
overview = viz.scene("overview")
detail = viz.scene("detail")

overview.add(Sphere(Point(0, 0, 0), radius=3), opacity=0.2)
detail.add(Sphere(Point(2, 1, 0), radius=1), opacity=0.5)
```

Scene names may contain slashes for grouping (e.g. ``"slides/intro"``).
Each scene has a unique URL:

| Scene | URL |
|-------|-----|
| Main (``""``) | ``http://localhost:8765/`` |
| ``"overview"`` | ``http://localhost:8765/overview`` |
| ``"detail"`` | ``http://localhost:8765/detail`` |

### `VizSceneHandle`

:meth:`Visualizer.scene` returns a :class:`VizSceneHandle` — a proxy that
exposes the same entity, label, control, animation, and title/annotation
API as ``Visualizer``, but all operations affect only the target scene.

| Method | Description |
|--------|-------------|
| `add(obj, *, ...)` | Add an entity, operator, MV, or label to this scene |
| `update(entity_id, **props)` | Update rendering properties |
| `update_entity(entity_id, obj)` | Replace geometry |
| `update_label(object_id, *, text, style)` | Update label text/style |
| `remove(entity_id)` | Remove an entity |
| `clear()` | Remove all entities from this scene |
| `flush()` | Push this scene's state to all browsers viewing it |
| `set_title(title)` | Update viewport title overlay |
| `set_annotation(text, *, style)` | Update annotation panel |
| `animate_to(entity_id, *, ...)` | Animate an entity |
| `timeline()` | Create a :class:`Timeline` targeting this scene |
| `add_slider`, `add_dropdown`, `add_button` | Add interactive controls |
| `add_group`, `remove_control`, `remove_group`, `clear_controls` | Control management |
| `navigate_to(scene_name)` | Navigate all browsers viewing *this* scene to another |
| `display(*, viewer_name, width, height)` | Jupyter inline display with optional viewer identity |
| `display_static(width, height)` | Serverless static HTML display |

Properties: `name`, `url`, `scene`, `styles`.

### Browser Navigation

:meth:`Visualizer.navigate_to` redirects connected browsers to a different
scene URL:

```python
# Navigate all browsers to the main scene
viz.navigate_to("")

# Navigate only browsers currently viewing the "overview" scene
viz.navigate_to("detail", target="scene:overview")

# Navigate a specific browser session
viz.navigate_to("slide2", target="browser:<browser_id>")

# Navigate all browsers with a specific viewer name
viz.navigate_to("intro", target="viewer:presenter-laptop")
```

Use :meth:`Visualizer.list_browsers` to inspect connected sessions:
each entry contains ``id``, ``scene``, ``remote_addr``, and ``viewer_name``.

### Viewer Identity

The optional ``?viewer=`` URL parameter assigns a friendly label to a browser
connection.  This label appears in :meth:`list_browsers` and can be targeted
in :meth:`navigate_to` via ``target="viewer:..."``.

```python
# In Jupyter: name a browser tab for targeted navigation
detail = viz.scene("detail")
detail.display(viewer_name="presenter-laptop")
```

## MV Input

```python
from pytanga.basis import BasisPGA3
from pytanga.geometry import Direction, Geometry, Plane, Point

pga = BasisPGA3()
geo = Geometry(pga)
viz = Visualizer()

# MV → analyze → Entity (the MV's algebra.opns flag is authoritative)
viz.add(geo(Point(5, 0, 0)), color="#ff4444")  # OPNS

# The same point in IPNS (grade-1 vector)
geo_ipns = Geometry(BasisPGA3(opns=False))
viz.add(geo_ipns(Point(5, 0, 0)), color="#44ff44")  # IPNS

viz.add(geo(Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1))), opacity=0.3)
```

Multivectors carry the OPNS/IPNS interpretation from the algebra that
created them; `add()` has no `opns` parameter.

## Updating Entities

```python
# Rendering properties (color, opacity, style fields)
viz.update(entity_id, color="#00ff00")

# Geometry replacement — for animation frame streaming
viz.update_entity(entity_id, Point(new_x, new_y, new_z))

# Label text / style without repositioning
viz.update_label(label_id, text="new text", style=LabelStyle(font_size=18))

# Remove entities
viz.remove(entity_id)
viz.clear()  # remove all (main scene)
```

## Server Lifecycle

| Method | Description |
|--------|-------------|
| `start(*, wait_for_browser=None, timeout=30.0)` | Start the server in a background daemon thread. In Jupyter, ``wait_for_browser`` defaults to ``False``; outside Jupyter it defaults to ``True``. |
| `wait_for_browser(timeout=30.0)` | Block until a WebSocket client connects. Returns `True` on success, `False` on timeout. |
| `flush(*, fit_camera=False)` | Push all dirty scenes to connected browsers.  Pass ``fit_camera=True`` after all entities are added to have the frontend auto‑adjust the camera to encompass them. |
| `stop()` | Stop the server and clean up. Waits for graceful WebSocket shutdown before stopping the event loop. |
| `run(*, wait_for_browser=None)` | Start server, open browser, block until Ctrl+C. In Jupyter, ``wait_for_browser`` defaults to ``False``. |
| `sleep_ms(ms)` | Sleep for ``ms`` milliseconds, returning early on the scene's stop key or Ctrl+C. Returns ``True`` if it slept the full interval, ``False`` if interrupted. |
| `interrupted()` | Returns ``True`` once the scene's browser stop key (default `q`) or Ctrl+C / SIGTERM has been received (requires the server to be started). Use it to break custom/nested loops. |
| `animate(*, fps=60.0, stop_key="q", stop_modifiers=None, scene_name="")` | Yield once per animation frame until interrupted (see [Animation](animation.md)). Paces the loop to ``fps``; ``fps=0`` disables pacing. The browser key defaults to `q` (matches `Q` too); ``stop_modifiers`` accepts `KeyModifier` values. The loop is scoped to ``scene_name``. |
| `url` (property) | The HTTP URL of the viewer (`"http://localhost:8765"`) |
| `scene(name)` | Get or create a named scene, returns :class:`VizSceneHandle` |
| `scenes` (property) | All scenes keyed by name (``""`` is the main scene) |
| `list_scenes()` | Return all scene names |
| `list_browsers()` | Return connected browser sessions as ``[{id, scene, remote_addr, viewer_name}]`` |
| `navigate_to(scene_name, *, target)` | Redirect matching browser sessions to another scene URL |
| `display_row(*scenes, width, height, gap)` | Display multiple scenes side-by-side in Jupyter (see [Jupyter Notebooks](jupyter.md)) |

Both `start()` and `run()` accept a `wait_for_browser` keyword-only argument.
When ``None`` (the default), it auto-detects: ``False`` in Jupyter (since
iframes connect asynchronously), ``True`` otherwise.  Set explicitly for
export-only or headless workflows where no browser will be opened.

### Browser Tab Reuse

When `reuse_existing=True` (the default), the server waits up to 3 seconds
after booting for an **existing browser tab** to reconnect via WebSocket.  If
the old tab reconnects during this window, no new tab is opened.  If not, a
new browser tab opens automatically.  Set `reuse_existing=False` to always open
a new tab immediately.

```
Waiting for existing browser to reconnect ...
No existing browser connected — opening new tab.
Browser at 127.0.0.1 loaded page (token: a1b2c3d4).
✓ Browser connected  (id=e5f6g7h8, token=a1b2c3d4, ip=127.0.0.1).
```

### Connection Logging

Every browser connection produces two log lines:

1. **Page load** (dim): printed when the browser fetches `viewer.html`, showing
   the remote address and a unique page token that correlates the HTTP request
   with the expected WebSocket connection.

2. **WebSocket connected** (green): printed after the browser completes the
   WebSocket handshake and sends its ``ready`` message.  Includes all available
   identifiers: browser ``id``, page ``token``, optional ``viewer`` name (from
   the ``?viewer=`` URL parameter), and remote ``ip``.

```
Browser at 192.168.1.10 loaded page (token: abc12345).
✓ Browser connected  (id=def67890, token=abc12345, viewer=my-tab, ip=192.168.1.10).
```

### WebSocket Reachability Diagnostics

On startup, the server prints only the HTTP URL:

```
http://localhost:8765
Waiting for browser to connect at http://localhost:8765 ...
```

The WebSocket URL (`ws://localhost:8765/ws`) and a reachability note only appear
if something goes wrong — either in a stale-token warning (below) or after a
`wait_for_browser()` timeout.  This keeps the normal output clean.

### Stale-Token Warning

After a browser first loads the page, the server waits for the WebSocket
``ready`` message.  If a page token remains unmatched after a grace period
(default 10 s), the server prints a warning:

```
┌──────────────────────────────────────────────────────────────────┐
│ ╔══════════════════════════════════════════════════════════════╗ │
│ ║  WebSocket connection failed                                 ║ │
│ ║  Browser at 192.168.1.10 loaded the page via HTTP but the    ║ │
│ ║  WebSocket never connected.                                  ║ │
│ ║  Check that the following URL is reachable:                  ║ │
│ ║  ws://localhost:8765/ws                                      ║ │
│ ╚══════════════════════════════════════════════════════════════╝ │
└──────────────────────────────────────────────────────────────────┘
```

This pinpoints the exact scenario where a port forward or reverse proxy
delivers the HTML page but strips WebSocket upgrade headers — the browser shows
the initial 3D viewport but never receives any geometry.

Controls and scene state are automatically pushed to all connected tabs.

### Multi-Tab Support

Multiple browser tabs can connect to the same server simultaneously.  Each
tab receives a unique browser ID and can independently view different scenes.
Scene state and controls are scoped per-scene — only the scene currently
being viewed by a tab is pushed to it.

### Blocking Mode (`show()` + `wait()`)

Simplest for one-shot scripts:

```python
viz = Visualizer()
viz.add(Point(1, 2, 3), color="#ff4444")
viz.show()  # serve on port 8765 + open a browser tab
viz.wait()  # blocks until Ctrl+C, then stops the server
```

Under WSL, native Windows, or headless environments where automatic browser
open is unsupported, `run()` prints the viewer URL and waits for you to open
it manually:

```
Waiting for browser to connect at http://localhost:8765 ...
Browser connected.
```

### Context Managers

`Visualizer` and `VizSceneHandle` can be used as context managers: they clear
the scene and call `show()` on entry, then `flush()` on exit.

```python
with viz:                       # clear + show main scene on entry
    viz.add(Point(1, 2, 3))

with viz.scene("detail"):       # clear + show named scene on entry
    viz.scene("detail").add(Point(4, 5, 6))
```

In Jupyter, `show()` renders inline (delegating to `display()`); in scripts it
opens a browser tab — follow the block with `wait()` to keep the script alive.

### Non-Blocking Mode (`start_server()` / `flush()` / `stop_server()`)

For animation loops and Jupyter notebooks:

```python
viz.start_server()  # serve only (defaults to port 8765)
point_id = viz.add(Point(3, 0, 0))
viz.flush()

for dt in viz.animate(fps=60):   # serves, opens a browser, runs until Q/Ctrl+C
    viz.update_entity(point_id, Point(new_x, new_y, new_z))
    viz.flush()
```

`animate()` ends when the scene's browser stop key (default `q`) or terminal
Ctrl+C / SIGTERM is received. The server is stopped automatically at
interpreter exit.

`start_server(host=..., port=...)` controls where the server binds:

- `port=None` (default) — use the standard Tanga viewer port **8765**, so an
  already-open browser tab can reconnect after the server restarts.
- `port=0` — auto-pick a free port.
- `port > 0` — use that exact port.

`host` defaults to `"localhost"`.  `show()` accepts the same `host`/`port`
keywords and forwards them to `start_server()` when the server isn't already
running.

For export-only workflows where no browser is needed:

```python
# add entities, export HTML/glTF without a live viewer
viz.export_snapshot("scene.html")
viz.export_glb("scene.glb")
```

### Serving & Lifecycle Summary

| Method | Purpose |
|--------|---------|
| `show(host=None, port=None, jupyter=None, viewer_name=None)` | Serve + show: opens a browser tab, or renders inline in Jupyter (delegates to `display()`). `viewer_name` dedupes notebook outputs. |
| `wait()` | Block until Ctrl+C, then stop the server |
| `start_server(host="localhost", port=None)` | Serve only (no browser). Port: `None`→8765, `0`→auto-pick, `>0`→exact |
| `stop_server()` | Stop the server |
| `open_browser()` | Open/reconnect a browser tab |
| `animate(fps, auto_clear=False)` | Serve (headless), yield a frame time each loop, stop on the scene's key or Ctrl+C. Never opens the viewer — call `show()` first. With `auto_clear=True`, objects added inside the loop are removed each frame |

### Deprecated Aliases

| Old | New |
|-----|-----|
| `start()` | `start_server()` + `open_browser()` (i.e. `show()`) |
| `stop()` | `stop_server()` |
| `run()` | `show()` + `wait()` |
| `display_static()` | `display_snapshot()` |
| `export_html()` | `export_snapshot()` |
| `export_figure_html()` | `export_figure(path=None)` |
| `open_figure()` | `open_snapshot()` |
| `export_animated_html()` | `export_snapshot(animation=rec)` |
| `export_animated_figure()` | `export_figure(animation=rec)` |
| `SceneExporter` | `viz` / `viz.scene(name)` |
