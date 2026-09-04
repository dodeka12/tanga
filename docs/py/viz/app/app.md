# Visualizer App

For the most flexibility — interactive controls (sliders, dropdowns, buttons)
with a managed lifecycle — derive from `VisualizerApp`. It handles the server
lifecycle (start → `init` → wait → `cleanup` → stop) so your class only defines
the scene and its handlers.

```python
from pytanga.geometry import Point, Sphere
from pytanga.viz import ControlEvent, SliderView, VisualizerApp


class MyApp(VisualizerApp):
    def __init__(self):
        super().__init__(title="My Interactive App")

    async def init(self) -> None:
        # Build the scene and mount a control view in the layout overlay.
        self._sphere = self.viz(Sphere(Point(0, 0, 0), radius=1), opacity=0.3)
        self.viz.add(
            SliderView(
                "radius",
                label="Radius",
                min=0.2,
                max=5.0,
                value=1.0,
                on_change=self.on_radius,
            )
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
3. The event loop blocks until shutdown is requested.
4. `cleanup()` runs, then the server stops.

The `viz` attribute is a `Visualizer` instance, available in every method.
`run()` accepts `wait_for_browser=True` and `timeout=30.0`.

## Stopping the app

Shutdown can be requested three ways:

1. Terminal **Ctrl+C** — always available.
2. Browser **Ctrl+Q** — opt-in. Create the app with
   `VisualizerApp(enable_server_stop_key=True)` to enable the default Ctrl+Q
   binding on the main scene (it mirrors a terminal Ctrl+C).
3. A **handler-triggered stop** — call `self.request_shutdown()` from any
   control or interaction handler, e.g. a "Quit" button:

```python
class MyApp(VisualizerApp):
    async def init(self) -> None:
        self.viz.add(ButtonView("quit", label="Quit", on_click=self.on_quit))

    async def on_quit(self, _value, _event) -> None:
        self.request_shutdown()
```

In every case `cleanup()` runs and the server stops.

## Controls

Controls are declarative `*View` classes mounted via `self.viz.add(view)` (or a
`set_layout`/`show(layout=...)` layout). Each takes a unique id and an **async**
handler callback.

| Control | View class | Handler signature |
|---------|-----------|-------------------|
| Slider | `SliderView(id, label, min, max, step, value, on_change)` | `(value: float, event) -> None` |
| Dropdown | `DropdownView(id, label, options, value, on_change)` | `(value: str, event) -> None` |
| Button | `ButtonView(id, label, on_click)` | `(value: None, event) -> None` |

Group them into a titled, collapsible panel with `GroupView`:

```python
self.viz.add(
    GroupView(
        "Controls",
        [radius_view, reset_view],
        position="bottom-right",
    )
)
```

Handlers receive the new value plus a `ControlEvent`; use
`self.viz.update_entity(...)` / `self.viz.update(...)` then `flush()` to apply
changes. For the full control reference (all control kinds + parameters), see
[Controls](../interaction/controls.md).

## Complete example

See [`two_spheres_interact.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/interaction/two_spheres_interact.py)
for a full working app — two IPNS spheres with a moving slider, a visibility
dropdown, and a reset button. The full control reference is in
[Controls](../interaction/controls.md).
