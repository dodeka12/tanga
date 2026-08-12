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

Projection helpers::

    Use event.camera.project(point) to convert a world Point to
    screen pixel coordinates.  Use event.camera.unproject(screen_point, depth)
    to go the other way.  Both dispatch on Point vs Direction input.

Usage::

    uv run python py/examples/viz/demo_drag_point.py
"""

import asyncio
import logging

from pytanga.geometry import Line, Point
from pytanga.viz import Visualizer
from pytanga.viz._interaction import (
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

    # Build the scene — mutable pos for the handler
    pos = [0.0, 0.0, 2.0]

    # The draggable point
    point_id = viz.add(Point(*pos), color="#ff4444")

    # Projection lines to cardinal planes (updated on drag)
    #   Cyan   → XY plane (z=0)
    #   Magenta → XZ plane (y=0)
    #   Yellow  → YZ plane (x=0)
    line_xy_id: str | None = None
    line_xz_id: str | None = None
    line_yz_id: str | None = None

    def _update_lines(x: float, y: float, z: float) -> None:
        """Create/replace projection lines from (x,y,z) to the three planes."""
        nonlocal line_xy_id, line_xz_id, line_yz_id
        p = Point(x, y, z)

        # XY plane: set z=0
        xy_line = Line.from_points(p, Point(x, y, 0))
        if line_xy_id is None:
            line_xy_id = viz.add(xy_line, color="#00cccc", opacity=0.5)
        else:
            viz.update_entity(line_xy_id, xy_line)

        # XZ plane: set y=0
        xz_line = Line.from_points(p, Point(x, 0, z))
        if line_xz_id is None:
            line_xz_id = viz.add(xz_line, color="#cc00cc", opacity=0.5)
        else:
            viz.update_entity(line_xz_id, xz_line)

        # YZ plane: set x=0
        yz_line = Line.from_points(p, Point(0, y, z))
        if line_yz_id is None:
            line_yz_id = viz.add(yz_line, color="#cccc00", opacity=0.5)
        else:
            viz.update_entity(line_yz_id, yz_line)

    # Initial projection lines
    _update_lines(*pos)

    # Enable left-button dragging with multiple constraint planes
    viz.set_interaction(
        point_id,
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
        pos[0], pos[1], pos[2] = p.x, p.y, p.z
        viz.update_entity(event.object_id, p)
        _update_lines(p.x, p.y, p.z)

        # Example: project the world position to screen pixels
        # screen_xy = event.camera.project(p)
        # print(f"Screen: {screen_xy}")

        # Example: unproject a pixel offset to a world Direction
        # d = event.camera.unproject(Direction(10, 0, 0), depth=cam_dist)

        viz.flush()

    viz.on_interaction(point_id, InteractionEventType.DRAG_MOVE, on_drag)

    # Start server + open browser
    if not viz.start(wait_for_browser=True):
        print("Failed to connect to browser. Exiting.")
        return
    viz.flush()
    print("Drag the red point.  Shift→XY  Ctrl→XZ  Ctrl+Shift→YZ")
    print("Press Ctrl+C to exit.")

    # Block until interrupted (Ctrl+C handled by library's persistent handler)
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