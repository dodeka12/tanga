# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Geometry convenience class — high-level facade bound to a single algebra.

The :class:`Geometry` class wraps an algebra instance and provides
``create()``, ``which_entity()``, and ``which_operator()`` methods that
delegate to the existing dispatchers, always using the stored algebra.
A default ``opns`` flag can be set on the instance and overridden per call.
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
    opns : bool, optional
        Default OPNS/IPNS flag for :meth:`create` and :meth:`which_entity`.
        Can be overridden per call.  Defaults to *True*.
    """

    __slots__ = ("_algebra", "opns")

    def __init__(self, algebra: Algebra, *, opns: bool = True) -> None:
        self._algebra = algebra
        self.opns: bool = opns

    # ── read-only algebra ──────────────────────────────────────

    @property
    def algebra(self) -> Algebra:
        """The algebra this ``Geometry`` instance is bound to (read-only)."""
        return self._algebra

    # ── convenience methods ────────────────────────────────────

    def create(self, obj: Entity | Operator, *, opns: bool | None = None) -> MV:
        """Create an MV from an entity or operator.

        Parameters
        ----------
        obj : Entity or Operator
            A geometric entity or operator dataclass.
        opns : bool or None, optional
            *True* → create in OPNS, *False* → create in IPNS.
            If *None* (default), uses ``self.opns``.

        Returns
        -------
        MV
            The multivector representation.
        """
        return create(self._algebra, obj, opns=self._opns(opns))

    def which_entity(self, mv: MV, *, opns: bool | None = None) -> Entity:
        """Determine which geometric entity an MV represents.

        Parameters
        ----------
        mv : MV
            A multivector to analyze.
        opns : bool or None, optional
            *True* → interpret blade in OPNS, *False* → in IPNS.
            If *None* (default), uses ``self.opns``.

        Returns
        -------
        Entity
            The :class:`~.entities.Entity` dataclass.
        """
        return analyze_entity(mv, opns=self._opns(opns))

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

    def analyze(self, mv: MV, *, opns: bool | None = None) -> Entity | Operator | None:
        """Try to analyze an MV as either an entity or an operator.

        Tries entity analysis first, then operator analysis.
        Returns the first successful match.

        Parameters
        ----------
        mv : MV
            A multivector to analyze.
        opns : bool or None, optional
            *True* → OPNS, *False* → IPNS. Only passed to entity analysis;
            operators are unaffected.  If *None* (default), uses ``self.opns``.

        Returns
        -------
        Entity, Operator, or None
        """
        return _analyze(mv, opns=self._opns(opns))

    # ── helpers ────────────────────────────────────────────────

    def _opns(self, override: bool | None) -> bool:
        """Resolve effective opns: *override* if given, else ``self.opns``."""
        return self.opns if override is None else override
