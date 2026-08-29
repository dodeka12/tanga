# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""
solver_basics_03.py — Core solver API: inverse and general solve.

The `solver_basic_xx.py" demonstrate the equation-solving pipeline in G(3,0) float64.

Topics covered:

  1 — Multivector inverse via solve()
  2 — General solve: A * X = B
  3 — Detecting a singular system (solve vs solve_lsq)

Keywords: solver, singular, solve_lsq, least-norm, G(3,1)
"""

from __future__ import annotations

import numpy as np
from pytanga import Algebra
from pytanga.solver.solve import solve, solve_lsq


def hr(title: str) -> None:
    """Print a title with a horizontal rule."""
    print(f"\n{'─' * 60}\n{title}\n{'─' * 60}")


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

# If you run this script for the first time, creating the algebra will trigger
# a one-time codegen step that may take a few seconds.
alg = Algebra(3, 0, "float64")

# Use a general (mixed-grade) multivector so the sub-algebra has full depth.
A = alg("0.5 + e1 - 2.0 e2")
print(f"A = {A}")

# ---------------------------------------------------------------------------
# Part C — Singular system: solve vs solve_lsq
# ---------------------------------------------------------------------------
hr("Part C — Singular A: solve raises, solve_lsq gives least-norm solution")

alg = Algebra(3, (1,), "float64")  # G(3,1) has a null vector (grade-1 blade)

# a null vector is singular: A_sing * A_sing = 0, so the system A_sing * X = 1 has no solution.
A_sing = alg("e1 + e2")

print(f"A_singular = {A_sing}")
print(f"A_sing * A_sing = {A_sing * A_sing}  (should be 0)")

try:
    X_fail = solve(A_sing, 1.0)
    print(f"solve result:  X = {X_fail}")
    print(f"A_singular * X_fail = {A_sing * X_fail}")
    print("solve succeeded (unexpected for this example)")
except np.linalg.LinAlgError as e:
    print(f"solve raised LinAlgError: {e}")
except ValueError as e:
    print(f"solve raised ValueError: {e}")
except Exception as e:
    print(f"solve raised unexpected exception: {type(e).__name__}: {e}")


X_lsq = solve_lsq(A_sing, 1.0)
check_lsq = A_sing * X_lsq
check_lsq.prune()
print(f"solve_lsq result:  X = {X_lsq}")
print(f"A_singular * X_lsq = {check_lsq}  (least-squares residual)")
