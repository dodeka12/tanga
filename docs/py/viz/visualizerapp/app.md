# Visualizer App

For the most flexibility — interactive controls (sliders, dropdowns, buttons)
with a managed lifecycle — derive from `VisualizerApp`. It handles the server
lifecycle (start → `init` → wait → `cleanup` → stop) so your class only defines
the scene and its handlers.

```python
from pytanga.geometry import Point, Sphere
from pytanga.viz import ControlEvent, VisualizerApp


class MyApp(VisualizerApp):
    def __init__(self):
        super().__init__(title="My Interactive App")

    async def init(self) -> None:
        # Build the scene and register controls.
        self._sphere = self.viz(Sphere(Point(0, 0, 0), radius=1), opacity=0.3)
        self.viz.add_slider(
            "radius",
            label="Radius",
            min=0.2,
            max=5.0,
            default=1.0,
            on_change=self.on_radius,
        )
        self.viz.flush()

    async def on_radius(self, value: float, _event: ControlEvent) -> None:
        self.viz.update_entity(self._sphere.id, Sphere(Point(0, 0, 0), value))
        self.viz.flush()

    async def cleanup(self) -> None:
        pass  # teardown


if __name__ == "__main__":
    MyApp().run()
```

## Lifecycle

1. `run()` starts the server (and waits for a browser, by default).
2. `init()` is called once — add entities and register controls here.
3. The event loop blocks until **Ctrl+C**.
4. `cleanup()` runs, then the server stops.

The `viz` attribute is a `Visualizer` instance, available in every method.
`run()` accepts `wait_for_browser=True` and `timeout=30.0`.

## Controls

Controls are created on `self.viz` and appear as an overlaid panel in the
browser. Each takes a unique id and an **async** handler callback.

| Control | Method | Handler signature |
|---------|--------|-------------------|
| Slider | `add_slider(id, label, min, max, step, default, on_change)` | `(value: float, event) -> None` |
| Dropdown | `add_dropdown(id, label, options, default, on_change)` | `(value: str, event) -> None` |
| Button | `add_button(id, label, on_click)` | `(value: None, event) -> None` |

Group them into a collapsible panel:

```python
self.viz.add_group(
    "controls",
    title="Controls",
    controls=["radius", "reset"],
    position="bottom-right",
)
```

Remove them with `remove_control(id)`, `remove_group(id)`, or `clear_controls()`.
Handlers receive the new value plus a `ControlEvent`; use
`self.viz.update_entity(...)` / `self.viz.update(...)` then `flush()` to apply
changes.

## Complete example

See [`two_spheres_interact.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/two_spheres_interact.py)
for a full working app — two IPNS spheres with a moving slider, a visibility
dropdown, and a reset button. The full control reference is in
[Controls](controls.md).
