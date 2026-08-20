# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Blade-mask derivation for entities and operators.

Turns a geometric :class:`~pytanga.geometry.entities.Entity` or
:class:`~pytanga.geometry.operators.Operator` type into the
:class:`~pytanga.BladeMask` of the blades that type occupies in a given
algebra.

The mask is derived by constructing a generic instance of the type and
delegating to :func:`~pytanga.geometry.create.create`.  This keeps
``create`` as the single source of truth: the OPNS/IPNS interpretation, the
per-algebra support matrix, and the "raise on unsupported type" behaviour
all come along for free.  The generic instance uses well-chosen values so
that every blade the type can ever occupy is non-zero and therefore
captured by :meth:`BladeMask.from_mv`.

``mask_for`` accepts either a **class** (full type blade mask) or an
**instance** (mask of that instance's non-zero blades).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pytanga.blade_mask import BladeMask
from pytanga.expression import Variable

from .create import create as _create
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
    VersorFactors,
)

if TYPE_CHECKING:
    from pytanga.algebra._algebra import Algebra


def _template(typ: type) -> object:
    """Return a generic instance of *typ* spanning all blades of that type.

    Values are chosen so that ``create(algebra, instance)`` produces every
    blade that the type can ever occupy (guarded by tests).  Types without a
    concrete ``create`` implementation raise ``TypeError``.
    """
    if issubclass(typ, ImagPointPair):
        raise TypeError("ImagPointPair has no concrete MV and no blade mask yet.")
    if issubclass(typ, PointPair):
        return PointPair(Point(1, 2, 3), Point(4, 5, 7))
    if issubclass(typ, ImagCircle):
        raise TypeError("ImagCircle has no concrete MV and no blade mask yet.")
    if issubclass(typ, Circle):
        return Circle(Point(1, 2, 3), 2.0, Direction(4, 5, 6))
    if issubclass(typ, ImagSphere):
        raise TypeError("ImagSphere has no concrete MV and no blade mask yet.")
    if issubclass(typ, Sphere):
        return Sphere(Point(1, 2, 3), 2.0)
    if issubclass(typ, Point):
        return Point(1, 2, 3)
    if issubclass(typ, Direction):
        return Direction(1, 2, 3)
    if issubclass(typ, HPoint):
        return HPoint(Point(1, 2, 3), 2.0)
    if issubclass(typ, HDirection):
        return HDirection(Direction(1, 2, 3))
    if issubclass(typ, Line):
        return Line(Point(1, 2, 3), Direction(4, 5, 6))
    if issubclass(typ, Plane):
        return Plane(Point(1, 2, 3), Direction(4, 5, 6))
    if issubclass(typ, Space):
        return Space()
    if issubclass(typ, Rotor):
        return Rotor(0.7, Direction(1, 2, 3))
    if issubclass(typ, Translator):
        return Translator(Direction(4, 5, 6))
    if issubclass(typ, Dilator):
        return Dilator(1.7, Point(1, 2, 3))
    if issubclass(typ, Inversion):
        return Inversion(Point(1, 2, 3), 2.0)
    if issubclass(typ, Motor):
        return Motor(Rotor(0.7, Direction(1, 2, 3)), Translator(Direction(4, 5, 6)))
    if issubclass(typ, GeneralRotor):
        return GeneralRotor(0.7, Direction(1, 2, 3), Point(1, 2, 3))
    if issubclass(typ, ReflectionLine):
        return ReflectionLine(Line(Point(1, 2, 3), Direction(4, 5, 6)))
    if issubclass(typ, ReflectionPlane):
        return ReflectionPlane(Plane(Point(1, 2, 3), Direction(4, 5, 6)))
    if issubclass(typ, ReflectionPoint):
        return ReflectionPoint(Point(1, 2, 3))
    if issubclass(typ, (TripleReflection, VersorFactors)):
        raise TypeError(
            f"{typ.__name__} has no fixed blade mask; it is an analysis container."
        )
    raise TypeError(f"Unsupported type for mask derivation: {typ.__name__}")


def mask_for(basis: Algebra, typ) -> BladeMask:
    """Return the :class:`BladeMask` a type or instance occupies in *basis*.

    Parameters
    ----------
    basis : Algebra
        The algebra instance.  Its ``opns`` flag determines the entity's
        OPNS/IPNS representation (operators are unaffected).
    typ : type or Entity/Operator instance
        A geometric type (e.g. :class:`Rotor`, :class:`Point`), or an
        instance thereof.  A class yields the full type blade set; an
        instance yields the mask of that instance's non-zero blades.
    """
    if isinstance(typ, type):
        cls = typ
        inst = _template(cls)
    else:
        inst = typ
    mv = _create(basis, inst)
    return BladeMask(mv)


def create_var(basis: Algebra, name: str, typ) -> Variable:
    """Create a :class:`Variable` whose mask matches *typ* in *basis*.

    ``create_var(alg, "R1", Rotor)`` is equivalent to
    ``Variable("R1", mask_for(alg, Rotor))``.
    """
    return Variable(name, mask_for(basis, typ))
