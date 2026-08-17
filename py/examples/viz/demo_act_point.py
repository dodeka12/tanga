# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Demo: Drag a 3D point interactively with :class:`ActPoint`.

Left-click and drag the red point.  Three projection lines connect the
point to its footprints on the cardinal planes:

    Cyan   → XY plane (z=0)
    Magenta → XZ plane (y=0)
    Yellow  → YZ plane (x=0)

Modifier keys switch the drag constraint plane::

    no modifier  → view plane (screen-parallel)
    Shift        → XY plane (z-locked)
    Ctrl         → XZ plane (y-locked)
    Ctrl+Shift   → YZ plane (x-locked)

This demo uses :class:`ActPoint` which registers its own interaction
handlers automatically.  The point's visual style is set via the
``viz.new()`` call.  Hover highlighting (emissive glow + scale) is
applied automatically from the default ``ActPointStyle``.

Usage::

    uv run python py/examples/viz/demo_act_point.py
"""

import asyncio

# import logging
from pytanga.geometry import Line, Point
from pytanga.viz import CylinderLineStyle, Visualizer, VizObjectRef
from pytanga.viz._active import ActPoint

# logging.basicConfig(level=logging.INFO)  # everything
# logging.getLogger("tanga.viz.server").setLevel(logging.DEBUG)  # extra HTTP/WS detail


async def main() -> None:
    viz = Visualizer(title="Drag Demo — ActPoint")

    # Render lines as solid cylinders (world-unit radius) instead of the
    # default screen-space fat lines.
    viz.styles["Line"] = CylinderLineStyle(thickness=0.03)

    # Projection lines to cardinal planes (updated on drag).
    # ``new()`` returns a VizObjectRef; replace its ``.entity`` to update it.
    line_xy: VizObjectRef | None = None
    line_xz: VizObjectRef | None = None
    line_yz: VizObjectRef | None = None

    def _update_lines(p: Point) -> None:
        """Create/replace projection lines from point to the three planes."""
        nonlocal line_xy, line_xz, line_yz

        xy_line = Line.from_points(p, Point(p.x, p.y, 0))
        if line_xy is None:
            line_xy = viz.new(xy_line, color="#00cccc", opacity=1.0)
        else:
            line_xy.entity = xy_line

        xz_line = Line.from_points(p, Point(p.x, 0, p.z))
        if line_xz is None:
            line_xz = viz.new(xz_line, color="#cc00cc", opacity=1.0)
        else:
            line_xz.entity = xz_line

        yz_line = Line.from_points(p, Point(0, p.y, p.z))
        if line_yz is None:
            line_yz = viz.new(yz_line, color="#cccc00", opacity=1.0)
        else:
            line_yz.entity = yz_line

    # Custom handler: update projection lines, then let ActPoint move the point.
    async def on_point_drag(event, ap):
        p = event.world_position
        _update_lines(p)
        return False  # let ActPoint do the default move + flush

    # Create the interactive point — style is set via viz.new().
    ap = ActPoint(1, 1, 1, handler=on_point_drag)
    viz.new(ap, color="#ff4444")

    # Initial projection lines
    _update_lines(ap.point)

    # Start server + open browser
    if not viz.start(wait_for_browser=True):
        print("Failed to connect to browser. Exiting.")
        return
    viz.flush()
    print("Drag the red point.  Shift→XY  Ctrl→XZ  Ctrl+Shift→YZ")
    print("Press Ctrl+C to exit.")

    try:
        await viz.wait_for_shutdown()
    finally:
        viz.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        print(f"Error: {exc}")
