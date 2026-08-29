# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Demo: Drag TWO 3D points interactively with :class:`ActPoint`.

Reproduces the multi-ActPoint interaction bug.  Two draggable points, each
with its own colour and three projection lines to the cardinal planes:

    Cyan    → XY plane (z=0)
    Magenta → XZ plane (y=0)
    Yellow  → YZ plane (x=0)

Modifier keys switch the drag constraint plane (per point)::

    no modifier  → view plane (screen-parallel)
    Shift        → XY plane (z-locked)
    Ctrl         → XZ plane (y-locked)
    Ctrl+Shift   → YZ plane (x-locked)

Usage::

    uv run python py/examples/viz/interaction/act_point_two.py

Keywords: interaction, ActPoint, drag, two points
"""

import asyncio

from pytanga.geometry import Line, Point
from pytanga.viz import ActPoint, CylinderLineStyle, Visualizer, VizObjectRef


class _ProjectionLines:
    """Three projection lines from a point to the cardinal planes."""

    def __init__(self, viz: Visualizer) -> None:
        self._viz = viz
        self.xy: VizObjectRef | None = None
        self.xz: VizObjectRef | None = None
        self.yz: VizObjectRef | None = None

    def update(self, p: Point) -> None:
        """Create/replace the three projection lines for position *p*."""
        xy_line = Line.from_points(p, Point(p.x, p.y, 0))
        if self.xy is None:
            self.xy = self._viz.new(xy_line, color="#00cccc", opacity=1.0)
        else:
            self.xy.entity = xy_line

        xz_line = Line.from_points(p, Point(p.x, 0, p.z))
        if self.xz is None:
            self.xz = self._viz.new(xz_line, color="#cc00cc", opacity=1.0)
        else:
            self.xz.entity = xz_line

        yz_line = Line.from_points(p, Point(0, p.y, p.z))
        if self.yz is None:
            self.yz = self._viz.new(yz_line, color="#cccc00", opacity=1.0)
        else:
            self.yz.entity = yz_line


async def main() -> None:
    viz = Visualizer(title="Drag Demo — Two ActPoints")

    # Render lines as solid cylinders (world-unit radius) instead of the
    # default screen-space fat lines.
    viz.styles["Line"] = CylinderLineStyle(thickness=0.03)

    lines_a = _ProjectionLines(viz)
    lines_b = _ProjectionLines(viz)

    # Custom handlers: update projection lines, then let ActPoint move the point.
    async def on_drag_a(event, ap):
        lines_a.update(event.world_position)
        return False  # let ActPoint do the default move + flush

    async def on_drag_b(event, ap):
        lines_b.update(event.world_position)
        return False  # let ActPoint do the default move + flush

    # Two interactive points — style is set via viz.new().
    ap_a = ActPoint(
        1,
        1,
        1,
        handler=on_drag_a,
    )
    ap_b = ActPoint(
        -1,
        -1,
        2,
        handler=on_drag_b,
    )
    viz.new(ap_a, color="#ff4444")
    viz.new(ap_b, color="#4488ff")

    # Initial projection lines
    lines_a.update(ap_a.point)
    lines_b.update(ap_b.point)

    # Start server + open browser
    if not viz.show(wait_for_browser=True):
        print("Failed to connect to browser. Exiting.")
        return
    viz.flush()
    print("Drag either point.  Shift→XY  Ctrl→XZ  Ctrl+Shift→YZ")
    print("Press Ctrl+C to exit.")

    try:
        await viz.wait_for_shutdown()
    finally:
        viz.stop_server()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        print(f"Error: {exc}")
