# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""
solver_basics_02.py — Core solver API: inverse and general solve.

The `solver_basic_xx.py" demonstrate the equation-solving pipeline in G(3,0) float64.

Topics covered:

  1 — Multivector inverse via solve()
  2 — General solve: A * X = B
  3 — Detecting a singular system (solve vs solve_lsq)
"""

from __future__ import annotations

from pytanga import Algebra
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
# General solve: A * X = B
# ---------------------------------------------------------------------------
hr("General solve: A * X = B")

# Use a general (mixed-grade) multivector so the sub-algebra has full depth.
A = alg("0.5 + e1 - 2.0 e2")
print(f"A = {A}")

B = alg("1 + 3 e1")
print(f"A = {A}")
print(f"B = {B}")

X = solve(A, B)
print(f"X = {X}")

check = A * X
check.prune()
print(f"A*X = {check}")

# Residual norm: max absolute coefficient error
residual = {k: abs((A * X).to_dict().get(k, 0.0) - v) for k, v in B.to_dict().items()}
print(f"Max residual: {max(residual.values()):.2e}  (should be ~1e-15)")
