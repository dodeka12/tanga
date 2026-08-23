# Handlers & Lifecycle

The `VisualizerApp` base class provides a structured lifecycle for building
interactive 3D visualization apps with sliders, dropdowns, buttons, and
control groups.

For the control methods themselves, see [Controls](controls.md).

## VisualizerApp base class

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
    title="Tanga 3D Viewer",
    annotation=None,
    background_color="#1a1a2e",
    camera=None,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `reuse_existing` | `bool` | `True` | Wait for existing browser tab before opening a new one |

See [Visualizer API](../visualizer/visualizer.md) for the full parameter list.

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

## Handler methods

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

## Complete example

See `py/examples/viz/two_spheres_interact.py` for a full working example:
two IPNS spheres with a moving slider, visibility dropdown, and reset
button, all using `VisualizerApp`.
