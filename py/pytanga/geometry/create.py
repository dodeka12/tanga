# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Geometry creation dispatcher — MV construction from Entity/Operator dataclasses.

This is the inverse of :func:`~.analysis.analyze`:
``create(basis, analyze(mv))`` reproduces *mv* (up to normalisation).
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from .entities import (
    Circle,
    Cone,
    Conic,
    Cylinder,
    Direction,
    Ellipse,
    Ellipsoid,
    Entity,
    HDirection,
    HPoint,
    Hyperbola,
    Line,
    LinePair,
    ParallelLinePair,
    Parabola,
    Plane,
    Point,
    PointPair,
    Quadric3D,
    Space,
    Sphere,
)
from .operators import (
    Dilator,
    GeneralRotor,
    Inversion,
    Motor,
    Operator,
    ReflectionLine,
    ReflectionPlane,
    ReflectionPoint,
    Rotor,
    Translator,
)

if TYPE_CHECKING:
    from pytanga.algebra._algebra import Algebra
    from pytanga.algebra._mv import MV


def _detect(basis) -> str:
    """Return ``'e2'``, ``'p2'``, ``'pga2'``, ``'n2'``, ``'e3'``, ``'p3'``, ``'pga3'``, or ``'n3'`` for a basis instance."""
    from pytanga.basis.e2 import BasisE2
    from pytanga.basis.e3 import BasisE3
    from pytanga.basis.n2 import BasisN2
    from pytanga.basis.n3 import BasisN3
    from pytanga.basis.p2 import BasisP2
    from pytanga.basis.p3 import BasisP3
    from pytanga.basis.pga2 import BasisPGA2
    from pytanga.basis.pga3 import BasisPGA3
    from pytanga.quadric import BasisQ2, BasisQ3

    # Quadric-space bases (distinct Algebra subclasses)
    if isinstance(basis, BasisQ3):
        return "q3"
    if isinstance(basis, BasisQ2):
        return "q2"

    # 3D algebras
    if isinstance(basis, BasisPGA3):
        return "pga3"
    elif isinstance(basis, BasisN3):
        return "n3"
    elif isinstance(basis, BasisP3):
        return "p3"
    elif isinstance(basis, BasisE3):
        return "e3"
    # 2D algebras — PGA2 before N2 (inheritance)
    elif isinstance(basis, BasisPGA2):
        return "pga2"
    elif isinstance(basis, BasisN2):
        return "n2"
    elif isinstance(basis, BasisP2):
        return "p2"
    elif isinstance(basis, BasisE2):
        return "e2"
    else:
        raise ValueError(f"Unknown basis type: {type(basis).__name__}")


# ═══════════════════════════════════════════════════════════════
# Entity creation
# ═══════════════════════════════════════════════════════════════


def create_entity(basis: Algebra, entity: Entity) -> MV:
    """Create an MV representing a geometric entity.

    Parameters
    ----------
    basis : Algebra
        An algebra instance (e.g. ``BasisE3()``).  Its ``opns`` flag
        determines whether the entity is created in OPNS or IPNS.
    entity : Entity
        An :class:`~.entities.Entity` dataclass.

    Returns
    -------
    MV
        The multivector representation.
    """
    from . import (
        create_e2,
        create_e3,
        create_n2,
        create_n3,
        create_p2,
        create_p3,
        create_pga2,
        create_pga3,
        create_q2,
        create_q3,
    )

    modules = {
        "e2": create_e2,
        "e3": create_e3,
        "n2": create_n2,
        "n3": create_n3,
        "p2": create_p2,
        "p3": create_p3,
        "pga2": create_pga2,
        "pga3": create_pga3,
        "q2": create_q2,
        "q3": create_q3,
    }
    mod = modules[_detect(basis)]

    if isinstance(
        entity,
        (
            Conic,
            Quadric3D,
            Hyperbola,
            Parabola,
            LinePair,
            ParallelLinePair,
            Ellipse,
            Ellipsoid,
            Cylinder,
            Cone,
        ),
    ):
        if _detect(basis) not in ("q2", "q3"):
            raise TypeError(
                f"Entity type {type(entity).__name__} not supported in {_detect(basis)}"
            )
        return mod.create_entity(basis, entity)

    if isinstance(entity, Point):
        return mod.create_point(basis, entity.x, entity.y, entity.z)
    elif isinstance(entity, Direction):
        return mod.create_direction(basis, entity.x, entity.y, entity.z)
    elif isinstance(entity, HPoint):
        return mod.create_homogeneous_point(basis, entity.point, entity.weight)
    elif isinstance(entity, HDirection):
        alg_type = _detect(basis)
        if alg_type not in ("n3", "n2"):
            raise TypeError(
                f"HDirection entity requires conformal model (N3/N2); "
                f"not supported in {alg_type.upper()}."
            )
        return mod.create_homogeneous_direction(
            basis, entity.direction.x, entity.direction.y, entity.direction.z
        )
    elif isinstance(entity, PointPair):
        if entity.is_imaginary and _detect(basis) in ("n3", "pga3"):
            # Reconstruct via dual-of-circle path using stored center/dir/separation
            if entity._center is not None and entity._direction is not None:
                return mod.create_imag_point_pair(
                    basis,
                    entity._center,
                    entity._direction,
                    entity._separation or 1.0,
                )
            # Fallback: reconstruct center/direction from point_a/point_b
            center = Point(
                (entity.point_a.x + entity.point_b.x) / 2,
                (entity.point_a.y + entity.point_b.y) / 2,
                (entity.point_a.z + entity.point_b.z) / 2,
            )
            direction = Direction(
                entity.point_b.x - entity.point_a.x,
                entity.point_b.y - entity.point_a.y,
                entity.point_b.z - entity.point_a.z,
            )
            separation = math.sqrt(direction.x**2 + direction.y**2 + direction.z**2)
            return mod.create_imag_point_pair(
                basis,
                center,
                direction,
                separation,
            )
        return mod.create_point_pair(basis, entity.point_a, entity.point_b)
    elif isinstance(entity, Line):
        return mod.create_line(basis, entity.origin, entity.direction)
    elif isinstance(entity, Circle):
        if entity.is_imaginary and _detect(basis) in ("n3", "pga3"):
            return mod.create_imag_circle(
                basis,
                entity.center,
                entity.normal,
                entity.radius,
            )
        return mod.create_circle(basis, entity.center, entity.normal, entity.radius)
    elif isinstance(entity, Plane):
        return mod.create_plane(basis, entity)
    elif isinstance(entity, Sphere):
        if entity.is_imaginary:
            if _detect(basis) in ("n2", "n3"):
                return mod.create_sphere(
                    basis,
                    entity.center,
                    entity.radius,
                    is_imaginary=True,
                )
            raise NotImplementedError("Imaginary spheres are not supported yet.")
        return mod.create_sphere(basis, entity.center, entity.radius)
    elif isinstance(entity, Space):
        return mod.create_space(basis, scale=entity.scale)
    else:
        raise TypeError(
            f"Entity type {type(entity).__name__} not supported in {_detect(basis)}"
        )


# ═══════════════════════════════════════════════════════════════
# Operator creation
# ═══════════════════════════════════════════════════════════════


def create_operator(basis: Algebra, operator: Operator) -> MV:
    """Create an MV representing a versor / operator.

    Parameters
    ----------
    basis : Algebra
        An algebra instance.
    operator : Operator
        An :class:`~.operators.Operator` dataclass.

    Returns
    -------
    MV
        The multivector representation.
    """
    from . import (
        create_e2,
        create_e3,
        create_n2,
        create_n3,
        create_p2,
        create_p3,
        create_pga2,
        create_pga3,
    )

    modules = {
        "e2": create_e2,
        "e3": create_e3,
        "n2": create_n2,
        "n3": create_n3,
        "p2": create_p2,
        "p3": create_p3,
        "pga2": create_pga2,
        "pga3": create_pga3,
    }
    mod = modules[_detect(basis)]

    if isinstance(operator, ReflectionLine):
        alg_type = _detect(basis)
        if alg_type in ("n3", "n2", "pga2", "pga3"):
            return mod.create_reflection_line(basis, operator.line)
        # PGA/E/P modules — use direction from line (origin-only)
        return mod.create_reflection_line(basis, operator.line.direction)
    elif isinstance(operator, ReflectionPlane):
        alg_type = _detect(basis)
        if alg_type in ("n3", "n2", "pga3"):
            return mod.create_reflection_plane(basis, operator.plane)
        # PGA/E/P modules — use normal from plane (origin-only)
        return mod.create_reflection_plane(basis, operator.plane.normal)
    elif isinstance(operator, ReflectionPoint):
        alg_type = _detect(basis)
        if alg_type not in ("n3", "n2", "pga3", "pga2", "p3", "p2"):
            raise TypeError(
                f"ReflectionPoint operator requires conformal model (N3/N2); "
                f"not supported in {alg_type.upper()}."
            )
        return mod.create_reflection_point(basis, operator.point)
    elif isinstance(operator, HDirection):
        alg_type = _detect(basis)
        if alg_type not in ("n3", "n2"):
            raise TypeError(
                f"HDirection (as operator) requires conformal model (N3/N2); "
                f"not supported in {alg_type.upper()}."
            )
        return mod.create_homogeneous_direction(
            basis, operator.direction.x, operator.direction.y, operator.direction.z
        )
    elif isinstance(operator, Inversion):
        return mod.create_inversion(basis, operator.center, operator.radius)
    elif isinstance(operator, Rotor):
        return mod.create_rotor(basis, operator.angle, operator.axis)
    elif isinstance(operator, Translator):
        return mod.create_translator(
            basis, operator.vector.x, operator.vector.y, operator.vector.z
        )
    elif isinstance(operator, Dilator):
        alg_type = _detect(basis)
        if alg_type in ("n3", "n2"):
            return mod.create_dilator(basis, operator.factor, origin=operator.origin)
        return mod.create_dilator(basis, operator.factor)
    elif isinstance(operator, Motor):
        return mod.create_motor(basis, operator.rotor, operator.translator)
    elif isinstance(operator, GeneralRotor):
        return mod.create_general_rotor(
            basis, operator.angle, operator.axis, operator.origin
        )
    else:
        raise TypeError(
            f"Operator type {type(operator).__name__} not supported in {_detect(basis)}"
        )


# ═══════════════════════════════════════════════════════════════
# Convenience wrapper
# ═══════════════════════════════════════════════════════════════


def create(basis: Algebra, obj: Entity | Operator) -> MV:
    """Create an MV from an entity or operator dataclass.

    Parameters
    ----------
    basis : Algebra
        An algebra instance.  Its ``opns`` flag determines whether an
        entity is created in OPNS or IPNS.
    obj : Entity or Operator
        A geometric entity or operator dataclass.

    Returns
    -------
    MV
        The multivector representation.
    """
    # Quadric-space viz entities (Ellipse/Ellipsoid/Cylinder) become MV-backed
    # in the quadric space even though they stay out of the generic Entity
    # union (they remain viz-only for the other algebras).
    if isinstance(obj, (Ellipse, Ellipsoid, Cylinder)):
        alg_type = _detect(basis)
        if alg_type in ("q2", "q3"):
            from . import create_q2, create_q3

            mod = create_q2 if alg_type == "q2" else create_q3
            return mod.create_entity(basis, obj)

    if isinstance(obj, Entity):
        return create_entity(basis, obj)
    elif isinstance(obj, Operator):
        return create_operator(basis, obj)
    else:
        raise TypeError(f"Expected Entity or Operator, got {type(obj).__name__}")
