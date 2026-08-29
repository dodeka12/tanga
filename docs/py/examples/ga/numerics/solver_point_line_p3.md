# Recover a rotor from 3D point ↔ projection-ray matches

**Keywords:** solver · rotor estimation · point-line matching · P3 · BladeMask · least-squares

3D points are projected onto an image plane to form projection rays, then
rotated by a known rotor and perturbed with noise. The script estimates the
rotor that best maps the noisy points back onto their rays by iteratively
solving for the rotor blade coefficients with product matrices and
least-squares.

## Run

```bash
uv run python py/examples/ga/numerics/solver_point_line_p3.py
```

## Source

[`ga/numerics/solver_point_line_p3.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/ga/numerics/solver_point_line_p3.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""solver_point_line_p3.py — Recover a rotor from 3D point ↔ projection-ray matches.

3D points are projected onto an image plane to form projection rays, then
rotated by a known rotor and perturbed with noise. The script estimates the
rotor that best maps the noisy points back onto their rays by iteratively
solving for the rotor blade coefficients with product matrices and
least-squares.

Run with:
    uv run python py/examples/ga/numerics/solver_point_line_p3.py

Keywords: solver, rotor estimation, point-line matching, P3, BladeMask, least-squares
"""

import math

from pytanga import MV, BladeMask
from pytanga.algebra import EProduct
from pytanga.basis.p3 import BasisP3
from pytanga.blade_mask.predict import product_blade_mask
from pytanga.geometry import (
    Direction,
    Geometry,
    Point,
    RndDirection,
    RndPoint,
    Rotor,
)
from pytanga.matrix import MVProductMatrix
from pytanga.matrix.convert import to_matrix
from pytanga.matrix.product import product_matrix

P3 = BasisP3()
geo = Geometry(P3, seed=0)


def _rnd_point() -> MV:
    return geo(RndPoint((-2, 2), (-2, 2), (-2, 2)))


def _rnd_direction() -> MV:
    return geo(RndDirection((-0.1, 0.1), (-0.1, 0.1), (-0.1, 0.1)))


# Create random points
pnt_list: list[MV] = geo(RndPoint((-2, 2), (-2, 2), (-2, 2), count=4))
print("3D points:")
for pnt in pnt_list:
    pnt.show()

# Project the 3d points to an image plane perpendicular to e3 at e3 + e4.
origin: MV = geo(Point(0, 0, 0))
plane: MV = geo(Point(0, 0, 1)) ^ geo(Point(1, 0, 1)) ^ geo(Point(0, 1, 1))
prj_ray_list: list[MV] = [origin ^ pnt for pnt in pnt_list]
prj_pnt_list: list[MV] = [ray | plane for ray in prj_ray_list]
print("Projections:")
for pnt in prj_pnt_list:
    pnt.show()

theta_true: float = math.radians(36.0)

rotor_true: MV = geo(Rotor(angle=theta_true, axis=Direction(1, 1, 1).normalized()))

# Rotate the points and add some noise to them
true_rot_pnt_list: list[MV] = [rotor_true.vp(pnt) for pnt in pnt_list]

rot_pnt_list: list[MV] = [pnt + _rnd_direction() for pnt in true_rot_pnt_list]

# We are looking for the rotor that best maps the noisy rot_pnt_list back to pnt_list
# from just knowing the projection rays.
# We need to solve for the rotor R, such that ray_a ^ (R * p_a * ~R) = 0.
# The R is quadratic in this equation, so we cannot use the solver directly.
# Instead, we can calculate the Jacobean of the equation with respect to the rotor R
# and use that to solve for R iteratively.
# To derive the Jacobean, let's write (R * p_a * ~R) in tensor form:
# q_a^n = r^i p_a^j G^k_ij r^l Rev^m_l G^n_km, where Rev^m_l encodes the reverse on a rotor.
# The derivative of this with respect to r^i is:
# d q_a^n / d r^i = p_a^j G^k_ij r^l Rev^m_l G^n_km + r^l p_a^j G^k_lj Rev^m_i G^n_km

# Create the blade masks we need
pnt_mask: BladeMask = BladeMask(P3, "e1 + e2 + e3 + e4")
rot_mask: BladeMask = BladeMask(P3, "1 + e12 + e23 + e13")
ray_mask: BladeMask = BladeMask(P3, grades=[2])

# Create product matrix for R * p_i
rp_mask: BladeMask = product_blade_mask(
    pnt_mask, rot_mask, product=EProduct.GP, left=False
)
print(f"Product mask for R * p_i: {rp_mask}")

# Let's test the calculation of (R * p_i * ~R) for all i using the product matrix approach.
rp_mat: MVProductMatrix = product_matrix(
    pnt_list, a_mask=pnt_mask, b_mask=rot_mask, product=EProduct.GP, left=False
)
print(f"Product matrix for R * p_i: {rp_mat}")

# Build the RHS target vector from projection rays
C = to_matrix(prj_ray_list, mask=ray_mask)
print(f"Target vector shape: {C.data.shape}")
````
