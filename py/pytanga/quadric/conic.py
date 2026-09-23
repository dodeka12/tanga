# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Conic and Quadric3D entity dataclasses plus their kind enums.

A conic (2D) is a symmetric 3×3 matrix, a quadric (3D) a symmetric 4×4 matrix;
both are stored as the ``pytanga.quadric`` coefficient vector (6 or 10 entries).
The derived classification properties (``kind``, ``rank``, ``signature``,
``center``, …) use the standard affine block form ``[[Q, b], [bᵀ, c]]``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from functools import cached_property
from typing import TYPE_CHECKING, Any

import numpy as np

from ._mapping import _from_coeffs, _to_coeffs
from .refine import refine_conic, refine_quadric

from pytanga.entity import Direction
from pytanga.entity import Point

if TYPE_CHECKING:
    from pytanga.geometry.matrix import Matrix

_TOL = 1e-10


class EConicKind(StrEnum):
    """Coarse projective classification of a 2D conic."""

    ellipse = "ellipse"
    circle = "circle"
    hyperbola = "hyperbola"
    parabola = "parabola"
    line = "line"
    line_pair = "line_pair"
    parallel_line_pair = "parallel_line_pair"
    point_pair = "point_pair"
    imaginary = "imaginary"


class EQuadricKind(StrEnum):
    """Coarse projective classification of a 3D quadric."""

    ellipsoid = "ellipsoid"
    sphere = "sphere"
    hyperboloid_1s = "hyperboloid_1s"
    hyperboloid_2s = "hyperboloid_2s"
    elliptic_paraboloid = "elliptic_paraboloid"
    hyperbolic_paraboloid = "hyperbolic_paraboloid"
    cone = "cone"
    elliptic_cylinder = "elliptic_cylinder"
    hyperbolic_cylinder = "hyperbolic_cylinder"
    parabolic_cylinder = "parabolic_cylinder"
    plane = "plane"
    plane_pair = "plane_pair"
    parallel_plane_pair = "parallel_plane_pair"
    imaginary = "imaginary"


def _rank(m: np.ndarray, tol: float | None = None) -> int:
    if tol is None:
        return int(np.linalg.matrix_rank(m))
    return int(np.linalg.matrix_rank(m, tol=tol))


def _inertia(m: np.ndarray, tol: float | None = None) -> tuple[int, int, int]:
    """Return ``(n_pos, n_neg, n_zero)`` — the inertia of a symmetric matrix."""
    t = _TOL if tol is None else tol
    evals = np.linalg.eigvalsh(np.asarray(m, dtype=float))
    scale = max(1.0, float(np.max(np.abs(evals))))
    thresh = t * scale
    pos = int(np.sum(evals > thresh))
    neg = int(np.sum(evals < -thresh))
    return pos, neg, len(evals) - pos - neg


def _is_isotropic(evals: np.ndarray, tol: float | None = None) -> bool:
    """True if all eigenvalues are (numerically) equal."""
    t = _TOL if tol is None else tol
    evals = np.asarray(evals, dtype=float)
    scale = max(1.0, float(np.max(np.abs(evals))))
    return float(evals.max() - evals.min()) <= t * scale


def _nonzero_evals(m: np.ndarray, tol: float | None = None) -> np.ndarray:
    """Non-zero eigenvalues of a symmetric matrix, ascending."""
    t = _TOL if tol is None else tol
    evals = np.linalg.eigvalsh(np.asarray(m, dtype=float))
    scale = max(1.0, float(np.max(np.abs(evals))))
    return evals[np.abs(evals) > t * scale]


def _classify_conic(a: np.ndarray, tol: float | None = None) -> EConicKind:
    """Classify a symmetric 3×3 conic matrix via its affine block form."""
    q = a[:2, :2]
    b = a[:2, 2]
    f = a[2, 2]
    r = _rank(a, tol)
    rq = _rank(q, tol)

    if r == 3:  # non-degenerate
        if rq == 1:
            return EConicKind.parabola
        ev = np.linalg.eigvalsh(q)
        if ev[0] * ev[1] > 0:  # definite quadratic part → ellipse/circle/imaginary
            c = np.linalg.solve(q, -b)
            fprime = f + float(b @ c)
            real = fprime < 0 if ev[0] > 0 else fprime > 0
            if not real:
                return EConicKind.imaginary
            return EConicKind.circle if _is_isotropic(ev, tol) else EConicKind.ellipse
        return EConicKind.hyperbola

    if r == 2:
        if rq == 2:
            ev = np.linalg.eigvalsh(q)
            return EConicKind.point_pair if ev[0] * ev[1] > 0 else EConicKind.line_pair
        if rq == 1:
            return EConicKind.parallel_line_pair

    if r == 1:
        return EConicKind.line

    return EConicKind.imaginary


def _classify_quadric(a: np.ndarray, tol: float | None = None) -> EQuadricKind:
    """Classify a symmetric 4×4 quadric matrix via its affine block form."""
    q = a[:3, :3]
    b = a[:3, 3]
    f = a[3, 3]
    r = _rank(a, tol)
    rq = _rank(q, tol)

    if r == 4:  # non-degenerate
        if rq == 3:
            ev = np.linalg.eigvalsh(q)
            if ev[0] * ev[2] > 0:  # definite → ellipsoid/sphere/imaginary
                c = np.linalg.solve(q, -b)
                fprime = f + float(b @ c)
                real = fprime < 0 if ev[0] > 0 else fprime > 0
                if not real:
                    return EQuadricKind.imaginary
                if _is_isotropic(ev, tol):
                    return EQuadricKind.sphere
                return EQuadricKind.ellipsoid
            # indefinite → hyperboloid (1- or 2-sheeted)
            c = np.linalg.solve(q, -b)
            fprime = f + float(b @ c)
            p, n, _ = _inertia(q, tol)
            one_sheet = (fprime < 0) == (p >= n)
            return (
                EQuadricKind.hyperboloid_1s
                if one_sheet
                else EQuadricKind.hyperboloid_2s
            )
        if rq == 2:  # paraboloid
            nz = _nonzero_evals(q, tol)
            if float(np.prod(nz)) > 0:
                return EQuadricKind.elliptic_paraboloid
            return EQuadricKind.hyperbolic_paraboloid
        return EQuadricKind.imaginary

    if r == 3:
        if rq == 3:
            p, n, _ = _inertia(q, tol)
            if p == 3 or n == 3:
                return EQuadricKind.imaginary  # imaginary cone (single point)
            return EQuadricKind.cone
        if rq == 2:
            nz = _nonzero_evals(q, tol)
            if float(np.prod(nz)) > 0:
                return EQuadricKind.elliptic_cylinder
            return EQuadricKind.hyperbolic_cylinder
        if rq == 1:
            return EQuadricKind.parabolic_cylinder
        return EQuadricKind.imaginary

    if r == 2:
        if rq == 0:
            return EQuadricKind.plane
        if rq == 1:
            return EQuadricKind.parallel_plane_pair
        ev = np.linalg.eigvalsh(q)
        if ev[0] * ev[2] > 0:
            return EQuadricKind.imaginary  # degenerate line / point
        return EQuadricKind.plane_pair

    if r == 1:
        return EQuadricKind.plane  # double plane

    return EQuadricKind.imaginary


@dataclass(frozen=True)
class Conic:
    """A conic (2D quadric), from its 6-entry coefficient vector or a symmetric 3×3 matrix.

    The coefficients use the ``pytanga.quadric`` ordering
    ``(a₁₃, a₂₃, (√2/2)a₃₃, (√2/2)a₁₁, (√2/2)a₂₂, a₁₂)``.
    """

    coeffs: tuple[float, ...]

    def __init__(self, data: "tuple[float, ...] | np.ndarray | Matrix") -> None:
        arr = np.asarray(data, dtype=float)
        if arr.ndim == 2:
            if arr.shape != (3, 3):
                raise ValueError(f"Conic matrix must be 3×3, got shape {arr.shape}")
            c = tuple(float(x) for x in _to_coeffs(arr))
        else:
            c = tuple(float(x) for x in arr)
            if len(c) != 6:
                raise ValueError(
                    f"Conic coeffs must be a 6-tuple, got length {len(c)}"
                )
        object.__setattr__(self, "coeffs", c)

    @cached_property
    def matrix(self) -> np.ndarray:
        """The symmetric 3×3 matrix ``A`` with ``xᵀ A x = 0``."""
        return _from_coeffs(self.coeffs)

    def to_matrix(self) -> np.ndarray:
        """Return the symmetric 3×3 matrix ``A`` (satisfies ``MatrixProvider``)."""
        return self.matrix

    @cached_property
    def rank(self) -> int:
        return _rank(self.matrix)

    @cached_property
    def signature(self) -> tuple[int, int, int]:
        """Inertia ``(n_pos, n_neg, n_zero)`` of the full 3×3 matrix."""
        return _inertia(self.matrix)

    @cached_property
    def kind(self) -> EConicKind:
        return _classify_conic(self.matrix)

    @cached_property
    def _quadratic(self) -> np.ndarray:
        return self.matrix[:2, :2]

    @cached_property
    def eigenvalues(self) -> tuple[float, ...]:
        """Eigenvalues of the 2×2 quadratic part (ascending)."""
        return tuple(float(x) for x in np.linalg.eigvalsh(self._quadratic))

    @cached_property
    def principal_directions(self) -> tuple[Direction, ...]:
        """Eigenvectors of the quadratic part as 2D ``Direction`` objects."""
        _, vecs = np.linalg.eigh(self._quadratic)
        return tuple(Direction(float(v[0]), float(v[1]), 0.0) for v in vecs.T)

    @cached_property
    def center(self) -> Point | None:
        """Center of a central conic (``None`` for parabolas / line pairs)."""
        if _rank(self._quadratic) < 2:
            return None
        c = np.linalg.solve(self._quadratic, -self.matrix[:2, 2])
        return Point(float(c[0]), float(c[1]), 0.0)

    @cached_property
    def rho(self) -> float | None:
        """Radius of a circle, else ``None``."""
        if self.kind is not EConicKind.circle:
            return None
        b = self.matrix[:2, 2]
        c = np.linalg.solve(self._quadratic, -b)
        fprime = self.matrix[2, 2] + float(b @ c)
        lam = self.eigenvalues[0]
        return float(np.sqrt(max(0.0, -fprime / lam)))

    def refine(self, tol: float | None = None) -> Any:
        """Refine this conic into its specific 2D entity (with optional tolerance)."""
        return refine_conic(self, tol=tol)

    def __repr__(self) -> str:
        return f"Conic({self.coeffs})"


@dataclass(frozen=True)
class Quadric3D:
    """A 3D quadric, from its 10-entry coefficient vector or a symmetric 4×4 matrix."""

    coeffs: tuple[float, ...]

    def __init__(self, data: "tuple[float, ...] | np.ndarray | Matrix") -> None:
        arr = np.asarray(data, dtype=float)
        if arr.ndim == 2:
            if arr.shape != (4, 4):
                raise ValueError(f"Quadric3D matrix must be 4×4, got shape {arr.shape}")
            c = tuple(float(x) for x in _to_coeffs(arr))
        else:
            c = tuple(float(x) for x in arr)
            if len(c) != 10:
                raise ValueError(
                    f"Quadric3D coeffs must be a 10-tuple, got length {len(c)}"
                )
        object.__setattr__(self, "coeffs", c)

    @cached_property
    def matrix(self) -> np.ndarray:
        """The symmetric 4×4 matrix ``Q`` with ``xᵀ Q x = 0``."""
        return _from_coeffs(self.coeffs)

    def to_matrix(self) -> np.ndarray:
        """Return the symmetric 4×4 matrix ``Q`` (satisfies ``MatrixProvider``)."""
        return self.matrix

    @cached_property
    def rank(self) -> int:
        return _rank(self.matrix)

    @cached_property
    def signature(self) -> tuple[int, int, int]:
        """Inertia ``(n_pos, n_neg, n_zero)`` of the full 4×4 matrix."""
        return _inertia(self.matrix)

    @cached_property
    def kind(self) -> EQuadricKind:
        return _classify_quadric(self.matrix)

    @cached_property
    def _quadratic(self) -> np.ndarray:
        return self.matrix[:3, :3]

    @cached_property
    def eigenvalues(self) -> tuple[float, ...]:
        """Eigenvalues of the 3×3 quadratic part (ascending)."""
        return tuple(float(x) for x in np.linalg.eigvalsh(self._quadratic))

    @cached_property
    def principal_directions(self) -> tuple[Direction, ...]:
        """Eigenvectors of the quadratic part as 3D ``Direction`` objects."""
        _, vecs = np.linalg.eigh(self._quadratic)
        return tuple(Direction(float(v[0]), float(v[1]), float(v[2])) for v in vecs.T)

    @cached_property
    def center(self) -> Point | None:
        """Center of a central quadric (``None`` for paraboloids / cylinders)."""
        if _rank(self._quadratic) < 3:
            return None
        c = np.linalg.solve(self._quadratic, -self.matrix[:3, 3])
        return Point(float(c[0]), float(c[1]), float(c[2]))

    @cached_property
    def rho(self) -> float | None:
        """Radius of a sphere, else ``None``."""
        if self.kind is not EQuadricKind.sphere:
            return None
        b = self.matrix[:3, 3]
        c = np.linalg.solve(self._quadratic, -b)
        fprime = self.matrix[3, 3] + float(b @ c)
        lam = self.eigenvalues[0]
        return float(np.sqrt(max(0.0, -fprime / lam)))

    def refine(self, tol: float | None = None) -> Any:
        """Refine this quadric into its specific 3D entity (with optional tolerance)."""
        return refine_quadric(self, tol=tol)

    def __repr__(self) -> str:
        return f"Quadric3D({self.coeffs})"


# Symmetric 2D alias (a conic is a 2D quadric).
Quadric2D = Conic
