# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""quadric3d_demo.py — reconstruct a quadric from 9 points and rotate it.

Embeds nine points in the 3D projective quadric space and reconstructs the
quadric through them as the **join** of the point embeddings (the smallest blade
containing all nine).  Dragging any of the three yellow action points reshapes
the quadric; two sliders choose the rotation axis (azimuth + polar angle) and
one sets the rotation angle, using the quadric-space rotation rotor
``geo(Rotor(angle, axis))`` applied as ``R · quadric · R̃``.  The effective rotor
is analysed back to ``Rotor(angle, axis)`` and drawn as an axis + arc.

A dropdown switches the point set:

- ``Ellipsoid`` — the initial 9 points on an ellipsoid (semi-axes 2, 1.3, 0.7).
- ``Cube`` — the 8 corners of a (±0.5)³ cube plus the centre point.  An *exact*
  cube + centre is degenerate: its 9 embeddings span only 8 dimensions, so the
  join is a grade-8 blade (not the grade-9 quadric).  ``analyze`` treats a
  grade-8 join as the degenerate case: its dual is the grade-2 IPNS pencil of
  quadrics through the 9 points, resolved to its plane-pair members (the four
  body diagonals).

Nine points in general position determine a unique quadric (9 dof — 10
homogeneous coefficients up to scale); three draggable points (3×3 = 9 dof)
therefore reach a full open set of quadrics.

Run with:  uv run python py/examples/ga/quadric/quadric3d_demo.py

Keywords: quadric, quadric3d, rotor, slider, dropdown, ellipsoid, join, analyze
"""

import functools
import math

from pytanga.geometry import Direction, Geometry, Point, Rotor, analyze_operator
from pytanga.quadric import BasisQ3
from pytanga.viz import (
    ActPoint,
    Color,
    ControlEvent,
    DragEvent,
    DropdownView,
    GroupView,
    SceneView,
    SliderView,
    Visualizer,
)

Q3 = BasisQ3(opns=True)
geo = Geometry(Q3)

# Two 9-point distributions: six fixed points plus three action points each.
DISTRIBUTIONS = {
    "Ellipsoid": {
        # x²/4 + y²/1.69 + z²/0.49 = 1  (semi-axes 2, 1.3, 0.7).
        "fixed": [
            (2.0000, 0.0000, 0.0000),
            (-0.8323, 1.1821, 0.0000),
            (-1.3073, -0.9838, 0.0000),
            (0.9826, 0.9947, -0.2913),
            (-1.1887, -0.8946, -0.2913),
            (-1.1180, 0.1036, 0.5777),
        ],
        "action": [
            (1.4769, 0.5244, 0.3782),
            (-1.3483, 0.6547, 0.3782),
            (0.2925, -0.6426, -0.5998),
        ],
    },
    "Cube": {
        # 8 corners of the (±0.5) cube plus the centre — an *exact* cube is
        # degenerate (the join is grade 8), resolved to the plane-pair
        # intersection (the four body diagonals).
        "fixed": [
            (-0.5, -0.5, -0.5),
            (0.5, -0.5, -0.5),
            (-0.5, 0.5, -0.5),
            (0.5, 0.5, -0.5),
            (-0.5, -0.5, 0.5),
            (0.5, -0.5, 0.5),
        ],
        "action": [
            (-0.5, 0.5, 0.5),
            (0.5, 0.5, 0.5),
            (0.0, 0.0, 0.0),
        ],
    },
}

# Mutable state: the six fixed-point MVs and their viz refs, the base quadric,
# and the rotation state (azimuth, polar angle, angle — all radians).
fixed = []
fixed_refs = []
base_quadric = None
azimuth = 0.0
polar = math.pi / 2.0
angle = 0.0
quadric_viz = None
rotor_viz = None


def _axis():
    """Rotation axis from the current azimuth/polar angles."""
    sp = math.sin(polar)
    return Direction(sp * math.cos(azimuth), sp * math.sin(azimuth), math.cos(polar))


def _rotor():
    return geo(Rotor(angle, _axis()))


def _points():
    """The nine point MVs: six fixed points plus the three action points."""
    return [*fixed, geo(ap1), geo(ap2), geo(ap3)]


def _join_blade():
    """The join (smallest containing blade) of the nine point embeddings.

    Generic points give a grade-9 blade (the quadric); a degenerate set such as
    the exact cube gives a grade-8 blade (the pencil's span).  ``analyze``
    resolves both — a grade-8 join is the degenerate case, whose dual grade-2
    pencil is analysed as a quadric intersection (see ``quadric._analysis``).
    """
    return functools.reduce(lambda a, c: a.join(c), _points())


def _rebuild():
    """Rebuild the quadric through the six fixed + three action points."""
    global base_quadric
    base_quadric = _join_blade()


def _apply_rotation(*, flush: bool = True) -> None:
    rotor = _rotor()
    quadric_viz.entity = rotor.vp(base_quadric)
    rotor_viz.entity = analyze_operator(rotor)  # effective rotor (angle, axis)
    if flush:
        viz.flush()


def _set_distribution(name: str, *, flush: bool = True) -> None:
    """Place the points for *name* and rebuild the quadric."""
    global base_quadric
    dist = DISTRIBUTIONS[name]
    fixed[:] = [geo(Point(*p)) for p in dist["fixed"]]
    for ref, p in zip(fixed_refs, dist["fixed"]):
        ref.entity = Point(*p)
    for ap, p in zip((ap1, ap2, ap3), dist["action"]):
        ap._move_to(Point(*p))
        ap.update()
    _rebuild()
    _apply_rotation(flush=flush)


async def on_drag(event: DragEvent, ap: ActPoint) -> bool:
    _rebuild()
    _apply_rotation(flush=False)
    # We did not move the point ourselves, so let the default behaviour run.
    return False


async def on_distribution(value: str, _event: ControlEvent) -> None:
    _set_distribution(value)


async def on_azimuth(value: float, _event: ControlEvent) -> None:
    global azimuth
    azimuth = math.radians(float(value))
    _apply_rotation()


async def on_polar(value: float, _event: ControlEvent) -> None:
    global polar
    polar = math.radians(float(value))
    _apply_rotation()


async def on_angle(value: float, _event: ControlEvent) -> None:
    global angle
    angle = math.radians(float(value))
    _apply_rotation()


ell = DISTRIBUTIONS["Ellipsoid"]
ap1 = ActPoint(*ell["action"][0], handler=on_drag)
ap2 = ActPoint(*ell["action"][1], handler=on_drag)
ap3 = ActPoint(*ell["action"][2], handler=on_drag)

fixed[:] = [geo(Point(*p)) for p in ell["fixed"]]
base_quadric = _join_blade()

viz = Visualizer(title="Tanga — quadric through 9 points")
for p in fixed:
    fixed_refs.append(viz.new(p, color=Color.BLUE))
for ap in (ap1, ap2, ap3):
    viz.add(ap, color=Color.YELLOW)

quadric_viz = viz.new(base_quadric)
rotor_viz = viz.new(analyze_operator(_rotor()), label="Rotor")

viz.set_layout(
    SceneView(
        "",
        overlay=[
            GroupView(
                "Point set",
                [
                    DropdownView(
                        "distribution",
                        label="Distribution",
                        options=list(DISTRIBUTIONS),
                        value="Ellipsoid",
                        on_change=on_distribution,
                    ),
                ],
                position="top-left",
            ),
            GroupView(
                "Rotation",
                [
                    SliderView(
                        "azimuth",
                        label="Azimuth (°)",
                        min=0.0,
                        max=360.0,
                        step=1.0,
                        value=0.0,
                        on_change=on_azimuth,
                    ),
                    SliderView(
                        "polar",
                        label="Polar (°)",
                        min=0.0,
                        max=180.0,
                        step=1.0,
                        value=90.0,
                        on_change=on_polar,
                    ),
                    SliderView(
                        "angle",
                        label="Rotation (°)",
                        min=-180.0,
                        max=180.0,
                        step=1.0,
                        value=0.0,
                        on_change=on_angle,
                    ),
                ],
                position="bottom-left",
            ),
        ],
    )
)

viz.set_annotation(
    "Drag a yellow point to reshape the quadric; use the dropdown to change the "
    "point set and the sliders to rotate it."
)
viz.show()
viz.wait()
