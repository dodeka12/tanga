#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

r"""Least-squares line fitting in P3 with visualization.

P3 (projective 3D, G(4,0)) uses homogeneous coordinates.  A point is a
grade-1 vector ``p = x·e1 + y·e2 + z·e3 + e4`` and a line the grade-2 outer
product of two points on it.  A point lies on a line ``L`` iff ``p ^ L = 0``.

We model the incidence with an expression over a *point* variable and a
*line* variable,

    E(P, L) = P ^ L,

bind ``P`` to a batch of noisy sample points, and find the line ``L`` that
best satisfies ``P_i ^ L ≈ 0`` via homogeneous least squares.  The
singular-value decomposition of the resulting linear map exposes the candidate
lines (its right-singular vectors) and the smallest singular value is the
best fit.

The noisy points and the fitted line are shown in the interactive viewer.

Run
---
.. code-block:: bash

    uv run python py/examples/ga/expression/line_fitting_p3.py

Keywords: expressions, line fitting, least-squares, P3, visualization
"""

from __future__ import annotations

import numpy as np
from pytanga.basis import BasisP3
from pytanga.expression import DataArray
from pytanga.geometry import Direction, Geometry, Line, Normal, Point, RndPoint
from pytanga.viz import LineStyle, PointStyle, Visualizer


def main() -> None:
    P3 = BasisP3()
    geo = Geometry(P3, seed=0)

    # Build the incidence expression E(P, L) = P ^ L.
    P = geo("P", Point)
    L = geo("L", Line)
    incidence = P ^ L

    # Ground-truth line: the x-axis (y = z = 0), through the origin.
    L_true = geo(Line(Point(0, 0, 0), Direction(1, 0, 0)))

    # Noisy sample points scattered near the x-axis.
    n = 20
    points = geo(RndPoint((-3.0, 3.0), Normal(0.0, 0.2), Normal(0.0, 0.2), count=n))

    # Partially evaluate P over all sample points: a linear map in L whose
    # counting axis stacks the per-point incidence constraints.
    constraints = incidence(P=DataArray(points, masks=("n", geo.mask_for(Point))))

    # Singular-value decomposition: the singular vectors are candidate lines,
    # and the smallest singular value is the homogeneous least-squares fit.
    svalues, smvs = constraints.svd()
    L_est = smvs[-1]

    residuals = [(p ^ L_est).mag for p in points]
    print("Line fitting (P3, homogeneous least squares):")
    print("  singular values :", [f"{v:.4f}" for v in svalues])
    print("  singular MVs:")
    for s, mv in zip(svalues, smvs):
        print(f"    σ={s:.4f}  {geo.analyze(mv)}")
    print("  true line :", geo.analyze(L_true))
    print("  fit line  :", geo.analyze(L_est))
    print(f"  mean |p ^ L_fit| = {np.mean(residuals):.4f}")

    # Map the raw MV results back to entities for visualization.
    viz = Visualizer(title="Tanga — Least-squares line fit (P3)")

    for p in points:
        viz.add(geo.analyze(p), color="#ffaa44", style=PointStyle(size=0.08))

    # All singular multivectors, drawn in gray.
    for mv in smvs:
        viz.add(
            geo.analyze(mv),
            color="#888888",
            style=LineStyle(opacity=0.4),
            label="singular MV",
        )

    viz.add(
        geo.analyze(L_est),
        color="#44ff44",
        label="fitted line",
    )
    viz.add(
        geo.analyze(L_true),
        color="#4488ff",
        label="ground truth",
    )

    viz.show()
    viz.wait()


if __name__ == "__main__":
    main()
