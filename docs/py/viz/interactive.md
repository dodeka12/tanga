# Interactive Controls

The `VisualizerApp` base class provides a structured lifecycle for building
interactive 3D visualization apps with sliders, dropdowns, buttons, and
control groups.

## VisualizerApp Base Class

Derive from `VisualizerApp`, override `init()` and `cleanup()`, and call
`run()` from your `main()` function:

```python
from pytanga.viz import ControlEvent, VisualizerApp

class MyApp(VisualizerApp):
    def __init__(self):
        super().__init__(title="My Scene")

    async def init(self) -> None:
        self.viz.add_slider("x", on_change=self.on_x)

    async def on_x(self, value: float, event: ControlEvent) -> None:
        self.viz.flush()

    async def cleanup(self) -> None:
        pass  # teardown

if __name__ == "__main__":
    MyApp().run()
```

## Constructor

`VisualizerApp.__init__` accepts the same parameters as `Visualizer`, and
forwards them directly:

```python
VisualizerApp(
    port=8765,
    host="localhost",
    open_browser=None,
    reuse_existing=True,
    opns=True,
    title="Tanga 3D Viewer",
    annotation=None,
    space_extent=10.0,
    show_grid=True,
    show_axes=True,
    background_color="#1a1a2e",
    camera=None,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `reuse_existing` | `bool` | `True` | Wait for existing browser tab before opening a new one |

See [Visualizer API](visualizer.md) for the full parameter list.

## Lifecycle

1. `start()` — server boots in a background thread, browser connects
2. `init()` — user overrides this method to add entities and controls
3. (wait) — the event loop blocks until the user presses **Ctrl+C**
4. `cleanup()` — user overrides for graceful teardown
5. `stop()` — server shuts down, all connections closed

The `viz` attribute (a `Visualizer` instance) is available in all methods:

```python
class MyApp(VisualizerApp):
    async def init(self) -> None:
        self.viz.add(Point(0, 0, 0), color="#ff4444")
        self.viz.flush()
```

## Control Methods

Controls are created on the `Visualizer` instance via `self.viz`. They
appear as an overlaid control panel in the browser.

### `add_slider`

```python
self.viz.add_slider(
    "sphere_b_x",
    label="X Position",
    min=-3.5,
    max=3.5,
    step=0.02,
    default=2.5,
    on_change=self.on_slider,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cid` | `str` | *(required)* | Control ID (unique string) |
| `label` | `str` | `""` | Label text displayed above the slider |
| `min` | `float` | `0.0` | Minimum value |
| `max` | `float` | `1.0` | Maximum value |
| `step` | `float` | `0.01` | Step increment |
| `default` | `float` | `min` | Initial value |
| `on_change` | `Callable` | `None` | Async callback: `(value: float, event: ControlEvent) -> None` |

### `add_dropdown`

```python
self.viz.add_dropdown(
    "mode",
    label="Display",
    options=["Both", "Sphere A only", "Sphere B only"],
    default="Both",
    on_change=self.on_mode,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cid` | `str` | *(required)* | Control ID |
| `label` | `str` | `""` | Label text |
| `options` | `list[str]` | `[]` | Dropdown choices |
| `default` | `str` | `""` | Initial selection |
| `on_change` | `Callable` | `None` | Async callback: `(value: str, event: ControlEvent) -> None` |

### `add_button`

```python
self.viz.add_button(
    "reset",
    label="Reset",
    on_click=self.on_reset,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cid` | `str` | *(required)* | Control ID |
| `label` | `str` | `""` | Button text |
| `on_click` | `Callable` | `None` | Async callback: `(value: None, event: ControlEvent) -> None` |

### `add_group`

Groups controls into a collapsible panel at a fixed position:

```python
self.viz.add_group(
    "viewport_controls",
    title="Controls",
    controls=["sphere_b_x", "mode", "reset"],
    position="bottom-right",
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `gid` | `str` | *(required)* | Group ID |
| `title` | `str` | `""` | Group header (empty = no header) |
| `controls` | `list[str]` | `[]` | Ordered list of control IDs |
| `position` | `str` | `"bottom-right"` | `"top-left"`, `"top-right"`, `"bottom-left"`, `"bottom-right"` |
| `collapsed` | `bool` | `False` | Start collapsed |
| `on_toggle` | `Callable` | `None` | Async callback: `(value: bool, event: ControlEvent) -> None` |

Controls must be created **before** the group that references them.

### Removing Controls

```python
self.viz.remove_control("sphere_b_x")
self.viz.remove_group("viewport_controls")
self.viz.clear_controls()  # remove all
```

## Handler Methods

Handler callbacks are **async** methods on your app class. They receive
the new value from the control and a :class:`~pytanga.viz.ControlEvent`
instance with metadata about the event:

```python
from pytanga.viz import ControlEvent

async def on_slider(self, value: float, event: ControlEvent) -> None:
    """Called when the slider moves."""
    self._x = value
    s2_mv = self._geo.create(Sphere(Point(value, 0, 0), 1.3))
    self.viz.update_entity(SPHERE_B_ID, s2_mv)
    self.viz.flush()

async def on_mode(self, mode: str, event: ControlEvent) -> None:
    """Called when the dropdown changes."""
    self._mode = mode
    await self._update_scene()

async def on_reset(self, _: None, event: ControlEvent) -> None:
    """Called when the button is clicked."""
    self._x = 2.5
    self.viz.clear_controls()
    self._setup_controls()
```

The :class:`ControlEvent` currently carries a ``browser_id`` attribute that
can be used with :meth:`~pytanga.viz.Visualizer.navigate_to` to redirect a
specific browser tab.  Additional metadata fields may be added in the future
without breaking existing handler signatures.

### Scene-Scoped Controls

Controls are scoped per-scene — when using :class:`VizSceneHandle`, controls
are created on the target scene and only appear for browsers viewing that
scene:

```python
detail = viz.scene("detail")
detail.add_slider("radius", label="Radius", min=0.1, max=5.0, on_change=on_radius)
detail.add_button("reset", label="Reset", on_click=on_reset)
detail.add_group("detail_controls", controls=["radius", "reset"], title="Detail")
```

Controls and groups are pushed only to browsers viewing the ``"detail"`` scene.
This allows different scenes to have completely independent control panels.

## Complete Example

See `py/examples/viz/two_spheres_interact.py` for a full working example:
two IPNS spheres with a moving slider, visibility dropdown, and reset
button, all using `VisualizerApp`.