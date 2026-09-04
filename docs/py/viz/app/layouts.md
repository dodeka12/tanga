# Layouts — Split Views & Controls

A `VisualizerApp` exposes the split-view and control machinery through its
`self.viz` attribute (a plain `Visualizer`), so you can build a multi-pane
layout with embedded controls and drive it from async handlers — all within the
managed lifecycle (`init` → block → `cleanup`).

For the underlying view model (sizes, splitters, panes), see
[Split Views](../visualizer/split-views.md); for the panel-control methods, see
[Controls](../interaction/controls.md).

The plain scene URL that `VisualizerApp.run()` opens is itself a one-`SceneView`
layout, so a `GroupView` overlay (or any control view mounted via `viz.add`)
renders there exactly as it does inside a custom split layout — the two modes
share one render path.

Flow containers (`StackView`/`GroupView`) accept `gap`/`align`/`justify`, and a
child's `preferred_*` maps to CSS flex (e.g. `Size.fr(1)` fills the leftover
space beside a button). See [Split Views](../visualizer/split-views.md) for the
sizing model and the flex mapping table.

## Controls in a layout

Controls are declarative `*View` classes placed in a `GroupView`/`StackView`
pane (or mounted in the overlay via `viz.add(view)`):

| API | Where it appears | Use for |
|-----|------------------|---------|
| `SliderView` / `DropdownView` / `ButtonView` / `GroupView` (inside a `GroupView`/`StackView`) | A pane in your `SplitView` layout | A sidebar/toolbar next to one or more scene panes |
| `viz.add(view)` | The default layout's overlay | Quick controls over a scene without a custom layout |

The **async** handler contract is `(value, event)`. The declarative view classes
are documented in full in [Control Views (xxxView)](../interaction/control-views.md).

## A split-view app

Build the layout, register it, and open it under a single URL. `VisualizerApp`
does not open layouts by default (its `run()` opens the plain scene URL), so
override `run()` to open the layout instead:

```python
import asyncio

from pytanga.geometry import Point, Sphere
from pytanga.viz import (
    ButtonView,
    CameraConfig3d,
    ControlEvent,
    GroupView,
    SceneView,
    Size,
    SliderView,
    SplitView,
    VisualizerApp,
)


class MyApp(VisualizerApp):
    def __init__(self):
        super().__init__(title="My Split-View App")
        self._layout = self._build_layout()

    def _build_layout(self):
        # Keep the main pane so a button can re-aim its camera at runtime.
        self._main_view = SceneView("")
        return SplitView(
            orientation="horizontal",
            children=[
                GroupView(
                    "Controls",
                    [
                        SliderView(
                            "radius",
                            label="Radius",
                            min=0.2,
                            max=5.0,
                            value=1.0,
                            on_change=self.on_radius,
                        ),
                        ButtonView("btn_topdown", label="Top-down", on_click=self.on_topdown),
                        ButtonView("btn_quit", label="Quit", on_click=self.on_quit),
                    ],
                ),
                SplitView(
                    orientation="vertical",
                    sizes=[Size.percent(70), Size.percent(30)],
                    children=[
                        self._main_view,
                        # The same scene from a different initial camera — each
                        # pane keeps its own orbit/zoom.
                        SceneView(
                            "",
                            camera=CameraConfig3d(
                                position=(8.0, 0.0, 0.0), target=(0.0, 0.0, 0.0)
                            ),
                        ),
                    ],
                ),
            ],
        )

    def run(self, *, wait_for_browser=True, timeout=30.0):
        # Open the layout URL instead of the plain scene URL.  ``show(layout=…)``
        # also registers the layout (and its control-view handlers).
        ok = self.viz.show(layout=self._layout, wait_for_browser=wait_for_browser)
        if not ok:
            raise RuntimeError(
                "Server failed to start or no browser connected. "
                f"Open {self.viz.url} manually."
            )
        try:
            asyncio.run(self._app_main())
        except KeyboardInterrupt:
            pass
        finally:
            self.viz.stop_server()

    async def init(self) -> None:
        self._sphere = self.viz(Sphere(Point(0, 0, 0), radius=1.0), opacity=0.3)
        self.viz.flush()

    async def on_radius(self, value: float, _event: ControlEvent) -> None:
        self.viz.update_entity(self._sphere.id, Sphere(Point(0, 0, 0), radius=value))
        self.viz.flush()

    async def on_topdown(self, _value, _event) -> None:
        self.viz.set_view_camera(
            self._main_view,
            CameraConfig3d(position=(0.0, 8.0, 0.0), target=(0.0, 0.0, 0.0)),
        )

    async def on_quit(self, _value, _event) -> None:
        self.request_shutdown()

    async def cleanup(self) -> None:
        pass  # teardown


if __name__ == "__main__":
    MyApp().run()
```

Key points:

- **Handlers are registered automatically.** `show(layout=…)` → `set_layout(...)`
  walks the view tree and registers each control view's `on_change`/`on_click`,
  so a `SliderView`/`ButtonView` behaves exactly like a panel control.
- **`SceneView("")` is the main scene.** A second `SceneView("")` shows the same
  scene from a different initial camera; each pane keeps its own orbit/zoom.
- **`set_view_camera(view, camera)`** re-aims one pane at runtime (targeted by
  the `SceneView` instance), without touching the scene or its other panes.

## Multiple scenes in a layout

`SceneView` references a scene by name (or `VizSceneHandle`). Create named
scenes **before** `run()` so they exist when the layout browser connects:

```python
def __init__(self):
    super().__init__(title="Multi-scene app")
    self._detail = self.viz.scene("detail")   # create before the browser connects
    self._layout = SplitView(
        "horizontal",
        [SceneView(""), SceneView("detail")],
    )

async def init(self):
    self._detail.add(Point(2, 0, 0), color="#44ff44")
    self.viz.flush()
```

Controls live in layouts, not scenes: place them in whichever pane's
`GroupView`/`StackView` (or overlay) you want.

## See Also

- [Split Views](../visualizer/split-views.md) — the view hierarchy, `Size` units,
  splitters, overlays, and per-pane cameras
- [Controls](../interaction/controls.md) — `SliderView`/`DropdownView`/`ButtonView`/`GroupView`
- [Handlers & Lifecycle](handlers.md) — the handler contract and the app lifecycle

