#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""2D Visualizer Demo — show geometric entities from all four 2D algebras.

Usage:
  uv run python dev/src/viz_2d_demo.py
"""

from pytanga.basis import BasisE2, BasisN2, BasisP2, BasisPGA2
from pytanga.geometry import (
    Circle,
    Direction,
    Line,
    Point,
    PointPair,
    Space,
    Sphere,
    analyze,
)
from pytanga.viz import Visualizer


def main():
    # ── Create a 2D visualizer ──────────────────────────────
    viz = Visualizer(
        space_dim=2,
        annotation="""
## 2D Algebra Demo

**E2** — directions & lines through origin

**P2** — points & lines via homogeneous coordinates

**N2** — conformal 2D: circles, point pairs, translators

**PGA2** — Gunn/Dorst plane‑based PGA: lines are primary

*Right‑click drag to pan, scroll to zoom*
""",
    )

    # ═══════════════════════════════════════════════════════
    # E2: Euclidean 2D — only origin‑through entities
    # ═══════════════════════════════════════════════════════
    e2 = BasisE2()

    viz.add(Direction(1, 0, 0), color="#ff4444", label="e1 (red)")
    viz.add(Direction(0, 1, 0), color="#44ff44", label="e2 (green)")

    # A direction between e1 and e2
    d = e2.multivector({1: 1.5, 2: 2.5})
    viz.add(d, color="#ffaa00", label="dir(1.5, 2.5)")

    # Space (pseudoscalar) — translucent
    viz.add(Space(scale=1.0), color="#8888ff", opacity=0.08)

    # # ═══════════════════════════════════════════════════════
    # # P2: Projective 2D — points & lines anywhere
    # # ═══════════════════════════════════════════════════════
    # p2 = BasisP2()

    # viz.add(Point(2, 1, 0), color="#ff44ff", label="P2 point (2,1)")

    # # Line through two points
    # line = Line(origin=Point(-3, -2, 0), direction=Direction(6, 1, 0))
    # viz.add(line, color="#44ffff", label="P2 line")

    # # Direction (ideal point)
    # viz.add(Direction(0.5, 1, 0), color="#ffff44", label="ideal dir(0.5,1)")

    # # ═══════════════════════════════════════════════════════
    # # N2: Conformal 2D — circles, point pairs, translators
    # # ═══════════════════════════════════════════════════════
    # n2 = BasisN2()

    # # Points on the null cone
    # viz.add(Point(-4, 1, 0), color="#ffffff", label="N2 point (-4,1)")

    # # A circle (N2 "sphere" = circle in 2D)
    # viz.add(
    #     Sphere(Point(-4, 1, 0), 1.5), color="#ff8888", opacity=0.3, label="circle r=1.5"
    # )

    # # A point pair
    # viz.add(
    #     PointPair(Point(2, -4, 0), Point(4, -2, 0)),
    #     color="#88ff88",
    #     label="point pair",
    # )

    # # Another line via conformal embedding
    # line_n2 = Line(origin=Point(-5, -4, 0), direction=Direction(3, 5, 0))
    # viz.add(line_n2, color="#8888ff", label="N2 line")

    # # ═══════════════════════════════════════════════════════
    # # PGA2: Gunn/Dorst plane‑based PGA — lines are primary
    # # ═══════════════════════════════════════════════════════
    # pga2 = BasisPGA2()

    # # Lines in PGA2 (grade-1 vectors)
    # l1 = Line(origin=Point(0, -3, 0), direction=Direction(1, 0.3, 0))
    # viz.add(l1, color="#ffaa44", opacity=0.6, label="PGA2 line A")

    # l2 = Line(origin=Point(0, -3, 0), direction=Direction(-0.3, 1, 0))
    # viz.add(l2, color="#44ffaa", opacity=0.6, label="PGA2 line B")

    # # Point = intersection of two lines
    # viz.add(
    #     Point(-0.8, -3, 0),
    #     color="#ffffff",
    #     label="intersection point",
    # )

    # ── Run the viewer ─────────────────────────────────────
    viz.show()
    viz.wait()


if __name__ == "__main__":
    main()
