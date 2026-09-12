# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Symmetric-matrix ↔ coefficient-vector maps for the quadric spaces.

Coefficient ordering (README math, fixed up front):

2D — symmetric 3×3 ``A`` → 6 coeffs
    ``(a₁₃, a₂₃, (√2/2)a₃₃, (√2/2)a₁₁, (√2/2)a₂₂, a₁₂)``

3D — symmetric 4×4 ``Q`` → 10 coeffs
    ``(q₁₄, q₂₄, q₃₄, (√2/2)q₄₄, (√2/2)q₁₁, (√2/2)q₂₂, (√2/2)q₃₃, q₁₂, q₁₃, q₂₃)``

``to_coeffs`` and ``from_coeffs`` are exact inverses.
"""

from __future__ import annotations

import numpy as np

_SQRT2_OVER_2 = float(np.sqrt(2.0) / 2.0)
_SQRT2 = float(np.sqrt(2.0))


def _as_matrix(a, n: int) -> np.ndarray:
    """Coerce *a* to a symmetric ``n×n`` float array."""
    arr = np.asarray(a, dtype=float)
    if arr.shape != (n, n):
        raise ValueError(f"expected a {n}×{n} matrix, got shape {arr.shape}")
    if not np.allclose(arr, arr.T):
        raise ValueError("matrix must be symmetric")
    return arr


def to_coeffs(a) -> tuple[float, ...]:
    """Map a symmetric 3×3 (conic) or 4×4 (quadric) matrix to coeffs."""
    arr = np.asarray(a, dtype=float)
    if arr.ndim != 2 or arr.shape[0] != arr.shape[1]:
        raise ValueError(f"expected a square matrix, got shape {arr.shape}")
    n = arr.shape[0]
    if n not in (3, 4):
        raise ValueError("only 3×3 (conic) and 4×4 (quadric) matrices are supported")
    arr = _as_matrix(arr, n)
    if n == 3:
        return (
            arr[0, 2],
            arr[1, 2],
            _SQRT2_OVER_2 * arr[2, 2],
            _SQRT2_OVER_2 * arr[0, 0],
            _SQRT2_OVER_2 * arr[1, 1],
            arr[0, 1],
        )
    return (
        arr[0, 3],
        arr[1, 3],
        arr[2, 3],
        _SQRT2_OVER_2 * arr[3, 3],
        _SQRT2_OVER_2 * arr[0, 0],
        _SQRT2_OVER_2 * arr[1, 1],
        _SQRT2_OVER_2 * arr[2, 2],
        arr[0, 1],
        arr[0, 2],
        arr[1, 2],
    )


def from_coeffs(coeffs) -> np.ndarray:
    """Map a 6- or 10-tuple of coeffs back to the symmetric matrix."""
    t = np.asarray(coeffs, dtype=float)
    if t.shape == (6,):
        return np.array(
            [
                [_SQRT2 * t[3], t[5], t[0]],
                [t[5], _SQRT2 * t[4], t[1]],
                [t[0], t[1], _SQRT2 * t[2]],
            ]
        )
    if t.shape == (10,):
        return np.array(
            [
                [_SQRT2 * t[4], t[7], t[8], t[0]],
                [t[7], _SQRT2 * t[5], t[9], t[1]],
                [t[8], t[9], _SQRT2 * t[6], t[2]],
                [t[0], t[1], t[2], _SQRT2 * t[3]],
            ]
        )
    raise ValueError("coeffs must be a 6-tuple (conic) or 10-tuple (quadric)")
