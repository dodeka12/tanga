# Least-squares homogeneous line fitting in P2

**Keywords:** solver · line fitting · least-squares · P2 · homogeneous

P2 (projective plane) is modelled as G(3,0) where e3 is the homogeneous
(projective) dimension.

  Point  = grade-1 vector with e3 = 1:  p = x·e1 + y·e2 + 1·e3
  Line   = grade-2 blade:               L = a·e12 + b·e13 + c·e23
  Incidence: p ^ L = 0  iff  p lies on L  (outer product lands in e123)

Given n noisy sample points, find the best-fit line L that minimises the sum
of squared incidence errors ‖p_i ^ L‖².

This is a homogeneous linear system: M · vec(L) = 0, where M is the stacked
outer-product matrix.  The solution is the right singular vector of M
corresponding to the SMALLEST singular value — NOT lstsq(b=0), which would
give the trivial solution vec(L) = 0.

## Source

[`ga/numerics/solver_line_fitting_p2.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/ga/numerics/solver_line_fitting_p2.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""
solver_line_fitting_p2.py — Least-squares homogeneous line fitting in P2.

P2 (projective plane) is modelled as G(3,0) where e3 is the homogeneous
(projective) dimension.

  Point  = grade-1 vector with e3 = 1:  p = x·e1 + y·e2 + 1·e3
  Line   = grade-2 blade:               L = a·e12 + b·e13 + c·e23
  Incidence: p ^ L = 0  iff  p lies on L  (outer product lands in e123)

Given n noisy sample points, find the best-fit line L that minimises the sum
of squared incidence errors ‖p_i ^ L‖².

This is a homogeneous linear system: M · vec(L) = 0, where M is the stacked
outer-product matrix.  The solution is the right singular vector of M
corresponding to the SMALLEST singular value — NOT lstsq(b=0), which would
give the trivial solution vec(L) = 0.

Keywords: solver, line fitting, least-squares, P2, homogeneous
"""

from __future__ import annotations

import numpy as np
from pytanga import Algebra, BladeMask, MVMatrix
from pytanga.matrix.convert import from_matrix
from pytanga.matrix.product import product_matrix


def hr(title: str) -> None:
    """Print a title with a horizontal rule."""
    print(f"\n{'─' * 60}\n{title}\n{'─' * 60}")


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
alg = Algebra(3, 0, "float64")

rng = np.random.default_rng(0)

# ---------------------------------------------------------------------------
# Ground truth line and noisy points
# ---------------------------------------------------------------------------
hr("Setup: ground truth line and noisy sample points")

# In P2, a line is the outer product of two points on it.
# The line y = x passes through (0,0,1) and (1,1,1) in homogeneous coords.
p_origin = alg({"e3": 1.0})
p_diag = alg({"e1": 1.0, "e2": 1.0, "e3": 1.0})
L_true_raw = p_origin ^ p_diag
L_true_raw.prune()
# Normalise so largest coefficient is 1
L_true_d = L_true_raw.to_dict()
scale_lt = max(abs(v) for v in L_true_d.values())
L_true = alg({k: v / scale_lt for k, v in L_true_d.items()})
print(f"True line L = {L_true}  (y = x in P2)")

# Generate n points on the line y = x with Gaussian noise
n = 20
t = rng.uniform(-3.0, 3.0, n)
noise = rng.normal(0, 0.05, (n, 2))
xs = t + noise[:, 0]
ys = t + noise[:, 1]

points = [alg({"e1": float(x), "e2": float(y), "e3": 1.0}) for x, y in zip(xs, ys)]
print(f"Generated {n} noisy points near y = x")

# ---------------------------------------------------------------------------
# Build the blade masks
# ---------------------------------------------------------------------------
# Outer product of a point (grade-1) and a line (grade-2) lands in grade-3
# which is the pseudoscalar e123 (one blade in G(3,0)).
col_mask = BladeMask(alg, grades=[2])  # all grade-2 blades = line subspace
row_mask = BladeMask(alg, grades=[3])  # grade-3 = pseudoscalar e123
print(f"\ncol_mask (line subspace): {col_mask}")
print(f"row_mask (output):         {row_mask}")

# ---------------------------------------------------------------------------
# Build the stacked outer-product matrix
# ---------------------------------------------------------------------------
hr("Build and solve the homogeneous system")

# product_matrix builds a stacked matrix M where each row corresponds
# to the incidence constraint for one sample point.
# M has shape (n, 3): n rows (one per point), 3 columns (one per line blade).
M = product_matrix(
    points, a_mask=col_mask, b_mask=col_mask, c_mask=row_mask, product="op"
)
print(f"Stacked matrix M shape: {M.shape}  (should be {n}×{len(col_mask)})")

# Solve the homogeneous system M · vec(L) = 0 via SVD.
# The solution is the right singular vector for the SMALLEST singular value
# (last row of Vt), not lstsq(b=0) which gives the trivial zero solution.
M2d = M.data.reshape(-1, len(col_mask))
_, singular_values, Vt = np.linalg.svd(M2d, full_matrices=True)
print(f"Singular values: {singular_values.round(3)}")
print(f"  (smallest → {singular_values[-1]:.4f}, should be near 0 for a good fit)")

L_vec = Vt[-1]  # last row of Vt = right singular vector for smallest σ
L_est = from_matrix(MVMatrix(L_vec.reshape(-1, 1), col_mask))

# ---------------------------------------------------------------------------
# Normalise by the max-magnitude coefficient (projective equivalence: L ~ c·L)
# ---------------------------------------------------------------------------
L_raw_d = L_est.to_dict()
max_val = max(abs(v) for v in L_raw_d.values())
L_norm = alg({k: v / max_val for k, v in L_raw_d.items()})

print(f"\nEstimated line (raw):        {L_est}")
print(f"Estimated line (normalised): {L_norm}")
print(f"True line:                   {L_true}")

# ---------------------------------------------------------------------------
# Evaluate residual incidence errors
# ---------------------------------------------------------------------------
residuals = []
for p in points:
    wedge = p ^ L_norm  # outer product should be ~0 for points on the line
    wedge.prune()
    d = wedge.to_dict()
    residuals.append(abs(d.get("I", 0.0)))  # the pseudoscalar component

mean_err = np.mean(residuals)
max_err = np.max(residuals)
print(f"\nMean |p_i ^ L| = {mean_err:.4f}  (should be ~noise level)")
print(f"Max  |p_i ^ L| = {max_err:.4f}")
````
