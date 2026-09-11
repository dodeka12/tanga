# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""motor_group_transform.py — Drive a VizGroup transform from a BasisN3 Motor.

Builds a motor in the BasisN3 (N3) algebra and uses it to drive a ``VizGroup``:
the initial placement is *set* from the motor's multivector, then a fresh motor
is *applied* (composed) each frame to keep the group spinning. ``set_transform``
and ``apply_transform`` accept the same inputs — a ``Transform``, an ``MV``, or
a GA operator (``Rotor``/``GeneralRotor``/``Motor``/``Translator``/``Dilator``).

Run with:  uv run python py/examples/viz/scenes/motor_group_transform.py

Keywords: BasisN3, Motor, VizGroup, Transform, scene graph, animation
"""

import math

from pytanga.basis import BasisN3
from pytanga.geometry import Direction, Geometry, Line, Motor, Point, Rotor, Translator
from pytanga.viz import LineStyle, PointStyle, Visualizer, VizGroup

N3 = BasisN3()
geo = Geometry(N3)


def motor_mv(angle: float):
    """A BasisN3 (N3) motor as a multivector.

    Rotate about +Z while translating in the XY plane, built through the
    BasisN3 algebra and returned as its ``MV`` — one of the inputs that both
    ``set_transform`` and ``apply_transform`` accept.
    """
    return geo.create(
        Motor(
            Rotor(angle, Direction(0, 0, 1)),
            Translator(0.05 * Direction(math.sin(angle), math.cos(angle), 0)),
        )
    )


viz = Visualizer(title="Tanga — Motor-driven VizGroup transform")
viz.show()

# Initialize the group's transform from a BasisN3 motor (set = replace).
body = VizGroup("spinner")
body_ref = viz.new(body)
body_ref.set_transform(motor_mv(0.0))  # initial placement

# Children live in the group's local frame, so spinning the group spins them too.
body_ref.new(
    Point(0, 0, 0), color="#ffaa00", label="pivot", style=PointStyle(size=0.10)
)
body_ref.new(
    Line.from_points(Point(0, 0, 0), Point(1.5, 0, 0)),
    color="#ff5555",
    label="rod",
    style=LineStyle(thickness=3.0),
)
body_ref.new(
    Point(1.5, 0, 0), color="#44ff44", label="tip", style=PointStyle(size=0.12)
)

viz.flush()

print("A rod + tip group spins, driven by a BasisN3 Motor.")
print("set_transform() sets the initial placement; apply_transform() composes")
print("each frame. Close the browser window or press Ctrl+C to exit.")

print("Starting animation...", flush=True)
speed = 1.2  # rad/s
fps = 30  # frames per second
delta_motor = motor_mv(speed / fps)  # incremental motor per second
for dt in viz.animate(fps=fps):
    # Compose an incremental motor onto the group's current transform.
    body_ref.apply_transform(delta_motor)
    viz.flush()

print("Animation stopped.")
viz.stop_server()
