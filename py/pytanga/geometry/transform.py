# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Canonical TRS transform + argument-coercion helpers.

:class:`Transform` is the single per-entity placement node of the Tanga
viewer: position + rotation + scale, with a derived 4×4 matrix and mutators.
The rotation is stored as a quaternion ``(x, y, z, w)`` (the single source of
truth); Euler triples are accepted on input and converted.  The pure
matrix/TRS/quaternion math lives in :mod:`pytanga.geometry.transforms`; this
module only wraps it into a mutable, JSON-serializable class plus the
argument-coercion helpers shared by the ``viz`` layer.

This module is geometry-only: it imports ``numpy``, the entity/operator
dataclasses, and the sibling ``transforms`` module — never ``viz``.
"""

from __future__ import annotations

from types import NotImplementedType
from typing import TYPE_CHECKING, Any, TypeAlias, Union

import numpy as np

from pytanga.geometry.entities import Direction, Point
from pytanga.geometry.operators import Rotor

from . import transforms as _T
from .matrix import MatrixProvider
from .transforms import TransformOperator

if TYPE_CHECKING:
    from pytanga.algebra import MV

__all__ = [
    "Transform",
    "TransformInput",
    "TransformOperator",
    "TransformRotation",
    "Triple",
    "_as_euler",
    "_as_vec3",
]

#: A 3-vector: a Point/Direction entity or a ``(x, y, z)`` 3-sequence.
Vec3: TypeAlias = Point | Direction | tuple[float, float, float]

#: A 3-tuple of floats (scale components, or an Euler-angle triple).
Triple: TypeAlias = tuple[float, float, float]

#: A scene/member-transform rotation: an Euler ``(rx, ry, rz)`` triple, a
#: quaternion ``(x, y, z, w)``, or a Rotor (all converted to a quaternion
#: internally).
TransformRotation: TypeAlias = Rotor | Triple | tuple[float, float, float, float]

#: A scene-transform argument: a ``Transform`` node, an ``MV`` (analyzed to an
#: operator), a GA operator dataclass (Rotor/GeneralRotor/Translator/Motor/Dilator),
#: or anything satisfying ``MatrixProvider`` (a ``Matrix`` / ``CoordinateFrame``).
TransformInput: TypeAlias = Union["Transform", "MV", TransformOperator, MatrixProvider]


def _is_vector_like(value: Any) -> bool:
    """Return ``True`` for non-scalar 3-vectors (tuples/lists/entity-like)."""
    if isinstance(value, (int, float, np.integer, np.floating)):
        return False
    return hasattr(value, "__len__") or (
        hasattr(value, "x") and hasattr(value, "y") and hasattr(value, "z")
    )


def _as_vec3(value: Any) -> tuple[float, float, float]:
    """Best-effort convert *value* to a 3-vector of floats.

    Accepts objects with ``x``/``y``/``z`` attributes (``Point``,
    ``Direction``, …) or any 3-sequence.
    """
    if hasattr(value, "x") and hasattr(value, "y") and hasattr(value, "z"):
        return (float(value.x), float(value.y), float(value.z))
    seq = tuple(value)
    if len(seq) != 3:
        raise ValueError(f"Expected a 3-vector, got {value!r}")
    return (float(seq[0]), float(seq[1]), float(seq[2]))


def _as_euler(value: Any) -> tuple[float, float, float]:
    """Coerce a rotation to an Euler ``(rx, ry, rz)`` triple (order ``"XYZ"``).

    Accepts a Rotor (axis-angle, converted to Euler) or an Euler triple. A
    GeneralRotor with a displaced rotation centre cannot be represented as a
    plain transform rotation and raises.
    """
    angle = getattr(value, "angle", None)
    axis = getattr(value, "axis", None)
    if angle is not None and axis is not None:
        origin = getattr(value, "origin", None)
        if origin is not None:
            ox, oy, oz = _as_vec3(origin)
            if abs(ox) > 1e-12 or abs(oy) > 1e-12 or abs(oz) > 1e-12:
                raise TypeError(
                    "A rotation with a displaced origin (GeneralRotor) cannot be "
                    "used as a transform rotation; pass a Rotor or an Euler triple"
                )
        _, euler, _ = _T.to_trs(_T.rotation_matrix(axis, float(angle)))
        return euler
    return _as_vec3(value)


def _as_quaternion(value: Any) -> tuple[float, float, float, float]:
    """Coerce a rotation to a quaternion ``(x, y, z, w)``.

    Accepts a Rotor (axis-angle), an Euler ``(rx, ry, rz)`` triple (order
    ``"XYZ"``), or a quaternion.  A GeneralRotor with a displaced rotation
    centre cannot be represented as a plain transform rotation and raises.
    """
    angle = getattr(value, "angle", None)
    axis = getattr(value, "axis", None)
    if angle is not None and axis is not None:
        origin = getattr(value, "origin", None)
        if origin is not None:
            ox, oy, oz = _as_vec3(origin)
            if abs(ox) > 1e-12 or abs(oy) > 1e-12 or abs(oz) > 1e-12:
                raise TypeError(
                    "A rotation with a displaced origin (GeneralRotor) cannot be "
                    "used as a transform rotation; pass a Rotor, an Euler triple, "
                    "or a quaternion"
                )
        return _T.quat_from_axis_angle(axis, float(angle))

    seq = tuple(value)
    if len(seq) == 4:
        return (float(seq[0]), float(seq[1]), float(seq[2]), float(seq[3]))
    if len(seq) == 3:
        euler = _as_euler(seq)
        rx = _T.rotation_matrix((1.0, 0.0, 0.0), euler[0])
        ry = _T.rotation_matrix((0.0, 1.0, 0.0), euler[1])
        rz = _T.rotation_matrix((0.0, 0.0, 1.0), euler[2])
        return _T.matrix_to_quat((rx @ ry @ rz)[:3, :3])
    raise ValueError(
        f"Expected a quaternion (x, y, z, w) or Euler (rx, ry, rz), got {value!r}"
    )


class Transform:
    """Canonical TRS transform (translation, quaternion rotation, scale).

    Position and scale are stored as triples; the rotation is stored as a
    quaternion ``(x, y, z, w)`` (the single source of truth — gimbal-lock
    free).  The 4×4 matrix is derived on demand and used for
    composition/decomposition only.
    """

    def __init__(
        self,
        position: Vec3 = (0.0, 0.0, 0.0),
        rotation: TransformRotation = (0.0, 0.0, 0.0, 1.0),
        scale: Triple = (1.0, 1.0, 1.0),
    ) -> None:
        self.position: tuple[float, float, float] = _as_vec3(position)
        self.rotation: tuple[float, float, float, float] = _as_quaternion(rotation)
        self.scale: tuple[float, float, float] = _as_vec3(scale)

    def matrix(self) -> np.ndarray:
        """Return the derived 4×4 transform matrix ``T @ R(q) @ S``."""
        return (
            _T.translation_matrix(*self.position)
            @ _T.quat_to_matrix(self.rotation)
            @ _T.scale_matrix(*self.scale)
        )

    def to_matrix(self) -> np.ndarray:
        """Return the derived 4×4 matrix (satisfies ``MatrixProvider``)."""
        return self.matrix()

    def set_matrix(self, m: Any) -> "Transform":
        """Set position/rotation/scale from a 4×4 matrix (decompose)."""
        m = np.asarray(m, dtype=np.float64)
        self.position = (float(m[0, 3]), float(m[1, 3]), float(m[2, 3]))
        r = m[:3, :3].copy()
        sx = float(np.linalg.norm(r[:, 0]))
        sy = float(np.linalg.norm(r[:, 1]))
        sz = float(np.linalg.norm(r[:, 2]))
        self.scale = (sx, sy, sz)
        if sx > _T._EPS:
            r[:, 0] /= sx
        if sy > _T._EPS:
            r[:, 1] /= sy
        if sz > _T._EPS:
            r[:, 2] /= sz
        self.rotation = _T.matrix_to_quat(r)
        return self

    @classmethod
    def from_matrix(cls, m: Any) -> "Transform":
        """Build a ``Transform`` from a 4×4 matrix (decomposed to TRS)."""
        return cls().set_matrix(m)

    @classmethod
    def from_operator(cls, op: TransformOperator) -> "Transform":
        """Build a ``Transform`` from a GA operator (``Translator``/``Rotor``/
        ``GeneralRotor``/``Motor``/``Dilator``).

        Uses the same ``operator_to_matrix`` conversion that
        :meth:`VizSceneObject.apply_transform` relies on.
        """
        return cls().set_matrix(_T.operator_to_matrix(op))

    def apply_matrix(self, m: Any, space: str = "local") -> "Transform":
        """Compose with *m* in local or world space.

        ``"local"`` post-multiplies (``M_new = M @ m``); ``"world"``
        pre-multiplies (``M_new = m @ M``).  The result is decomposed back to
        TRS.
        """
        m = np.asarray(m, dtype=np.float64)
        if space == "local":
            return self.set_matrix(self.matrix() @ m)
        if space == "world":
            return self.set_matrix(m @ self.matrix())
        raise ValueError(f"Unknown space {space!r}; expected 'local' or 'world'")

    def translate(self, x: Any = 0.0, y: float = 0.0, z: float = 0.0) -> "Transform":
        """Translate by ``(x, y, z)``, or by a 3-vector supplied as *x*."""
        if _is_vector_like(x):
            dx, dy, dz = _as_vec3(x)
        else:
            dx, dy, dz = float(x), float(y), float(z)
        self.position = (
            self.position[0] + dx,
            self.position[1] + dy,
            self.position[2] + dz,
        )
        return self

    def rotate(self, axis: Any, angle: float) -> "Transform":
        """Rotate in local space by *angle* about *axis* (axis-angle)."""
        q = _T.quat_from_axis_angle(axis, angle)
        self.rotation = _T.quat_mul(self.rotation, q)
        return self

    def scale_by(
        self,
        x: float = 1.0,
        y: float | None = None,
        z: float | None = None,
    ) -> "Transform":
        """Scale component-wise (or uniformly when only *x* is given)."""
        if y is None and z is None:
            sx = sy = sz = float(x)
        else:
            sx = float(x)
            sy = float(y if y is not None else 1.0)
            sz = float(z if z is not None else 1.0)
        self.scale = (
            self.scale[0] * sx,
            self.scale[1] * sy,
            self.scale[2] * sz,
        )
        return self

    def set(
        self,
        position: Vec3 | None = None,
        rotation: TransformRotation | None = None,
        scale: Triple | None = None,
    ) -> "Transform":
        """Set position / rotation / scale (only the provided components)."""
        if position is not None:
            self.position = _as_vec3(position)
        if rotation is not None:
            self.rotation = _as_quaternion(rotation)
        if scale is not None:
            self.scale = _as_vec3(scale)
        return self

    def apply(self, obj: Any) -> Point | Direction | NotImplementedType:
        """Apply this transform to a :class:`Point` or :class:`Direction`.

        ``Point`` → ``R·S·p + t``; ``Direction`` → ``R·S·d`` (a direction is
        an ideal point, so no translation).  Any other type returns
        :data:`NotImplemented` so the operator overloads fall through.
        """
        if isinstance(obj, Point):
            m = self.matrix()
            p = np.array([obj.x, obj.y, obj.z, 1.0], dtype=np.float64)
            r = m @ p
            return Point(float(r[0]), float(r[1]), float(r[2]))
        if isinstance(obj, Direction):
            m = self.matrix()
            d = np.array([obj.x, obj.y, obj.z, 0.0], dtype=np.float64)
            r = m @ d
            return Direction(float(r[0]), float(r[1]), float(r[2]))
        return NotImplemented

    def __matmul__(self, other: Any) -> Point | Direction | NotImplementedType:
        """``transform @ point`` / ``transform @ direction``."""
        return self.apply(other)

    def __rmatmul__(self, other: Any) -> Point | Direction | NotImplementedType:
        """``point @ transform`` / ``direction @ transform``."""
        return self.apply(other)

    def __mul__(self, other: Any) -> Point | Direction | NotImplementedType:
        """``transform * point`` / ``transform * direction``."""
        return self.apply(other)

    def __rmul__(self, other: Any) -> Point | Direction | NotImplementedType:
        """``point * transform`` / ``direction * transform``."""
        return self.apply(other)

    def to_dict(self) -> dict[str, Any]:
        """Return the JSON-ready TRS dict (``rotation`` is a quaternion)."""
        return {
            "position": list(self.position),
            "rotation": list(self.rotation),
            "scale": list(self.scale),
        }
