# Visualizer API

The `Visualizer` class is the main entry point for the 3D viewer.

## Constructor

```python
from pytanga.viz import Visualizer, CameraConfig

Visualizer(
    port=8765,
    host="localhost",
    open_browser=None,  # auto: False in Jupyter, True otherwise
    reuse_existing=True,
    opns=True,
    title="Tanga 3D Viewer",
    annotation=None,
    space_extent=10.0,
    show_grid=True,
    show_axes=True,
    background_color="#1a1a2e",
    camera=None,  # None = auto-fit from entities
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `port` | `int` | `8765` | HTTP + WebSocket server port |
| `host` | `str` | `"localhost"` | Bind address |
| `open_browser` | `bool \| None` | auto | Open viewer URL on start |
| `reuse_existing` | `bool` | `True` | Wait for existing browser tab to reconnect before opening a new one |
| `opns` | `bool` | `True` | Default MV interpretation (OPNS/IPNS) |
| `title` | `str` | `"Tanga 3D Viewer"` | Overlay title and browser tab title (main scene). Defaults to `"Tanga 2D Viewer"` when `space_dim=2`. |
| `annotation` | `str \| None` | `None` | Markdown annotation with LaTeX math (main scene) |
| `space_dim` | `int` | `3` | Spatial dimension: `3` for 3D viewer, `2` for 2D viewer (see below) |
| `space_extent` | `float` | `10.0` | Half-extent of visible space |
| `show_grid` | `bool` | `True` | Show ground grid |
| `show_axes` | `bool` | `True` | Show RGB axes helper |
| `background_color` | `str` | `"#1a1a2e"` | CSS background color |
| `camera` | `CameraConfig \| None` | `None` | Explicit camera settings |

## 2D Visualization

Activate 2D mode with `space_dim=2`:

```python
from pytanga.viz import Visualizer
from pytanga.geometry import Point

viz = Visualizer(space_dim=2)
viz.add(Point(3, 4, 0))
viz.run()
```

When `space_dim=2`:

- The default title becomes `"Tanga 2D Viewer"` instead of `"Tanga 3D Viewer"`.
- The camera switches to an **orthographic top-down view** looking down from
  `(0, 0, 20)` toward `(0, 0, 0)`.
- Mouse controls adjust for 2D interaction:
    - **Pan:** left-click drag *or* right-click drag
    - **Zoom:** scroll wheel
    - No orbit rotation (rotation around the view axis is locked).
- The grid renders as a flat XY plane instead of a ground plane.
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
    opns=None,                    # MV interpretation (None = instance default)
    color=None,                   # hex string, RGB tuple, or RGBA tuple
    opacity=None,                 # 0.0–1.0
    style=None,                   # PointStyle, SphereStyle, …
    label=None,                   # shortcut: auto-create a Label
    label_style=None,             # style for the auto-created label
) → str | list[str] | tuple[str, str]
```

`add()` is the universal entry point for the **main scene**. It accepts:

- **Geometry entities:** `Point`, `Direction`, `HPoint`, `PointPair`, `Line`,
  `Plane`, `Circle`, `Sphere`, `Space`
- **Operators:** `Rotor`, `Translator`, `Motor`, `Dilator`, `GeneralRotor`,
  `GeneralDilator`, `ReflectionLine`, `ReflectionPlane`, `ReflectionPoint`,
  `Inversion`
- **Multivectors (MVs):** Objects from `pytanga.algebra` — analyzed internally
  via `pytanga.geometry.analyze()`
- **Labels:** `Label(text="…", position=(x,y,z), parent_id=…)`

**Return values:**

| Input | Returns |
|-------|---------|
| Entity / Operator | Entity ID (`str`) |
| MV → single entity | Entity ID (`str`) |
| MV → multiple entities | List of IDs (`list[str]`) |
| Entity with `label="…"` shortcut | `(entity_id, label_id)` tuple |
| `Label` instance | Label ID (`str`) |

**Color and opacity priority:**

```
add(color=...)               → explicit per-call (highest)
  ↓ if not provided
style=SphereStyle(color=…)   → user's style fields (non-None)
  ↓ if None in user's style
default_styles[Sphere]       → canonical default (lowest)
```

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

Properties: `name`, `url`, `scene`, `default_styles`, `default_label_style`.

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
from pytanga.algebra import Algebra

pga = BasisPGA3()
viz = Visualizer(opns=True)

# MV → analyze(opns=True) → Entity
viz.add(pga.point(5, 0, 0), color="#ff4444")  # OPNS
viz.add(pga.point(5, 0, 0), color="#44ff44", opns=False)  # IPNS
viz.add(pga.plane(0, 0, 1, 3), opacity=0.3)
```

The `opns` flag on `add()` overrides the instance default. When `None`,
the instance's `self._opns` value is used.

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
| `flush()` | Push all dirty scenes to connected browsers |
| `stop()` | Stop the server and clean up. Waits for graceful WebSocket shutdown before stopping the event loop. |
| `run(*, wait_for_browser=None)` | Start server, open browser, block until Ctrl+C. In Jupyter, ``wait_for_browser`` defaults to ``False``. |
| `sleep_ms(ms)` | Convenience: `time.sleep(ms / 1000)` |
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

### Blocking Mode (`run()`)

Simplest for one-shot scripts:

```python
viz = Visualizer()
viz.add(Point(1, 2, 3), color="#ff4444")
viz.run()  # waits for browser, opens it, blocks until Ctrl+C
```

Under WSL, native Windows, or headless environments where automatic browser
open is unsupported, `run()` prints the viewer URL and waits for you to open
it manually:

```
Waiting for browser to connect at http://localhost:8765 ...
Browser connected.
```

### Non-Blocking Mode (`start()` / `flush()` / `stop()`)

For animation loops and Jupyter notebooks.  By default, `start()` blocks until
a browser connects so that entities added afterwards are delivered reliably:

```python
viz.start()  # waits for browser, then returns
point_id = viz.add(Point(3, 0, 0))
viz.flush()

for _ in range(100):
    viz.update_entity(point_id, Point(new_x, new_y, new_z))
    viz.flush()
    viz.sleep_ms(16)

viz.stop()
```

For export-only workflows where no browser is needed:

```python
viz.start(wait_for_browser=False)
# add entities, export HTML/glTF without a live viewer
exporter = SceneExporter(viz)
exporter.export_html("scene.html")
viz.stop()
```
