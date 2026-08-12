# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""two_body_gravity.py — Gravitational two-body simulation using only
Point and Direction for vector arithmetic.

Two massive bodies orbit each other under Newtonian gravity.
All calculations use ``Point`` and ``Direction`` operators
(+, -, *, /) and methods (dot, cross, mag, norm) — no raw
floats for vector components except at initialisation.

Run with:  uv run python py/examples/viz/two_body_gravity.py
"""

from pytanga.geometry import Direction, Point
from pytanga.viz import PointStyle, Visualizer

# ═══════════════════════════════════════════════════════════════
# Simulation parameters
# ═══════════════════════════════════════════════════════════════

G = 2.0  # gravitational constant (tuned for visual appeal)
DT = 0.02
DT_MS = DT * 1000  # time step (~60 FPS)
TOTAL_FRAMES = 600  # ~10 seconds

# Body 1 — heavy, starts near origin
mass_1 = 5.0
pos_1 = Point(2.0, 0.0, 0.0)
vel_1 = Direction(0.0, 0.5, 0.0)

# Body 2 — lighter, opposite side
mass_2 = 1.0
pos_2 = Point(-2.0, 0.0, 0.0)
vel_2 = Direction(0.5, -0.5, 0.0)

# ═══════════════════════════════════════════════════════════════
# Visualisation setup
# ═══════════════════════════════════════════════════════════════

viz = Visualizer(title="Tanga — Two-Body Gravitational Simulation")
viz.start()

# Coordinate axes for reference
viz.add(
    Point(0, 0, 0),
    label="origin",
    style=PointStyle(
        size=0.12,
        color="#333333",
    ),
)

# Body entities
id_1 = viz.add(
    pos_1,
    label=f"$m_1 = {mass_1}$",
    style=PointStyle(
        size=0.25,
        color="#ff4444",
    ),
)
id_2 = viz.add(
    pos_2,
    label=f"$m_2 ={mass_2}$",
    style=PointStyle(
        size=0.18,
        color="#4488ff",
    ),
)

viz.flush()

# ═══════════════════════════════════════════════════════════════
# Simulation loop
# ═══════════════════════════════════════════════════════════════

print(f"Simulating {TOTAL_FRAMES} frames (~{TOTAL_FRAMES * DT:.0f} s)...")

for _frame in range(TOTAL_FRAMES):
    # ── Gravitational force ──────────────────────────────────
    # Vector from body 1 to body 2:  r = pos_2 - pos_1
    r_12: Direction = pos_2 - pos_1
    dist_12 = r_12.mag()
    # Unit direction from 1 toward 2
    r_hat_12: Direction = r_12.normalized()

    # Force magnitude: F = G * m1 * m2 / r²
    force_mag = G * mass_1 * mass_2 / (dist_12 * dist_12)

    # Force on body 1: toward body 2 (+r_hat direction)
    f_1: Direction = r_hat_12 * force_mag
    # Force on body 2: toward body 1 (−r_hat direction)
    f_2: Direction = -f_1

    # ── Update velocities (a = F/m, v += a * dt) ─────────────
    acc_1: Direction = f_1 / mass_1
    acc_2: Direction = f_2 / mass_2

    vel_1 = vel_1 + acc_1 * DT
    vel_2 = vel_2 + acc_2 * DT

    # ── Update positions (p += v * dt) ───────────────────────
    pos_1 = pos_1 + vel_1 * DT
    pos_2 = pos_2 + vel_2 * DT

    # ── Render ───────────────────────────────────────────────
    viz.update_entity(id_1, pos_1)
    viz.update_entity(id_2, pos_2)

    viz.flush()
    viz.sleep_ms(DT_MS)

viz.stop()
print("Simulation stopped.")
