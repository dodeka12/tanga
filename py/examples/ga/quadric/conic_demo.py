# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""conic_demo.py — reconstruct a conic from 5 points and rotate it with a slider.

Embeds five points in the 2D projective quadric (conic) space, reconstructs the
conic through them as the grade-5 join of the point embeddings, and shows it in
the viewer.  Dragging the yellow point reshapes the conic; a slider rotates it
about the origin using the conic-space rotation rotor
``geo(Rotor(angle, Direction(0, 0, 1)))`` applied as ``R · conic · R̃``.

Run with:  uv run python py/examples/ga/quadric/conic_demo.py

Keywords: quadric, conic, rotor, conic_from_points, refine, analyze, slider
"""

import math

from typing import Any
from pytanga.algebra import MV
from pytanga.geometry import Direction, Geometry, Point, Rotor, analyze_operator
from pytanga.quadric import BasisQ2
from pytanga.viz import (
    ActPoint,
    ActSceneObject,
    Color,
    ControlEvent,
    DragEvent,
    GroupView,
    SceneView,
    SliderView,
    Visualizer,
)

# Five points on the ellipse  x²/4 + y² = 1  (no three collinear).

Q2 = BasisQ2(opns=True)
geo = Geometry(Q2)
p1 = geo(Point(1, 0, 0))
p2 = geo(Point(-1, 0, 0))
p3 = geo(Point(0, 1, 0))
p4 = geo(Point(0, -1, 0))

# The conic through the five points (before rotation) and the current rotation
# angle in radians.
base_conic = None
angle = 0.0
conic_viz = None
rotor_viz = None


def _rotated_conic() -> Any:
    """Return the base conic rotated by the current angle (R · conic · R̃)."""
    rotor = geo(Rotor(angle, Direction(0, 0, 1)))
    assert isinstance(rotor, MV), "a Rotor entity materialises one MV"
    assert base_conic is not None, "the base conic exists before the first render"
    return rotor.vp(base_conic)


async def on_drag_a(event: DragEvent, ap: ActSceneObject) -> bool:
    global base_conic
    # The point is dragged: rebuild the base conic and re-apply the rotor.
    base_conic = p1 ^ p2 ^ p3 ^ p4 ^ geo(ap)
    assert conic_viz is not None and rotor_viz is not None
    conic_viz.entity = _rotated_conic()
    # We did not move the point ourselves, so let the default behaviour run.
    return False


async def on_rotation(value: float, _event: ControlEvent) -> None:
    global angle
    angle = math.radians(float(value))
    assert base_conic is not None, "the base conic exists before the first render"
    rotor = geo(Rotor(angle, Direction(0, 0, 1)))
    assert isinstance(rotor, MV), "a Rotor entity materialises one MV"
    assert conic_viz is not None and rotor_viz is not None
    conic_viz.entity = rotor.vp(base_conic)
    rotor_viz.entity = analyze_operator(rotor)  # effective rotor (angle, axis)
    viz.flush()


ap_a = ActPoint(0.7, 0.7, 0, handler=on_drag_a)

base_conic = p1 ^ p2 ^ p3 ^ p4 ^ geo(ap_a)

viz = Visualizer(title="Tanga — conic through 5 points", space_dim=2)
for p, c in zip(
    [p1, p2, p3, p4, ap_a],
    [Color.RED, Color.GREEN, Color.BLUE, Color.MAGENTA, Color.YELLOW],
):
    viz.add(p, color=c)

conic_viz = viz.new(_rotated_conic())
rotor_viz = viz.new(Rotor(0.0, Direction(0, 0, 1)), label="Rotor")

viz.set_layout(
    SceneView(
        "",
        overlay=[
            GroupView(
                "Rotation",
                [
                    SliderView(
                        "angle",
                        label="Rotation (°)",
                        min=-180.0,
                        max=180.0,
                        step=1.0,
                        value=0.0,
                        on_change=on_rotation,
                    ),
                ],
                position="bottom-left",
            ),
        ],
    )
)

viz.set_annotation(
    "Drag the yellow point to reshape the conic; use the slider to rotate it."
)
viz.show()
viz.wait()
