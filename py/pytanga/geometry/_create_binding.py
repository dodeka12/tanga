# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Typed protocol describing the per-algebra ``create_*`` dispatch surface.

:func:`~pytanga.geometry.create.create_entity` and
:func:`~pytanga.geometry.create.create_operator` pick one of the ten
per-algebra creation modules at runtime out of a ``dict`` keyed by the detected
algebra.  A type checker sees that ``dict`` value as a union of ten module
types, so every method call is checked against the *intersection* of those
modules and ``create_direction`` (which only exists where the algebra supports
directions) is reported as an unresolved attribute.

This protocol declares the full dispatch surface once, so the two dispatchers
can view the selected module through a single typed handle and type-check
without suppressions.  The signatures are transcribed from the
``create_*.py`` / ``pytanga.quadric._create`` modules; where the modules
disagree — e.g. ``create_reflection_line`` takes a :class:`Line` in N2/N3 but a
:class:`Direction` in the E/P/PGA modules — the protocol uses the union of the
accepted types.  ``rotor`` / ``translator`` in :meth:`CreateModule.create_motor`
are ``Any`` because the loosely typed E/P modules accept the dataclasses
without annotating them.

Not every module implements every method; the dispatchers only call a method
after verifying that the target algebra supports it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from pytanga.algebra._algebra import Algebra
    from pytanga.algebra._mv import MV

    from .entities import (
        Conic,
        Cone,
        Cylinder,
        Direction,
        Ellipse,
        Ellipsoid,
        Hyperbola,
        Line,
        LinePair,
        Parabola,
        Plane,
        PlanePair,
        Point,
        Quadric3D,
    )


class CreateModule(Protocol):
    """The full ``create_*`` surface of a per-algebra creation module."""

    # --- entities ---------------------------------------------------------
    def create_entity(
        self,
        basis: Algebra,
        entity: (
            Conic
            | Quadric3D
            | Hyperbola
            | Parabola
            | LinePair
            | PlanePair
            | Ellipse
            | Ellipsoid
            | Cylinder
            | Cone
        ),
    ) -> MV: ...

    def create_point(self, basis: Algebra, x: float, y: float, z: float) -> MV: ...

    def create_direction(self, basis: Algebra, x: float, y: float, z: float) -> MV: ...

    def create_homogeneous_point(
        self, basis: Algebra, point: Point, weight: float = 1.0
    ) -> MV: ...

    def create_homogeneous_direction(
        self, basis: Algebra, x: float, y: float, z: float
    ) -> MV: ...

    def create_point_pair(self, basis: Algebra, a: Point, b: Point) -> MV: ...

    def create_imag_point_pair(
        self,
        basis: Algebra,
        center: Point,
        direction: Direction,
        separation: float,
    ) -> MV: ...

    def create_imag_circle(
        self,
        basis: Algebra,
        center: Point,
        normal: Direction,
        radius: float,
    ) -> MV: ...

    def create_line(
        self, basis: Algebra, origin: Point, direction: Direction
    ) -> MV: ...

    def create_circle(
        self, basis: Algebra, center: Point, normal: Direction, radius: float
    ) -> MV: ...

    def create_plane(self, basis: Algebra, plane: Plane) -> MV: ...

    def create_sphere(
        self,
        basis: Algebra,
        center: Point,
        radius: float,
        is_imaginary: bool = False,
    ) -> MV: ...

    def create_space(self, basis: Algebra, *, scale: float = 1.0) -> MV: ...

    # --- operators --------------------------------------------------------
    def create_rotor(self, basis: Algebra, angle: float, axis: Direction) -> MV: ...

    def create_translator(self, basis: Algebra, x: float, y: float, z: float) -> MV: ...

    def create_dilator(
        self, basis: Algebra, factor: float, *, origin: Point | None = None
    ) -> MV: ...

    def create_motor(self, basis: Algebra, rotor: Any, translator: Any) -> MV: ...

    def create_twist_bivector(
        self, basis: Algebra, rotor: Any, translator: Any
    ) -> MV: ...

    def create_inversion(
        self, basis: Algebra, center: Point, radius: float = 1.0
    ) -> MV: ...

    def create_general_rotor(
        self, basis: Algebra, angle: float, axis: Direction, origin: Point
    ) -> MV: ...

    def create_reflection_line(
        self, basis: Algebra, line_or_direction: Line | Direction
    ) -> MV: ...

    def create_reflection_plane(
        self, basis: Algebra, plane_or_normal: Plane | Direction
    ) -> MV: ...

    def create_reflection_point(self, basis: Algebra, point: Point) -> MV: ...
