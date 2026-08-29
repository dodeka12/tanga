# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Demo: Drag a 3D point interactively with the mouse.

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

This demo uses the low-level interaction API directly, giving full
control over triggers and handlers.

Usage::

    uv run python py/examples/viz/interaction/drag_point.py

Keywords: interaction, drag, point, constraints, low-level
"""

import asyncio
import logging

from pytanga.geometry import Line, Point
from pytanga.viz import Visualizer, VizObjectRef
from pytanga.viz import (
    DragMode,
    InteractionConfig,
    InteractionEventType,
    InteractionTrigger,
    ModifierKey,
    MouseButton,
)

logging.basicConfig(level=logging.INFO)  # everything
logging.getLogger("tanga.viz.server").setLevel(logging.DEBUG)  # extra HTTP/WS detail


async def main() -> None:
    viz = Visualizer(title="Drag Demo — Grab the red point")

    # The draggable point
    pos = Point(0, 0, 2)
    point = viz.new(pos, color="#ff4444")

    # Projection lines to cardinal planes (updated on drag).
    # `new()` returns a VizObjectRef; replace its `.entity` to update it.
    line_xy: VizObjectRef | None = None
    line_xz: VizObjectRef | None = None
    line_yz: VizObjectRef | None = None

    def _update_lines(p: Point) -> None:
        """Create/replace projection lines from (x,y,z) to the three planes."""
        nonlocal line_xy, line_xz, line_yz

        # XY plane: set z=0
        xy_line = Line.from_points(p, Point(p.x, p.y, 0))
        if line_xy is None:
            line_xy = viz.new(xy_line, color="#00cccc", opacity=1.0)
        else:
            line_xy.entity = xy_line

        # XZ plane: set y=0
        xz_line = Line.from_points(p, Point(p.x, 0, p.z))
        if line_xz is None:
            line_xz = viz.new(xz_line, color="#cc00cc", opacity=1.0)
        else:
            line_xz.entity = xz_line

        # YZ plane: set x=0
        yz_line = Line.from_points(p, Point(0, p.y, p.z))
        if line_yz is None:
            line_yz = viz.new(yz_line, color="#cccc00", opacity=1.0)
        else:
            line_yz.entity = yz_line

    # Initial projection lines
    _update_lines(pos)

    # Enable left-button dragging with multiple constraint planes
    point.set_interaction(
        InteractionConfig(
            enabled=True,
            triggers=[
                InteractionTrigger(
                    event_type=InteractionEventType.DRAG,
                    mouse_button=MouseButton.LEFT,
                    drag_mode=DragMode.VIEW_PLANE,
                ),
                InteractionTrigger(
                    event_type=InteractionEventType.DRAG,
                    mouse_button=MouseButton.LEFT,
                    modifiers=frozenset({ModifierKey.SHIFT}),
                    drag_mode=DragMode.XY_PLANE,
                ),
                InteractionTrigger(
                    event_type=InteractionEventType.DRAG,
                    mouse_button=MouseButton.LEFT,
                    modifiers=frozenset({ModifierKey.CTRL}),
                    drag_mode=DragMode.XZ_PLANE,
                ),
                InteractionTrigger(
                    event_type=InteractionEventType.DRAG,
                    mouse_button=MouseButton.LEFT,
                    modifiers=frozenset({ModifierKey.CTRL, ModifierKey.SHIFT}),
                    drag_mode=DragMode.YZ_PLANE,
                ),
            ],
            throttle_ms=40,
        ),
    )

    async def on_drag(event):
        # event.world_position is a pytanga.geometry.Point
        p = event.world_position
        point.entity = p
        _update_lines(p)
        viz.flush()

    point.on_interaction(InteractionEventType.DRAG_MOVE, on_drag)

    # Start server + open browser
    if not viz.show(wait_for_browser=True):
        print("Failed to connect to browser. Exiting.")
        return
    viz.flush()
    print("Drag the red point.  Shift→XY  Ctrl→XZ  Ctrl+Shift→YZ")
    print("Press Ctrl+C to exit.")

    # Block until interrupted (Ctrl+C handled by library's persistent handler)
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
