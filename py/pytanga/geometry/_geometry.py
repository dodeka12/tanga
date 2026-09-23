# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Geometry convenience class — high-level facade bound to a single algebra.

The :class:`Geometry` class wraps an algebra instance and provides
``create()``, ``which_entity()``, and ``which_operator()`` methods that
delegate to the existing dispatchers, always using the stored algebra.
The OPNS/IPNS interpretation is read from ``geometry.algebra.opns``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, overload

import numpy as np

from pytanga.blade_mask import BladeMask
from pytanga.expression import Variable

from .analysis import analyze as _analyze
from .analysis import analyze_entity, analyze_operator
from .create import create
from .entities import Conic, Entity, Quadric3D, _is_mv
from .operators import Operator, Translator
from .random import RndEntity
from .refine import refine

if TYPE_CHECKING:
    from pytanga.algebra._algebra import Algebra
    from pytanga.algebra._mv import MV
    from pytanga.expression import Expression


class Geometry:
    """High-level geometry facade bound to a single algebra.

    Parameters
    ----------
    algebra : Algebra
        The algebra instance (e.g. ``BasisN3()``).
        Stored immutably; access via the :attr:`algebra` property.
    seed : int | None
        Optional seed for this instance's random number generator (used by
        the random entity generators passed to :meth:`__call__`).
    """

    __slots__ = ("_algebra", "_rng", "_tol")

    def __init__(
        self,
        algebra: Algebra,
        *,
        seed: int | None = None,
        tol: float | None = None,
    ) -> None:
        self._algebra = algebra
        self._rng = np.random.default_rng(seed)
        self._tol = tol

    # ── read-only algebra ──────────────────────────────────────

    @property
    def algebra(self) -> Algebra:
        """The algebra this ``Geometry`` instance is bound to (read-only)."""
        return self._algebra

    @property
    def rng(self) -> np.random.Generator:
        """NumPy random number generator owned by this :class:`Geometry`.

        Seedable at construction time via ``Geometry(algebra, seed=...)`` and
        forwarded to random entity generators so results are reproducible.
        """
        return self._rng

    @property
    def tol(self) -> float | None:
        """Tolerance used for conic/quadric refinement (``None`` = algebra default)."""
        return self._tol

    @tol.setter
    def tol(self, value: float | None) -> None:
        self._tol = value

    # ── convenience methods ────────────────────────────────────

    @overload
    def create(self, obj: Translator) -> MV | Expression: ...
    @overload
    def create(self, obj: Entity | Operator) -> MV: ...
    def create(self, obj: Entity | Operator) -> MV | Expression:
        """Create an MV (or a linear-map expression) from an entity or operator.

        The OPNS/IPNS interpretation is read from ``self.algebra.opns``.  A
        ``Translator`` in the quadric spaces (Q2/Q3) has no versor and returns a
        linear-map :class:`~pytanga.expression.Expression` instead.

        Parameters
        ----------
        obj : Entity or Operator
            A geometric entity or operator dataclass.

        Returns
        -------
        MV or Expression
            The multivector representation, or a linear-map expression for a
            quadric-space translator.
        """
        return create(self._algebra, obj)

    @overload
    def __call__(self, obj: "Conic | Quadric3D") -> Any: ...
    @overload
    def __call__(self, obj: Translator) -> MV | Expression: ...
    @overload
    def __call__(self, obj: "Entity | Operator") -> MV: ...
    @overload
    def __call__(self, obj: MV) -> "Entity | Operator | None": ...
    @overload
    def __call__(self, obj: str, typ: type[object]) -> Variable: ...
    @overload
    def __call__(self, obj: "list[Any] | tuple[Any, ...]") -> "list[Any]": ...
    @overload
    def __call__(self, obj: "RndEntity") -> "MV | list[Any]": ...
    @overload
    def __call__(self, obj: Any, typ: type[object] | None = None) -> Any: ...
    def __call__(self, obj: object, typ: type | None = None) -> object:
        """Create MVs, create variables, or analyze MVs.

        Dispatch rules, in order:

        - ``geo(name, type)`` → :meth:`create_var` (e.g. ``geo("R1", Rotor)``).
        - :class:`~.random.RndEntity` (e.g. ``RndPoint``) → materialize with this
          instance's ``rng`` and create the resulting entity or list of entities.
        - ``list`` / ``tuple`` → recurse over each element (e.g. a list of
          ``RndPoint`` instances, or plain entities).
        - :class:`Entity` / :class:`Operator` → :meth:`create`.
        - :class:`MV` → :meth:`analyze`.
        - object with an ``entity`` attribute (e.g. a viz ``ActPoint``) → recurse
          on ``obj.entity``.
        """
        if isinstance(obj, str) and typ is not None:
            return self.create_var(obj, typ)
        if isinstance(obj, RndEntity):
            result = obj(self._rng)
            if _is_mv(result):
                return result
            if isinstance(result, (list, tuple)):
                return [item if _is_mv(item) else self.create(item) for item in result]
            return self.create(result)
        if isinstance(obj, (list, tuple)):
            return [self(item) for item in obj]
        if isinstance(obj, (Conic, Quadric3D)):
            return self.refine(obj)
        if isinstance(obj, (Entity, Operator)):
            return self.create(obj)
        if _is_mv(obj):
            return self.analyze(obj)
        entity = getattr(obj, "entity", None)
        if entity is not None:
            return self(entity)
        raise TypeError(
            f"Geometry.__call__() expects RndEntity, Entity, Operator, list, MV, "
            f"(name, type) tuple, or an object with an `entity` attribute, "
            f"got {type(obj).__name__}"
        )

    def which_entity(self, mv: MV) -> Entity | None:
        """Determine which geometric entity an MV represents.

        Parameters
        ----------
        mv : MV
            A multivector to analyze.  The MV's ``algebra.opns`` flag
            determines the OPNS/IPNS interpretation.

        Returns
        -------
        Entity
            The :class:`~.entities.Entity` dataclass.
        """
        return analyze_entity(mv)

    def which_operator(
        self,
        mv: MV,
        *,
        expect: type[Operator] | tuple[type[Operator], ...] | None = None,
    ) -> Operator | None:
        """Determine which versor / operator an MV represents.

        Parameters
        ----------
        mv : MV
            A multivector to analyze.
        expect : type[Operator] | tuple[type[Operator], ...] | None, optional
            An optional expected operator type, forwarded to
            :func:`~pytanga.geometry.analysis.analyze_operator` (see its
            docstring).

        Returns
        -------
        Operator
            The :class:`~.operators.Operator` dataclass.

        Notes
        -----
        Operators (versors) are independent of the OPNS/IPNS flag;
        this method does not accept an *opns* argument.
        """
        return analyze_operator(mv, expect=expect)

    def analyze(
        self,
        mv: MV,
        *,
        expect: type[Operator] | tuple[type[Operator], ...] | None = None,
    ) -> Entity | Operator | None:
        """Try to analyze an MV as either an entity or an operator.

        Tries entity analysis first, then operator analysis.
        Returns the first successful match.

        Parameters
        ----------
        mv : MV
            A multivector to analyze.  The MV's ``algebra.opns`` flag
            determines the OPNS/IPNS interpretation for entity analysis;
            operators are unaffected.
        expect : type[Operator] | tuple[type[Operator], ...] | None, optional
            An optional expected operator type, forwarded to the operator
            fallback (see :func:`~pytanga.geometry.analysis.analyze_operator`).

        Returns
        -------
        Entity, Operator, or None
        """
        return _analyze(mv, expect=expect)

    def refine(self, entity: object, *, tol: float | None = None) -> object:
        """Refine a raw :class:`Conic` / :class:`Quadric3D` into a specific entity.

        The second analysis level: ``geo(analyze(mv))`` yields the raw
        ``Conic``/``Quadric3D``, and ``geo(that)`` refines it (e.g. to a
        ``Circle``, ``Ellipsoid``, …).  *tol* (defaults to :attr:`tol`, which
        itself defaults to the algebra's ``precision``) is forwarded to the
        conic/quadric classification so a noisy quadric can be classified within
        a tolerance.
        """
        effective = self._tol if tol is None else tol
        if effective is None:
            effective = self._algebra.precision
        return refine(entity, tol=effective)

    # ── variable / blade-mask helpers ──────────────────────────

    def mask_for(self, typ: "type[object] | Entity | Operator") -> BladeMask:
        """Return the :class:`BladeMask` a type or instance occupies in this algebra.

        A class (e.g. ``Rotor``) yields the full type blade set; an instance
        yields the mask of that instance's non-zero blades.  Entities respect
        ``self.algebra.opns``; operators are unaffected.
        """
        from .mask import mask_for

        return mask_for(self._algebra, typ)

    def create_var(
        self, name: str, typ: "type[object] | Entity | Operator"
    ) -> Variable:
        """Create a :class:`~pytanga.Variable` whose mask matches *typ*.

        ``geo.create_var("R1", Rotor)`` creates a variable that may hold any
        rotor of ``self.algebra``.
        """
        return Variable(name, self.mask_for(typ))
