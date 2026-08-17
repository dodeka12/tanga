# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""demo_double_pendulum.py — A chaotic double pendulum from nested ``VizGroup``s.

Builds a two-link double pendulum out of *nested* scene-graph groups, exactly
like ``demo_nested_groups.py``::

    arm1  (top-level group — pivot at the world origin, the "ceiling")
    ├── rod1     segment hanging down from the pivot
    └── arm2     (group *nested inside* arm1, offset to the end of rod1)
        ├── rod2 segment hanging down from the end of rod1
        └── bob  point mass at the end of rod2

Each link rotates about its *own* pivot:

* ``arm1`` rotates ``rod1`` (and everything nested under it) about the ceiling
  pivot by the absolute angle ``theta1``.
* ``arm2`` rotates ``rod2`` about the joint at the end of rod1 by the relative
  angle ``theta2 - theta1``, so rod2's absolute angle is ``theta2``.

The pendulum state (``theta1``, ``theta2`` and their angular velocities) is
integrated each frame with the standard double-pendulum equations of motion;
only the two group transforms are re-serialized, so no rod geometry is ever
recomputed or re-sent.

Each rod's label is anchored to the *center* of the line via
``LabelStyle(along=0.5)`` — ``along`` is the fraction along the line's extent
(``0`` = start, ``0.5`` = midpoint, ``1`` = end).

Run with:  uv run python py/examples/viz/demo_double_pendulum.py
"""

import math

from pytanga.geometry import Line, Point
from pytanga.viz import LabelStyle, LineStyle, PointStyle, Visualizer

# ── Pendulum parameters ──────────────────────────────────────
M1 = 1.0  # mass at the end of rod1 (kg)
M2 = 1.0  # mass at the end of rod2 (kg)
L1 = 2.0  # length of rod1 (world units)
L2 = 1.5  # length of rod2 (world units)
G = 9.81  # gravity (world units / s^2)

# ── Integration / animation timing ───────────────────────────
FPS = 50          # visual frames per second
DT = 1.0 / FPS    # seconds per frame
STEPS = 4         # physics substeps per frame (for stability)
H = DT / STEPS    # integration step size (seconds)
DAMPING = 0.0     # per-second angular-velocity damping (0.0 = ideal / chaotic)
N_FRAMES = 600    # total frames (~12 s)

# ── Initial state: both rods released from horizontal, pointing at +x ──
THETA1_0 = math.pi / 2
THETA2_0 = math.pi / 2
OMEGA1_0 = 0.0
OMEGA2_0 = 0.0


def _accel(theta1, theta2, omega1, omega2):
    """Angular accelerations of the two links (standard double-pendulum EOM).

    ``theta1`` / ``theta2`` are measured from the downward vertical (positive
    toward +x).  Returns ``(alpha1, alpha2)``.
    """
    dtheta = theta1 - theta2
    sin_d = math.sin(dtheta)
    cos_d = math.cos(dtheta)
    denom = 2.0 * M1 + M2 - M2 * math.cos(2.0 * dtheta)

    alpha1 = (
        -G * (2.0 * M1 + M2) * math.sin(theta1)
        - M2 * G * math.sin(theta1 - 2.0 * theta2)
        - 2.0 * sin_d * M2 * (omega2**2 * L2 + omega1**2 * L1 * cos_d)
    ) / (L1 * denom)

    alpha2 = (
        2.0
        * sin_d
        * (
            omega1**2 * L1 * (M1 + M2)
            + G * (M1 + M2) * math.cos(theta1)
            + omega2**2 * L2 * M2 * cos_d
        )
    ) / (L2 * denom)

    return alpha1, alpha2


viz = Visualizer(title="Tanga — Double Pendulum")
viz.start()

# ── arm1: pivot at the world origin (the ceiling anchor) ─────
# Both rods are drawn hanging straight *down* (the −y direction); rotation is
# about the z axis, so a positive angle swings the rod toward +x.
arm1 = viz.add_group("arm1")
arm1.new(Point(0, 0, 0), color="#ffaa00", label="pivot1", style=PointStyle(size=0.10))
arm1.new(
    Line.from_points(Point(0, 0, 0), Point(0, -L1, 0)),
    color="#ff5555",
    label="rod1",
    label_style=LabelStyle(along=0.5),  # anchor label at the line's midpoint
    style=LineStyle(thickness=3.0),
)

# ── arm2: nested inside arm1, offset to the end of rod1 ──────
arm2 = arm1.add_group("arm2")
arm2.set_transform(position=(0.0, -L1, 0.0))
arm2.new(Point(0, 0, 0), color="#ffaa00", label="pivot2", style=PointStyle(size=0.09))
arm2.new(
    Line.from_points(Point(0, 0, 0), Point(0, -L2, 0)),
    color="#5599ff",
    label="rod2",
    label_style=LabelStyle(along=0.5),  # anchor label at the line's midpoint
    style=LineStyle(thickness=3.0),
)
arm2.new(Point(0, -L2, 0), color="#44ff44", label="bob", style=PointStyle(size=0.14))

viz.flush()

theta1, theta2 = THETA1_0, THETA2_0
omega1, omega2 = OMEGA1_0, OMEGA2_0

print("Simulating the double pendulum for ~12 seconds...")
for _ in range(N_FRAMES):
    for _ in range(STEPS):
        alpha1, alpha2 = _accel(theta1, theta2, omega1, omega2)
        omega1 += alpha1 * H
        omega2 += alpha2 * H
        if DAMPING:
            omega1 *= 1.0 - DAMPING * H
            omega2 *= 1.0 - DAMPING * H
        theta1 += omega1 * H
        theta2 += omega2 * H

    # arm1 rotates rod1 + arm2 + rod2 about the ceiling pivot.
    arm1.set_transform(rotation=(0.0, 0.0, theta1))

    # arm2 rotates rod2 about the joint by the *relative* angle theta2 - theta1,
    # compounding with arm1 so rod2's absolute angle is theta2.
    arm2.set_transform(rotation=(0.0, 0.0, theta2 - theta1))

    viz.flush()
    viz.sleep_ms(int(1000 / FPS))

viz.stop()
print("Animation stopped.")
