# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""general_quadric.py — draw arbitrary quadrics straight from their coefficients.

Builds three non-ellipsoid quadrics directly from their symmetric 4×4 matrices
(a hyperboloid of one sheet, a cone, and an elliptic paraboloid) and draws each
raw ``Quadric3D`` in the standard viewer.  ``Quadric3D`` renders through the
analytic ray renderer by default, so unbounded quadrics are clipped to a finite
proxy volume (a ±10 cube, here) rather than the mesh pipeline.

Run with:  uv run python py/examples/ga/quadric/general_quadric.py

Keywords: quadric, ray, Quadric3D, hyperboloid, cone, paraboloid
"""

import numpy as np

from pytanga.geometry import Quadric3D
from pytanga.quadric import to_coeffs
from pytanga.viz import Visualizer


def _translated_quadric(q, center, const):
    """Symmetric 4×4 matrix of ``(x - center)ᵀ q (x - center) + const = 0``."""
    q = np.asarray(q, dtype=float)
    c = np.asarray(center, dtype=float)
    b = -q @ c
    f = float(c @ q @ c) + const
    return np.block([[q, b[:, None]], [b[None, :], np.array([[f]])]])


def _paraboloid_matrix(vertex):
    """Symmetric 4×4 matrix of ``(x - vx)² + (y - vy)² - (z - vz) = 0``."""
    vx, vy, vz = vertex
    return np.array(
        [
            [1.0, 0.0, 0.0, -vx],
            [0.0, 1.0, 0.0, -vy],
            [0.0, 0.0, 0.0, -0.5],
            [-vx, -vy, -0.5, vx * vx + vy * vy + vz],
        ]
    )


viz = Visualizer(title="Tanga — general quadrics (analytic ray renderer)")

# Hyperboloid of one sheet:  x² + y² - z² = 1, centred at (-4, 0, 0).
hyperboloid = _translated_quadric(np.diag([1.0, 1.0, -1.0]), (-4.0, 0.0, 0.0), -1.0)
viz.add(
    Quadric3D(to_coeffs(hyperboloid)),
    color="#44aaff",
    label="Hyperboloid (1 sheet)",
)

# Cone:  x² + y² - z² = 0, apex at the origin.
cone = _translated_quadric(np.diag([1.0, 1.0, -1.0]), (0.0, 0.0, 0.0), 0.0)
viz.add(Quadric3D(to_coeffs(cone)), color="#ff8844", label="Cone")

# Elliptic paraboloid:  (x - 4)² + y² - z = 0, vertex at (4, 0, 0).
paraboloid = _paraboloid_matrix((4.0, 0.0, 0.0))
viz.add(Quadric3D(to_coeffs(paraboloid)), color="#44ffaa", label="Paraboloid")

print("Three general quadrics, each rendered through the analytic ray path.")
viz.show()
viz.wait()
