# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Conic/quadric/line construction from points in the quadric spaces."""

from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

import numpy as np

from pytanga.algebra._mv import MV

from ._embedding import embed_point
from ._mapping import from_coeffs

if TYPE_CHECKING:
    from pytanga.algebra._algebra import Algebra

    from ._basis import BasisQ2


def _mv_coeffs(basis: "Algebra", mv: MV) -> tuple[float, ...]:
    """Read a grade-1 MV's coefficients in ``b1…bN`` order (blade IDs 1, 2, 4, …)."""
    return tuple(mv[1 << i] for i in range(basis.dim))


def _point_coeffs(basis: "Algebra", point: "tuple[float, ...]") -> tuple[float, ...]:
    """Coeff vector of a point's rank-1 embedding (equals ``to_coeffs(p pᵀ)``)."""
    return _mv_coeffs(basis, embed_point(basis, *point))


def _from_points_dual(
    basis: "Algebra", points: "Sequence[tuple[float, ...]]"
) -> np.ndarray:
    """Build a conic/quadric from points via ``from_coeffs(dual(∧ embed(pᵢ)))``."""
    wedge: MV | None = None
    for p in points:
        emb = embed_point(basis, *p)
        wedge = emb if wedge is None else basis.op(wedge, emb)
    if wedge is None:
        raise ValueError("_from_points_dual requires at least one point")
    coeffs = _mv_coeffs(basis, basis.dual(wedge))
    return from_coeffs(coeffs)


def _from_points_svd(
    basis: "Algebra", points: "Sequence[tuple[float, ...]]"
) -> np.ndarray:
    """Build a conic/quadric from the null space of the stacked point embeddings."""
    rows = np.array([_point_coeffs(basis, p) for p in points], dtype=float)
    _, _, vt = np.linalg.svd(rows, full_matrices=True)
    return from_coeffs(vt[-1])


def conic_from_points(
    basis: "Algebra", points: "Sequence[tuple[float, ...]]"
) -> np.ndarray:
    """Conic (symmetric 3×3) through 5 points — thesis pencil/dual method."""
    if basis.dim != 6:
        raise ValueError("conic_from_points requires the 2D quadric basis (BasisQ2)")
    return _from_points_dual(basis, points)


def quadric_from_points(
    basis: "Algebra", points: "Sequence[tuple[float, ...]]"
) -> np.ndarray:
    """Quadric (symmetric 4×4) through 9 points — dual method."""
    if basis.dim != 10:
        raise ValueError("quadric_from_points requires the 3D quadric basis (BasisQ3)")
    return _from_points_dual(basis, points)


def conic_from_points_svd(
    basis: "Algebra", points: "Sequence[tuple[float, ...]]"
) -> np.ndarray:
    """Conic (symmetric 3×3) through 5 points — SVD null-space method."""
    if basis.dim != 6:
        raise ValueError(
            "conic_from_points_svd requires the 2D quadric basis (BasisQ2)"
        )
    return _from_points_svd(basis, points)


def quadric_from_points_svd(
    basis: "Algebra", points: "Sequence[tuple[float, ...]]"
) -> np.ndarray:
    """Quadric (symmetric 4×4) through 9 points — SVD null-space method."""
    if basis.dim != 10:
        raise ValueError(
            "quadric_from_points_svd requires the 3D quadric basis (BasisQ3)"
        )
    return _from_points_svd(basis, points)


def line_from_points(
    basis: "BasisQ2", a: "tuple[float, ...]", b: "tuple[float, ...]"
) -> MV:
    """2D line through points *a* and *b*: ``embed(a) ∧ embed(b) ∧ b₄ ∧ b₅ ∧ b₆``."""
    if basis.dim != 6:
        raise ValueError("line_from_points requires the 2D quadric basis (BasisQ2)")
    ea = embed_point(basis, *a)
    eb = embed_point(basis, *b)
    return ea ^ eb ^ basis.b4 ^ basis.b5 ^ basis.b6
