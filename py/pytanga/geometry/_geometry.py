# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Geometry convenience class — high-level facade bound to a single algebra.

The :class:`Geometry` class wraps an algebra instance and provides
``create()``, ``which_entity()``, and ``which_operator()`` methods that
delegate to the existing dispatchers, always using the stored algebra.
The OPNS/IPNS interpretation is read from ``geometry.algebra.opns``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from pytanga.blade_mask import BladeMask
from pytanga.expression import Variable

from .analysis import analyze as _analyze
from .analysis import analyze_entity, analyze_operator
from .create import create
from .entities import Entity, _is_mv
from .operators import Operator
from .random import RndEntity

if TYPE_CHECKING:
    from pytanga.algebra._algebra import Algebra
    from pytanga.algebra._mv import MV


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

    __slots__ = ("_algebra", "_rng")

    def __init__(self, algebra: Algebra, *, seed: int | None = None) -> None:
        self._algebra = algebra
        self._rng = np.random.default_rng(seed)

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

    # ── convenience methods ────────────────────────────────────

    def create(self, obj: Entity | Operator) -> MV:
        """Create an MV from an entity or operator.

        The OPNS/IPNS interpretation is read from ``self.algebra.opns``.

        Parameters
        ----------
        obj : Entity or Operator
            A geometric entity or operator dataclass.

        Returns
        -------
        MV
            The multivector representation.
        """
        return create(self._algebra, obj)

    def __call__(self, obj, typ=None):
        """Create MVs, create variables, or analyze MVs.

        Dispatch rules, in order:

        - ``geo(name, type)`` → :meth:`create_var` (e.g. ``geo("R1", Rotor)``).
        - :class:`~.random.RndEntity` (e.g. ``RndPoint``) → materialize with this
          instance's ``rng`` and create the resulting entity or list of entities.
        - ``list`` / ``tuple`` → recurse over each element (e.g. a list of
          ``RndPoint`` instances, or plain entities).
        - :class:`Entity` / :class:`Operator` → :meth:`create`.
        - :class:`MV` → :meth:`analyze`.
        """
        if isinstance(obj, str) and typ is not None:
            return self.create_var(obj, typ)
        if isinstance(obj, RndEntity):
            result = obj(self._rng)
            if isinstance(result, (list, tuple)):
                return [self.create(item) for item in result]
            return self.create(result)
        if isinstance(obj, (list, tuple)):
            return [self(item) for item in obj]
        if isinstance(obj, (Entity, Operator)):
            return self.create(obj)
        if _is_mv(obj):
            return self.analyze(obj)
        raise TypeError(
            f"Geometry.__call__() expects RndEntity, Entity, Operator, list, MV, "
            f"or (name, type) tuple, got {type(obj).__name__}"
        )

    def which_entity(self, mv: MV) -> Entity:
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

    def which_operator(self, mv: MV) -> Operator:
        """Determine which versor / operator an MV represents.

        Parameters
        ----------
        mv : MV
            A multivector to analyze.

        Returns
        -------
        Operator
            The :class:`~.operators.Operator` dataclass.

        Notes
        -----
        Operators (versors) are independent of the OPNS/IPNS flag;
        this method does not accept an *opns* argument.
        """
        return analyze_operator(mv)

    def analyze(self, mv: MV) -> Entity | Operator | None:
        """Try to analyze an MV as either an entity or an operator.

        Tries entity analysis first, then operator analysis.
        Returns the first successful match.

        Parameters
        ----------
        mv : MV
            A multivector to analyze.  The MV's ``algebra.opns`` flag
            determines the OPNS/IPNS interpretation for entity analysis;
            operators are unaffected.

        Returns
        -------
        Entity, Operator, or None
        """
        return _analyze(mv)

    # ── variable / blade-mask helpers ──────────────────────────

    def mask_for(self, typ) -> BladeMask:
        """Return the :class:`BladeMask` a type or instance occupies in this algebra.

        A class (e.g. ``Rotor``) yields the full type blade set; an instance
        yields the mask of that instance's non-zero blades.  Entities respect
        ``self.algebra.opns``; operators are unaffected.
        """
        from .mask import mask_for

        return mask_for(self._algebra, typ)

    def create_var(self, name: str, typ) -> Variable:
        """Create a :class:`~pytanga.Variable` whose mask matches *typ*.

        ``geo.create_var("R1", Rotor)`` creates a variable that may hold any
        rotor of ``self.algebra``.
        """
        return Variable(name, self.mask_for(typ))
