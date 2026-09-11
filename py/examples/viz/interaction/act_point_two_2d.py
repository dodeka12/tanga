# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Demo: Drag TWO 2D points interactively with :class:`ActPoint`.

Reproduces the multi-ActPoint interaction bug in 2D mode.  Two draggable
points in an orthographic 2D view, each with its own colour.

Modifier keys switch the drag constraint plane (per point)::

    no modifier  → view plane (screen-parallel)
    Shift        → XY plane (z-locked)
    Ctrl         → XZ plane (y-locked)
    Ctrl+Shift   → YZ plane (x-locked)

Usage::

    uv run python py/examples/viz/interaction/act_point_two_2d.py

Keywords: interaction, ActPoint, drag, click, 2D, two points
"""

import asyncio

from pytanga.viz import (
    ActPoint,
    ClickEvent,
    DragEvent,
    View2DConfig,
    Visualizer,
)


async def on_drag_start(ev: DragEvent, control: ActPoint) -> None:
    print(f"Drag started: {ev.world_position} (screen: {ev.screen_position})")


async def on_drag_end(ev: DragEvent, control: ActPoint) -> None:
    print(f"Drag ended: {ev.world_position} (screen: {ev.screen_position})")


async def on_click(ev: ClickEvent, control: ActPoint) -> None:
    print(f"Clicked: {ev.world_position} (screen: {ev.screen_position})")


async def main() -> None:
    viz = Visualizer(
        title="Drag Demo — Two ActPoints (2D)",
        space_dim=2,
        camera=View2DConfig(xmin=-3.0, xmax=3.0, ymin=-2.0, ymax=2.0),
    )

    # Two interactive points — style is set via viz.new().
    ap_a = ActPoint(
        1.0,
        0.5,
        0.0,
        on_click=on_click,
        on_drag_start=on_drag_start,
        on_drag_end=on_drag_end,
    )
    ap_b = ActPoint(-1.0, -0.5, 0.0)
    viz.new(ap_a, color="#ff4444")
    viz.new(ap_b, color="#4488ff")

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
