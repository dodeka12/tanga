# Core solver API: inverse and general solve

**Keywords:** solver · inverse · general solve · linear system

The `solver_basic_xx.py" demonstrate the equation-solving pipeline in G(3,0) float64.

Topics covered:

  1 — Multivector inverse via solve()
  2 — General solve: A * X = B
  3 — Detecting a singular system (solve vs solve_lsq)

## Source

[`ga/numerics/solver_basics_01.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/ga/numerics/solver_basics_01.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""
solver_basics_01.py — Core solver API: inverse and general solve.

The `solver_basic_xx.py" demonstrate the equation-solving pipeline in G(3,0) float64.

Topics covered:

  1 — Multivector inverse via solve()
  2 — General solve: A * X = B
  3 — Detecting a singular system (solve vs solve_lsq)

Keywords: solver, inverse, general solve, linear system
"""

from __future__ import annotations

import numpy as np
from pytanga import MV, Algebra, EProduct, MVMatrix
from pytanga.matrix.convert import from_matrix, to_matrix
from pytanga.matrix.product import product_matrix
from pytanga.solver.solve import solve


def hr(title: str) -> None:
    """Print a title with a horizontal rule."""
    print(f"\n{'─' * 60}\n{title}\n{'─' * 60}")


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

# If you run this script for the first time, creating the algebra will trigger
# a one-time codegen step that may take a few seconds.
alg = Algebra(3, 0, "float64")

# ---------------------------------------------------------------------------
# Part A — Multivector inverse
# ---------------------------------------------------------------------------
hr("Multivector inverse (two equivalent paths)")

# Use a general (mixed-grade) multivector so the sub-algebra has full depth.
A = alg("0.5 + e1 - 2.0 e2")
print(f"A = {A}")

# Path 1: high-level one-liner — scalar 1.0 is coerced to MV automatically
B1 = solve(A, 1.0)
print("\nPath 1 — solve(A, 1.0):")
print(f"  B = {B1}")
check = A * B1
check.prune()
print(f"  A*B = {check}  (should be scalar 1)")

# Path 2: explicit step-by-step (educational)
# We want to solve A * B = 1 for B given A.
print("\nPath 2 — explicit step-by-step:")

# Now we create the product matrix.
# If no explicit blade masks are given, this function assumes multivector B may contain
# elements of the whole algebra and uses the non-zero components of A to determine
# the set of blades in the resulting multivector C (for A * B = C).
# The product matrix M is a linear map from the components of B to the components of C.
M = product_matrix(A, product=EProduct.GP)
# print(f"Product matrix M:\n{M}")

print(f"  b_mask: {M.b_mask}")
print(f"  c_mask: {M.c_mask}")
print(f"  M shape: {M.data.shape}")

c_mv: MV = alg("1.0")  # The right-hand side of the equation A * B = C
C = to_matrix(
    c_mv, mask=M.c_mask
)  # Convert C to a column vector with the same blade mask as M's output

if M.data.shape[1] == M.data.shape[2]:
    # Solve the linear system M * B = C for B, where B is the unknown multivector.
    b_arr = np.linalg.solve(M.data[0, :, :], C.data)
    # Convert the solution back to a multivector using the blade mask of B.
    B2 = from_matrix(MVMatrix(b_arr, M.b_mask))
    print(f"  B = {B2}")
    assert B1.to_dict() == B2.to_dict(), "paths disagree!"
    print("  ✓ Both paths agree")
else:
    print(
        f"  System is {M.data.shape[1]}x{M.data.shape[2]} — not square with this mask."
    )
    print("  (Use solve() which auto-derives a square closed sub-algebra mask.)")
````
