# Best-fit rotor from point correspondences

**Keywords:** solver · rotor estimation · point correspondences · least-squares

Demonstrates estimating a rotor R in G(3,0) from n point pairs (X_i, Y_i)
related by the same unknown rotation R * X_i * ~R = Y_i.

The sandwich equation is linearised by multiplying both sides on the right
by R:

    R * X_i = Y_i * R
    ⟹  R * X_i - Y_i * R = 0

This is LINEAR in the coefficients of R, so for each pair (X_i, Y_i) we can
build a constraint matrix C_i and stack them into an overdetermined homogeneous
system C · vec(R) = 0, solved by SVD.

GENERALISATION NOTE
─────────────────────────────────────────────────────────────────────────────
The equation R * X - Y * R = 0 (linear in R) has exactly the same form
regardless of the grade of the matched objects.  Only the blade masks change:

  Object type   | col_mask (unknown R)  | row_mask (constraint output)
  ─────────────────────────────────────────────────────────────────────
  Vectors       | grades=[0,2]          | grades=[1]
  Lines (P3=G4) | grades=[0,2]          | grades=[2]
  Planes (P3)   | grades=[0,2]          | grades=[3]
  Rotors (P3)   | grades=[0,2]          | grades=[0,2]

Swap in different masks to match lines to lines, planes to planes, etc.

## Source

[`ga/numerics/solver_rotor_estimation.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/ga/numerics/solver_rotor_estimation.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""
solver_rotor_estimation.py — Best-fit rotor from point correspondences.

Demonstrates estimating a rotor R in G(3,0) from n point pairs (X_i, Y_i)
related by the same unknown rotation R * X_i * ~R = Y_i.

The sandwich equation is linearised by multiplying both sides on the right
by R:

    R * X_i = Y_i * R
    ⟹  R * X_i - Y_i * R = 0

This is LINEAR in the coefficients of R, so for each pair (X_i, Y_i) we can
build a constraint matrix C_i and stack them into an overdetermined homogeneous
system C · vec(R) = 0, solved by SVD.

GENERALISATION NOTE
─────────────────────────────────────────────────────────────────────────────
The equation R * X - Y * R = 0 (linear in R) has exactly the same form
regardless of the grade of the matched objects.  Only the blade masks change:

  Object type   | col_mask (unknown R)  | row_mask (constraint output)
  ─────────────────────────────────────────────────────────────────────
  Vectors       | grades=[0,2]          | grades=[1]
  Lines (P3=G4) | grades=[0,2]          | grades=[2]
  Planes (P3)   | grades=[0,2]          | grades=[3]
  Rotors (P3)   | grades=[0,2]          | grades=[0,2]

Swap in different masks to match lines to lines, planes to planes, etc.

Keywords: solver, rotor estimation, point correspondences, least-squares
"""

from __future__ import annotations

import math

import numpy as np
from pytanga import Algebra, BladeMask, MVMatrix
from pytanga.geometry import RndMV
from pytanga.matrix.convert import from_matrix
from pytanga.matrix.product import product_matrix


def hr(title: str) -> None:
    """Print a title with a horizontal rule."""
    print(f"\n{'─' * 60}\n{title}\n{'─' * 60}")


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
alg = Algebra(3, 0, "float64")

rng = np.random.default_rng(7)

# ---------------------------------------------------------------------------
# Ground truth rotor: 30° rotation in the e1∧e2 plane
# ---------------------------------------------------------------------------
hr("Ground truth: 30° rotation in the e1∧e2 plane")

angle = math.radians(30)
# R = cos(θ/2) + sin(θ/2)·e12
R_true = alg({0: math.cos(angle / 2), "e12": math.sin(angle / 2)})
print(f"R_true = {R_true}")
print(f"R_true * ~R_true = {(R_true * ~R_true).prune()}")  # should be ~1

# ---------------------------------------------------------------------------
# Generate point correspondences (with optional noise)
# ---------------------------------------------------------------------------
hr("Generate n point pairs X_i → Y_i = R * X_i * ~R")

n = 10
noise_level = 0.01

vec_mask = BladeMask(alg, grades=[1])
vectors = [
    RndMV(vec_mask, [(-1.0, 1.0)] * len(vec_mask))(np.random.default_rng(i))
    for i in range(n)
]

# Apply R via the normalised versor product
rotated = [alg.nvp(R_true, v) for v in vectors]

# Add Gaussian noise to Y_i
noisy_rotated = []
for y in rotated:
    d = y.to_dict()
    noisy = alg({k: v + rng.normal(0, noise_level) for k, v in d.items()})
    noisy_rotated.append(noisy)

print(f"Generated {n} vector pairs with noise σ={noise_level}")

# ---------------------------------------------------------------------------
# Build the constraint matrices for each pair
# ---------------------------------------------------------------------------
hr("Build stacked constraint matrix C")

# A rotor in G(3,0) lives in the even sub-algebra:
# R = r0 + r12·e12 + r13·e13 + r23·e23  → grades=[0,2]
rotor_mask = BladeMask(alg, grades=[0, 2])  # even sub-algebra (4 blades)
vector_mask = BladeMask(alg, grades=[1])  # grade-1 output (3 blades)

print(f"rotor_mask:  {rotor_mask}  ({len(rotor_mask)} blades)")
print(f"vector_mask: {vector_mask}  ({len(vector_mask)} blades)")

# For each pair (Xi, Yi):
#   M_R_i = product_matrix(Xi, rotor_mask, vector_mask, left=False)
#         → M such that M_R_i · vec(R) = vec(R * Xi)
#   M_L_i = product_matrix(Yi, rotor_mask, vector_mask, left=True)
#         → M such that M_L_i · vec(R) = vec(Yi * R)
#   C_i = M_R_i − M_L_i   (constraint: C_i · vec(R) = 0)
C_blocks = []
for xi, yi in zip(vectors, noisy_rotated):
    M_R = product_matrix(
        xi, a_mask=rotor_mask, b_mask=rotor_mask, c_mask=vector_mask, left=False
    )  # R * Xi
    M_L = product_matrix(
        yi, a_mask=rotor_mask, b_mask=rotor_mask, c_mask=vector_mask, left=True
    )  # Yi * R
    C_i = M_R.data - M_L.data
    C_blocks.append(C_i)

C = np.vstack(C_blocks)
print(
    f"Stacked constraint matrix C shape: {C.shape}  ({n}·{len(vector_mask)} x {len(rotor_mask)})"
)

# ---------------------------------------------------------------------------
# Solve the homogeneous system C · vec(R) = 0 via SVD
# ---------------------------------------------------------------------------
hr("SVD solve and normalise")

_, singular_values, Vt = np.linalg.svd(C, full_matrices=True)
print(f"Singular values: {singular_values.round(4)}")
print(f"  (smallest → {singular_values[-1]:.6f}, should be near 0)")

R_vec = Vt[-1]  # right singular vector for smallest σ
R_est = from_matrix(MVMatrix(R_vec.reshape(-1, 1), rotor_mask))
print(f"\nR estimated (raw): {R_est}")

# ---------------------------------------------------------------------------
# Normalise: a proper rotor satisfies R * ~R = 1
# ---------------------------------------------------------------------------
rev_r = alg.rev(R_est)
rr_scalar = alg.gp(R_est, rev_r).to_dict().get("s", 0.0)
norm = math.sqrt(abs(rr_scalar))
# Convention: keep scalar part positive (R and -R represent the same rotation)
scalar_sign = math.copysign(1.0, R_est.to_dict().get("s", 1.0))
R_norm = alg({k: v / norm * scalar_sign for k, v in R_est.to_dict().items()})
R_norm.prune()
print(f"R estimated (normalised): {R_norm}")
print(f"R true:                   {R_true}")

# ---------------------------------------------------------------------------
# Evaluate rotation error per point
# ---------------------------------------------------------------------------
hr("Rotation error per point")

errors = []
for xi, yi in zip(vectors, rotated):  # use clean rotated (no noise) for evaluation
    y_est = alg.nvp(R_norm, xi)
    y_true = yi
    diff = {
        k: abs(y_est.to_dict().get(k, 0.0) - y_true.to_dict().get(k, 0.0))
        for k in set(y_est.to_dict()) | set(y_true.to_dict())
    }
    errors.append(max(diff.values()) if diff else 0.0)

print(
    f"Mean rotation error: {np.mean(errors):.6f}  (should be ~noise level {noise_level})"
)
print(f"Max  rotation error: {np.max(errors):.6f}")
print("\nNote: swap rotor_mask / vector_mask to match lines, planes, or other MVs.")
````
