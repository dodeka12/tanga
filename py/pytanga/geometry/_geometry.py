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

from .analysis import analyze as _analyze
from .analysis import analyze_entity, analyze_operator
from .create import create

if TYPE_CHECKING:
    from pytanga.algebra._algebra import Algebra
    from pytanga.algebra._mv import MV

    from .entities import Entity
    from .operators import Operator


class Geometry:
    """High-level geometry facade bound to a single algebra.

    Parameters
    ----------
    algebra : Algebra
        The algebra instance (e.g. ``BasisN3()``).
        Stored immutably; access via the :attr:`algebra` property.
    """

    __slots__ = ("_algebra",)

    def __init__(self, algebra: Algebra) -> None:
        self._algebra = algebra

    # ── read-only algebra ──────────────────────────────────────

    @property
    def algebra(self) -> Algebra:
        """The algebra this ``Geometry`` instance is bound to (read-only)."""
        return self._algebra

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

    def __call__(self, obj: Entity | Operator) -> MV:
        """Create an MV from *obj* (alias for :meth:`create`)."""
        return self.create(obj)

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
