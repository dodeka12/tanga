# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Transform math for the scene graph.

Converts geometry entities and operator dataclasses into 4×4 matrices and
TRS (translation / rotation / scale) tuples.  Pure math on the dataclass
fields — no algebra analysis, no scene dependency.  Usable by the scene
graph and by standalone user code.

Conventions:
    - Matrices are :class:`numpy.ndarray` of shape ``(4, 4)`` and
      ``dtype=float64``.
    - Column-vector convention ``v' = M @ v``; composition is ``M1 @ M2``
      applies ``M2`` first.  Translations therefore live in the last column.
    - Rotation serialization uses a 3×3 rotation matrix decomposed to Euler
      angles with order ``"XYZ"`` (three.js default), i.e. ``R = Rx @ Ry @ Rz``.
"""

from __future__ import annotations

import numpy as np

from pytanga.geometry.entities import Direction, Point
from pytanga.geometry.operators import Dilator, GeneralRotor, Motor, Rotor, Translator

_EPS = 1e-12

__all__ = [
    "translation_matrix",
    "rotation_matrix",
    "scale_matrix",
    "to_trs",
    "translator_to_matrix",
    "rotor_to_matrix",
    "general_rotor_to_matrix",
    "motor_to_matrix",
    "dilator_to_matrix",
    "operator_to_matrix",
    "operator_to_trs",
    "to_matrix",
    "to_trs_tuple",
]


def translation_matrix(tx: float, ty: float, tz: float) -> np.ndarray:
    """Return a 4×4 translation matrix (column-vector convention)."""
    m = np.eye(4, dtype=np.float64)
    m[0, 3] = float(tx)
    m[1, 3] = float(ty)
    m[2, 3] = float(tz)
    return m


def rotation_matrix(axis: Direction | tuple[float, float, float], angle: float) -> np.ndarray:
    """Return a 4×4 rotation matrix from an axis-angle representation.

    The axis is normalized before building the rotation (Rodrigues' formula).
    A zero-length axis yields the identity rotation.
    """
    if isinstance(axis, Direction):
        a = np.array([axis.x, axis.y, axis.z], dtype=np.float64)
    else:
        a = np.array(axis, dtype=np.float64)
    n = float(np.linalg.norm(a))
    if n < _EPS:
        return np.eye(4, dtype=np.float64)
    a = a / n
    x, y, z = a
    c = float(np.cos(angle))
    s = float(np.sin(angle))
    c1 = 1.0 - c
    r = np.array(
        [
            [c + x * x * c1, x * y * c1 - z * s, x * z * c1 + y * s],
            [y * x * c1 + z * s, c + y * y * c1, y * z * c1 - x * s],
            [z * x * c1 - y * s, z * y * c1 + x * s, c + z * z * c1],
        ],
        dtype=np.float64,
    )
    m = np.eye(4, dtype=np.float64)
    m[:3, :3] = r
    return m


def scale_matrix(sx: float, sy: float | None = None, sz: float | None = None) -> np.ndarray:
    """Return a 4×4 scale matrix.

    ``scale_matrix(f)`` applies a uniform scale by ``f`` on all axes;
    ``scale_matrix(sx, sy, sz)`` applies component-wise scaling.
    """
    if sy is None and sz is None:
        sy = sz = float(sx)
        sx = float(sx)
    else:
        sx = float(sx)
        sy = float(sy)
        sz = float(sz)
    m = np.eye(4, dtype=np.float64)
    m[0, 0] = sx
    m[1, 1] = sy
    m[2, 2] = sz
    return m


def _mat3_to_euler(r: np.ndarray) -> tuple[float, float, float]:
    """Decompose a 3×3 rotation matrix into Euler angles (order ``"XYZ"``).

    Assumes ``R = Rx(x) @ Ry(y) @ Rz(z)``, matching three.js' default Euler
    order.  Gimbal lock falls back to folding the rotation into ``z``.
    """
    r00, r01, r02 = r[0, 0], r[0, 1], r[0, 2]
    r10, r11, r12 = r[1, 0], r[1, 1], r[1, 2]
    r20, r21, r22 = r[2, 0], r[2, 1], r[2, 2]

    y = float(np.arcsin(np.clip(r02, -1.0, 1.0)))
    cy = float(np.cos(y))
    if abs(cy) > _EPS:
        x = float(np.arctan2(-r12, r22))
        z = float(np.arctan2(-r01, r00))
    else:
        x = 0.0
        z = float(np.arctan2(r10, r11))
    return (x, y, z)


def to_trs(m: np.ndarray) -> tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]:
    """Decompose a 4×4 matrix into ``(position, euler, scale)``.

    ``position`` is the last column, ``scale`` the column norms of the 3×3
    linear part, and ``euler`` the ``"XYZ"`` Euler angles of the normalized
    rotation part.  Assumes no shear.
    """
    m = np.asarray(m, dtype=np.float64)
    if m.shape != (4, 4):
        raise ValueError(f"Expected a (4, 4) matrix, got {m.shape}")

    position = (float(m[0, 3]), float(m[1, 3]), float(m[2, 3]))
    r = m[:3, :3].copy()
    sx = float(np.linalg.norm(r[:, 0]))
    sy = float(np.linalg.norm(r[:, 1]))
    sz = float(np.linalg.norm(r[:, 2]))
    scale = (sx, sy, sz)

    if sx > _EPS:
        r[:, 0] /= sx
    if sy > _EPS:
        r[:, 1] /= sy
    if sz > _EPS:
        r[:, 2] /= sz

    return position, _mat3_to_euler(r), scale


def translator_to_matrix(translator: Translator) -> np.ndarray:
    """Return the 4×4 matrix of a :class:`Translator`."""
    v = translator.vector
    return translation_matrix(v.x, v.y, v.z)


def rotor_to_matrix(rotor: Rotor) -> np.ndarray:
    """Return the 4×4 matrix of a :class:`Rotor`."""
    return rotation_matrix(rotor.axis, rotor.angle)


def general_rotor_to_matrix(general_rotor: GeneralRotor) -> np.ndarray:
    """Return the 4×4 matrix of a :class:`GeneralRotor`.

    The underlying transform is ``T(origin) @ R @ T(-origin)``.
    """
    ox, oy, oz = general_rotor.origin.x, general_rotor.origin.y, general_rotor.origin.z
    t = translation_matrix(ox, oy, oz)
    t_inv = translation_matrix(-ox, -oy, -oz)
    r = rotation_matrix(general_rotor.axis, general_rotor.angle)
    return t @ r @ t_inv


def motor_to_matrix(motor: Motor) -> np.ndarray:
    """Return the 4×4 matrix of a :class:`Motor`.

    The motor applies ``T(t) @ R`` (rotation followed by translation).
    """
    return translator_to_matrix(motor.translator) @ rotor_to_matrix(motor.rotor)


def dilator_to_matrix(dilator: Dilator) -> np.ndarray:
    """Return the 4×4 matrix of a :class:`Dilator`.

    The underlying transform is ``T(origin) @ S(f) @ T(-origin)``.
    """
    ox, oy, oz = dilator.origin.x, dilator.origin.y, dilator.origin.z
    t = translation_matrix(ox, oy, oz)
    t_inv = translation_matrix(-ox, -oy, -oz)
    s = scale_matrix(dilator.factor)
    return t @ s @ t_inv


def operator_to_matrix(op) -> np.ndarray:
    """Return the 4×4 matrix for a supported operator dataclass."""
    if isinstance(op, Translator):
        return translator_to_matrix(op)
    if isinstance(op, Rotor):
        return rotor_to_matrix(op)
    if isinstance(op, GeneralRotor):
        return general_rotor_to_matrix(op)
    if isinstance(op, Motor):
        return motor_to_matrix(op)
    if isinstance(op, Dilator):
        return dilator_to_matrix(op)
    raise TypeError(f"Unsupported operator type: {type(op).__name__}")


def operator_to_trs(op) -> tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]:
    """Return ``(position, euler, scale)`` for a supported operator.

    Analytical decompositions are used where possible to avoid round-trip
    error:

    - ``Rotor`` → zero position, rotation euler, unit scale.
    - ``Translator`` → vector position, zero euler, unit scale.
    - ``Motor`` → translator vector position, rotor euler, unit scale.
    - ``GeneralRotor`` → position ``(I - R) @ origin``, rotor euler, unit scale.
    - ``Dilator`` → position ``(1 - f) * origin``, zero euler, scale ``(f, f, f)``.
    """
    if isinstance(op, Rotor):
        r = rotation_matrix(op.axis, op.angle)[:3, :3]
        return (0.0, 0.0, 0.0), _mat3_to_euler(r), (1.0, 1.0, 1.0)
    if isinstance(op, Translator):
        v = op.vector
        return (float(v.x), float(v.y), float(v.z)), (0.0, 0.0, 0.0), (1.0, 1.0, 1.0)
    if isinstance(op, Motor):
        r = rotation_matrix(op.rotor.axis, op.rotor.angle)[:3, :3]
        v = op.translator.vector
        return (float(v.x), float(v.y), float(v.z)), _mat3_to_euler(r), (1.0, 1.0, 1.0)
    if isinstance(op, GeneralRotor):
        r = rotation_matrix(op.axis, op.angle)[:3, :3]
        origin = np.array([op.origin.x, op.origin.y, op.origin.z], dtype=np.float64)
        p = (np.eye(3) - r) @ origin
        return (float(p[0]), float(p[1]), float(p[2])), _mat3_to_euler(r), (1.0, 1.0, 1.0)
    if isinstance(op, Dilator):
        f = float(op.factor)
        origin = np.array([op.origin.x, op.origin.y, op.origin.z], dtype=np.float64)
        p = (1.0 - f) * origin
        return (float(p[0]), float(p[1]), float(p[2])), (0.0, 0.0, 0.0), (f, f, f)
    raise TypeError(f"Unsupported operator type: {type(op).__name__}")


def to_matrix(obj) -> np.ndarray:
    """Return the 4×4 matrix for a supported entity or operator.

    - :class:`Point` → translation matrix.
    - :class:`Direction` → translation matrix (treated as a move vector).
    - operator dataclasses → :func:`operator_to_matrix`.
    """
    if isinstance(obj, Point):
        return translation_matrix(obj.x, obj.y, obj.z)
    if isinstance(obj, Direction):
        return translation_matrix(obj.x, obj.y, obj.z)
    return operator_to_matrix(obj)


def to_trs_tuple(obj) -> tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]:
    """Return ``(position, euler, scale)`` for a supported entity/operator."""
    if isinstance(obj, Point):
        return (float(obj.x), float(obj.y), float(obj.z)), (0.0, 0.0, 0.0), (1.0, 1.0, 1.0)
    if isinstance(obj, Direction):
        return (float(obj.x), float(obj.y), float(obj.z)), (0.0, 0.0, 0.0), (1.0, 1.0, 1.0)
    return operator_to_trs(obj)