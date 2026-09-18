# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Blade-mask lookup for entities and operators.

Maps a geometric :class:`~pytanga.geometry.entities.Entity` or
:class:`~pytanga.geometry.operators.Operator` type to the
:class:`~pytanga.BladeMask` of the blades that type occupies in a given algebra.

Each ``create_*`` module hard-codes the full type mask via
``mask_for_<key>(basis)`` functions, so masks are deterministic and never depend
on a sample instance.

``mask_for`` accepts either a **class** (the hard-coded full type mask) or an
**instance** (the non-zero blades of that instance's MV).
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING, cast

from pytanga.blade_mask import BladeMask
from pytanga.expression import Variable

from .create import create as _create

if TYPE_CHECKING:
    from pytanga.algebra._algebra import Algebra

    from .entities import Entity
    from .operators import Operator


def _create_module(alg_type: str) -> Any:
    """Return the per-algebra ``create_*`` module for an algebra type key."""
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

    return {
        "e2": create_e2,
        "e3": create_e3,
        "n2": create_n2,
        "n3": create_n3,
        "p2": create_p2,
        "p3": create_p3,
        "pga2": create_pga2,
        "pga3": create_pga3,
    }[alg_type]


def _basis_type_key(typ: "type[object]") -> "str | None":
    """Return the canonical type key used to find ``mask_for_<key>``."""
    from .entities import (
        Circle,
        Direction,
        HDirection,
        HPoint,
        ImagCircle,
        ImagPointPair,
        ImagSphere,
        Line,
        Plane,
        Point,
        PointPair,
        Space,
        Sphere,
    )
    from .operators import (
        Dilator,
        GeneralRotor,
        Inversion,
        Motor,
        ReflectionLine,
        ReflectionPlane,
        ReflectionPoint,
        Rotor,
        Translator,
        TripleReflection,
        TwistBivector,
        VersorFactors,
    )

    if issubclass(
        typ, (ImagCircle, ImagPointPair, ImagSphere, TripleReflection, VersorFactors)
    ):
        return None
    if issubclass(typ, TwistBivector):
        return "twist_bivector"
    if issubclass(typ, GeneralRotor):
        return "general_rotor"
    if issubclass(typ, ReflectionLine):
        return "reflection_line"
    if issubclass(typ, ReflectionPlane):
        return "reflection_plane"
    if issubclass(typ, ReflectionPoint):
        return "reflection_point"
    if issubclass(typ, Inversion):
        return "inversion"
    if issubclass(typ, Motor):
        return "motor"
    if issubclass(typ, Rotor):
        return "rotor"
    if issubclass(typ, Translator):
        return "translator"
    if issubclass(typ, Dilator):
        return "dilator"
    if issubclass(typ, HDirection):
        return "homogeneous_direction"
    if issubclass(typ, HPoint):
        return "homogeneous_point"
    if issubclass(typ, PointPair):
        return "point_pair"
    if issubclass(typ, Circle):
        return "circle"
    if issubclass(typ, Sphere):
        return "sphere"
    if issubclass(typ, Line):
        return "line"
    if issubclass(typ, Plane):
        return "plane"
    if issubclass(typ, Point):
        return "point"
    if issubclass(typ, Direction):
        return "direction"
    if issubclass(typ, Space):
        return "space"
    return None


def mask_for(basis: Algebra, typ: "type[object] | Entity | Operator") -> BladeMask:
    """Return the :class:`BladeMask` a type or instance occupies in *basis*.

    - **class** → the hard-coded full type mask from the per-algebra
      ``create_*.mask_for_<key>(basis)`` function.
    - **instance** → the non-zero blades of that instance's MV.

    The ``opns`` flag on *basis* determines the OPNS/IPNS representation for
    entities (operators are unaffected).
    """
    from .create import _detect

    if isinstance(typ, type):
        alg_type = _detect(basis)
        if alg_type in ("q2", "q3"):
            raise TypeError(f"mask_for does not support quadric entities ({alg_type})")
        mod = _create_module(alg_type)
        key = _basis_type_key(typ)
        if key is None:
            raise TypeError(f"Unsupported type for mask derivation: {typ.__name__}")
        fn = getattr(mod, f"mask_for_{key}", None)
        if fn is None:
            raise TypeError(f"{typ.__name__} is not supported in {alg_type.upper()}")
        return cast("BladeMask", fn(basis))
    return BladeMask(_create(basis, typ))


def create_var(
    basis: Algebra, name: str, typ: "type[object] | Entity | Operator"
) -> Variable:
    """Create a :class:`Variable` whose mask matches *typ* in *basis*.

    ``create_var(alg, "R1", Rotor)`` is equivalent to
    ``Variable("R1", mask_for(alg, Rotor))``.
    """
    return Variable(name, mask_for(basis, typ))
