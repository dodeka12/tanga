# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""A plain numeric square matrix and the ``MatrixProvider`` protocol.

The :class:`Matrix` type is a thin, typed wrapper around a ``numpy`` array using
the column-vector convention (``v' = M @ v``).  It is intentionally free of any
geometric-algebra or scene dependency so it can back camera intrinsics/
extrinsics and change-of-basis transforms alike.

Anything that exposes ``to_matrix() -> np.ndarray`` satisfies the runtime-
checkable :class:`MatrixProvider` protocol, which the scene graph accepts as a
transform input (``set_transform`` / ``apply_transform``).
"""

from __future__ import annotations

from typing import Any, Protocol, overload, runtime_checkable

import numpy as np

from pytanga.entity.direction import Direction
from pytanga.entity.point import Point

__all__ = ["Matrix", "MatrixProvider"]


@runtime_checkable
class MatrixProvider(Protocol):
    """A value that can provide a ``numpy`` matrix via ``to_matrix()``."""

    def to_matrix(self) -> np.ndarray: ...


def _axis(axis: object) -> np.ndarray:
    """Coerce an axis argument (a ``Direction`` or a 3-sequence) to a float vector."""
    if isinstance(axis, Direction):
        return np.array([axis.x, axis.y, axis.z], dtype=float)
    arr = np.asarray(axis, dtype=float)
    if arr.ndim != 1 or arr.shape[0] != 3:
        raise ValueError(f"axis must be a 3-vector, got {axis!r}")
    return arr


class Matrix:
    """A plain numeric square matrix (column-vector convention)."""

    def __init__(self, data: object) -> None:
        m = np.asarray(data, dtype=float)
        if m.ndim != 2 or m.shape[0] != m.shape[1]:
            raise ValueError(f"Matrix must be square, got shape {m.shape}")
        if m.shape[0] < 2:
            raise ValueError(f"Matrix must be at least 2×2, got shape {m.shape}")
        self.data = m

    # ── numpy interop ────────────────────────────────────────────────
    def to_matrix(self) -> np.ndarray:
        """Return the raw ``numpy`` matrix (satisfies ``MatrixProvider``)."""
        return self.data

    def to_numpy(self) -> np.ndarray:
        """Return the raw ``numpy`` matrix."""
        return self.data

    def __array__(self, dtype: Any = None) -> np.ndarray:
        if dtype is None:
            return self.data
        return np.asarray(self.data, dtype=dtype)

    @property
    def shape(self) -> tuple[int, int]:
        return (int(self.data.shape[0]), int(self.data.shape[1]))

    # ── basic linear algebra ─────────────────────────────────────────
    @property
    def T(self) -> "Matrix":
        return Matrix(self.data.T)

    def inverse(self) -> "Matrix":
        return Matrix(np.linalg.inv(self.data))

    def det(self) -> float:
        return float(np.linalg.det(self.data))

    def is_rotation(self, atol: float = 1e-6) -> bool:
        """True for a 3×3 (or 4×4) proper rotation (orthonormal, det ≈ +1)."""
        m = self.data
        if m.shape[0] not in (3, 4):
            return False
        r = m[:3, :3]
        return bool(np.allclose(r @ r.T, np.eye(3), atol=atol)) and bool(
            np.isclose(np.linalg.det(r), 1.0, atol=atol)
        )

    # ── application ──────────────────────────────────────────────────
    @overload
    def __matmul__(self, other: Matrix) -> Matrix: ...
    @overload
    def __matmul__(self, other: Point) -> Point: ...
    @overload
    def __matmul__(self, other: Direction) -> Direction: ...
    @overload
    def __matmul__(self, other: np.ndarray) -> np.ndarray: ...
    def __matmul__(self, other: object) -> object:
        m = self.data
        if isinstance(other, Matrix):
            return Matrix(m @ other.data)
        if isinstance(other, Point):
            return self._apply_point(other)
        if isinstance(other, Direction):
            return self._apply_direction(other)
        return m @ np.asarray(other)

    def _apply_point(self, p: Point) -> Point:
        m = self.data
        xyz = np.array([p.x, p.y, p.z], dtype=float)
        if m.shape == (4, 4):
            v = m @ np.append(xyz, 1.0)
            w = v[3]
            return Point(v[0] / w, v[1] / w, v[2] / w)
        if m.shape == (3, 3):
            v = m @ xyz
            return Point(v[0], v[1], v[2])
        raise ValueError(f"Matrix shape {m.shape} cannot transform a 3D vector")

    def _apply_direction(self, d: Direction) -> Direction:
        m = self.data
        xyz = np.array([d.x, d.y, d.z], dtype=float)
        if m.shape == (4, 4):
            v = m @ np.append(xyz, 0.0)
            return Direction(v[0], v[1], v[2])
        if m.shape == (3, 3):
            v = m @ xyz
            return Direction(v[0], v[1], v[2])
        raise ValueError(f"Matrix shape {m.shape} cannot transform a 3D vector")

    # ── constructors ─────────────────────────────────────────────────
    @classmethod
    def identity(cls, n: int) -> "Matrix":
        return cls(np.eye(n))

    @classmethod
    def translation(cls, tx: float, ty: float, tz: float) -> "Matrix":
        m = np.eye(4)
        m[0, 3] = float(tx)
        m[1, 3] = float(ty)
        m[2, 3] = float(tz)
        return cls(m)

    @classmethod
    def rotation(cls, axis: object, angle: float) -> "Matrix":
        """Return a 3×3 rotation matrix from an axis-angle pair (Rodrigues)."""
        a = _axis(axis)
        n = float(np.linalg.norm(a))
        if n < 1e-12:
            return cls(np.eye(3))
        a = a / n
        x, y, z = a
        c, s = float(np.cos(angle)), float(np.sin(angle))
        c1 = 1.0 - c
        r = np.array(
            [
                [c + x * x * c1, x * y * c1 - z * s, x * z * c1 + y * s],
                [y * x * c1 + z * s, c + y * y * c1, y * z * c1 - x * s],
                [z * x * c1 - y * s, z * y * c1 + x * s, c + z * z * c1],
            ],
            dtype=float,
        )
        return cls(r)

    @classmethod
    def scale(cls, sx: float, sy: float | None = None, sz: float | None = None) -> "Matrix":
        """Return a 3×3 scale matrix (uniform when only ``sx`` is given)."""
        if sy is None and sz is None:
            sx = sy = sz = float(sx)
        elif sy is None or sz is None:
            raise ValueError("scale() requires both sy and sz, or neither")
        else:
            sx, sy, sz = float(sx), float(sy), float(sz)
        return cls(np.diag([sx, sy, sz]))

    @classmethod
    def from_axes(cls, x: object, y: object, z: object) -> "Matrix":
        """Return the 3×3 change-of-basis whose columns are the axes ``x``/``y``/``z``."""
        return cls(np.column_stack([_axis(x), _axis(y), _axis(z)]))

    @classmethod
    def from_R_t(cls, R: object, t: object) -> "Matrix":
        """Return the 4×4 rigid transform ``[R t; 0 1]`` from a 3×3 rotation
        and a 3-vector translation."""
        r = np.asarray(R, dtype=float)
        if r.shape != (3, 3):
            raise ValueError(f"R must be 3×3, got shape {r.shape}")
        t = np.asarray(t, dtype=float)
        if t.shape != (3,):
            raise ValueError(f"t must be a length-3 vector, got shape {t.shape}")
        m = np.eye(4)
        m[:3, :3] = r
        m[:3, 3] = t
        return cls(m)

    # ── misc ─────────────────────────────────────────────────────────
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Matrix):
            return bool(np.allclose(self.data, other.data))
        return NotImplemented

    def __repr__(self) -> str:
        return f"Matrix({self.data.shape[0]}×{self.data.shape[1]})"
