# VisualizerApp with a sin/cos split view and draggable points

**Keywords:** app · split view · ActPoint · drag · CoordinateSystem · plotting

Builds a `~pytanga.viz.SplitView` layout inside a
`~pytanga.viz.VisualizerApp`:

- a horizontal split whose **left** pane is a vertical split of two 2D plots
  (`sin` and `cos`), each rendered by a
  `~pytanga.viz.CoordinateSystem`;
- a **right** pane showing a 2D scene with four
  `~pytanga.viz.ActPoint` corners joined by lines — dragging a corner
  updates the two adjacent lines;
- the `sin` pane additionally holds an amplitude
  `~pytanga.viz.ActPoint` whose Y coordinate sets the `sin` amplitude
  and re-plots the curve live.

This doubles as a test bed for per-pane interaction, pane-aspect 2D framing,
the `fit_view2d` helper, and per-scene grid/axes opt-out.

## Run

```bash
uv run python py/examples/viz/app/split_view_app.py
```

## Source

[`viz/app/split_view_app.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/app/split_view_app.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""split_view_app.py — VisualizerApp with a sin/cos split view and draggable points.

Builds a :class:`~pytanga.viz.SplitView` layout inside a
:class:`~pytanga.viz.VisualizerApp`:

- a horizontal split whose **left** pane is a vertical split of two 2D plots
  (``sin`` and ``cos``), each rendered by a
  :class:`~pytanga.viz.CoordinateSystem`;
- a **right** pane showing a 2D scene with four
  :class:`~pytanga.viz.ActPoint` corners joined by lines — dragging a corner
  updates the two adjacent lines;
- the ``sin`` pane additionally holds an amplitude
  :class:`~pytanga.viz.ActPoint` whose Y coordinate sets the ``sin`` amplitude
  and re-plots the curve live.

This doubles as a test bed for per-pane interaction, pane-aspect 2D framing,
the ``fit_view2d`` helper, and per-scene grid/axes opt-out.

Run with:  uv run python py/examples/viz/app/split_view_app.py

Keywords: app, split view, ActPoint, drag, CoordinateSystem, plotting
"""

import asyncio
import math

from pytanga.geometry import Line, Point
from pytanga.viz import (
    ActPoint,
    CoordinateSystem,
    DragMode,
    PointPath,
    PointPathStyle,
    PointStyle,
    SceneView,
    Size,
    SplitView,
    View2DConfig,
    VisualizerApp,
    VizObjectRef,
    fit_view2d,
)

_X_MIN = 0.0
_X_MAX = 2.0 * math.pi
_Y_MIN = -1.2
_Y_MAX = 1.2
_AMP_X = 1.5  # fixed x of the amplitude control point
_AMP0 = 1.0  # initial amplitude
_AMP_MIN = 0.05
_AMP_MAX = 1.5


class SplitViewApp(VisualizerApp):
    """A split-view app: sin/cos plots on the left, a draggable polygon on the right."""

    def __init__(self) -> None:
        super().__init__(
            title="Tanga — Split-View Plot & Drag",
            space_dim=2,
            add_default_axes=False,
            add_default_grid=False,
        )
        # Named scenes must exist before run() opens the layout.
        self._sin_scene = self.viz.scene("sin", add_axes=False, add_grid=False)
        self._cos_scene = self.viz.scene("cos", add_axes=False, add_grid=False)

        self._xs = [0.05 * i for i in range(int(_X_MAX / 0.05) + 1)]
        self._amplitude = _AMP0
        self._sin_path = PointPath()
        self._sin_cs: CoordinateSystem | None = None
        self._amp: ActPoint | None = None
        self._points: list[ActPoint] = []
        self._lines: list[VizObjectRef] = []

        self._layout = self._build_layout()

    def _build_layout(self) -> SplitView:
        sin_view = SceneView(
            "sin", camera=fit_view2d((_X_MIN, _X_MAX), (_Y_MIN, _Y_MAX))
        )
        cos_view = SceneView(
            "cos", camera=fit_view2d((_X_MIN, _X_MAX), (_Y_MIN, _Y_MAX))
        )
        main_view = SceneView(
            "", camera=View2DConfig(xmin=-3.0, xmax=3.0, ymin=-3.0, ymax=3.0)
        )
        return SplitView(
            "horizontal",
            [
                SplitView(
                    "vertical",
                    sizes=[Size.percent(50), Size.percent(50)],
                    children=[sin_view, cos_view],
                ),
                main_view,
            ],
        )

    def run(
        self,
        *,
        wait_for_browser: bool = True,
        timeout: float = 30.0,
        port: int | None = None,
        host: str | None = None,
    ) -> None:
        ok = self.viz.show(
            layout=self._layout,
            wait_for_browser=wait_for_browser,
            timeout=timeout,
            port=port,
            host=host,
        )
        if not ok:
            raise RuntimeError(
                "Server failed to start or no browser connected "
                f"within {timeout}s.  Open {self.viz.url} manually."
            )
        try:
            asyncio.run(self._app_main())
        except KeyboardInterrupt:
            pass
        finally:
            self.viz.stop_server()

    async def init(self) -> None:
        self._sin_cs = CoordinateSystem(
            self._sin_scene,
            xlim=(_X_MIN, _X_MAX),
            ylim=(_Y_MIN, _Y_MAX),
            labels=("x", "sin(x)"),
            camera=False,
        )
        self._cos_cs = CoordinateSystem(
            self._cos_scene,
            xlim=(_X_MIN, _X_MAX),
            ylim=(_Y_MIN, _Y_MAX),
            labels=("x", "cos(x)"),
            camera=False,
        )

        # Live sin plot (amplitude-driven) + static cos plot.
        self._fill_sin_path()
        self._sin_cs.add_plot(self._sin_path, style=PointPathStyle(line_thickness=2))
        self._cos_cs.plot(
            self._xs,
            [math.cos(x) for x in self._xs],
            style=PointPathStyle(line_thickness=2),
        )

        # Amplitude control point (its Y coordinate is the sin amplitude).
        self._amp = ActPoint(
            _AMP_X,
            self._amplitude,
            0.0,
            drag_mode=DragMode.XY_PLANE,
            on_drag_end=self._on_amp_drag_end,
        )
        self._sin_scene.new(self._amp, color="#ffcc00", style=PointStyle(size=0.15))

        # Four draggable corners + connecting lines in the main pane.
        corners = [(-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, 1.0)]
        for i, (x, y) in enumerate(corners):
            ap = ActPoint(
                x, y, 0.0, drag_mode=DragMode.XY_PLANE, handler=self._line_handler(i)
            )
            self._points.append(ap)
            self.viz.new(ap, color="#ff4444", style=PointStyle(size=0.15))
        for i in range(len(self._points)):
            j = (i + 1) % len(self._points)
            line = Line.from_points(self._points[i].point, self._points[j].point)
            self._lines.append(self.viz.new(line, color="#44ff44", opacity=0.9))

        self.viz.flush()

    def _fill_sin_path(self) -> None:
        self._sin_path.clear()
        for x in self._xs:
            self._sin_path.add((x, self._amplitude * math.sin(x)))

    async def _on_amp_drag_end(self, _event, ap: ActPoint) -> None:
        amp = min(max(ap.point.y, _AMP_MIN), _AMP_MAX)
        self._amplitude = amp
        self._fill_sin_path()
        self._sin_cs.update_plots()
        self._sin_scene.flush()

    def _line_handler(self, i: int):
        async def handler(event, _ap: ActPoint):
            self._update_lines(i, event.world_position)
            return False  # let ActPoint move the point and flush

        return handler

    def _update_lines(self, i: int, pos: Point) -> None:
        n = len(self._points)
        for k in (i, (i - 1) % n):
            j = (k + 1) % n
            a = pos if k == i else self._points[k].point
            b = pos if j == i else self._points[j].point
            self._lines[k].entity = Line.from_points(a, b)

    async def cleanup(self) -> None:
        pass


if __name__ == "__main__":
    SplitViewApp().run()
````
