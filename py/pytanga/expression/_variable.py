# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""The Variable class — a named slot with a fixed blade mask."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pytanga.blade_mask import BladeMask

from ._labels import allocate_block

if TYPE_CHECKING:
    from pytanga.algebra import Algebra, MV

    from ._expression import AffineExpression, Expression


class Variable:
    """A named placeholder with a fixed :class:`~pytanga.BladeMask`.

    A variable is a symbolic slot; it carries no coefficient data.  Combining
    it with constants or other variables (via ``*``, ``|``, ``^``) builds an
    :class:`~pytanga.expression.Expression`.
    """

    __slots__ = ("_name", "_mask", "_labels")

    def __init__(self, name: str, mask: BladeMask) -> None:
        if not isinstance(mask, BladeMask):
            raise TypeError(
                f"Variable mask must be a BladeMask, got {type(mask).__name__}"
            )
        self._name = str(name)
        self._mask = mask
        self._labels = allocate_block()

    @property
    def name(self) -> str:
        """The variable's name (used as a keyword when evaluating)."""
        return self._name

    @property
    def mask(self) -> BladeMask:
        """The blade subspace this variable is allowed to hold."""
        return self._mask

    @property
    def algebra(self) -> "Algebra":
        """The algebra the variable's mask belongs to."""
        return self._mask.algebra

    @property
    def label(self) -> int:
        """The first axis label (backward-compatible; an integer from the pool)."""
        return self._labels[0]

    @property
    def labels(self) -> tuple[int, ...]:
        """The variable's label block; ``labels[k]`` is the ``k``-th occurrence."""
        return self._labels

    def __repr__(self) -> str:
        return f"Variable({self._name!r}, BladeMask({self._mask.names()}))"

    # ------------------------------------------------------------------
    # Arithmetic — each overload delegates to the expression builder.
    # ------------------------------------------------------------------

    def __mul__(
        self, other: "MV | Variable | Expression | int | float"
    ) -> "Expression":
        from pytanga.algebra import EProduct

        from ._expression import _product

        if isinstance(other, (int, float)):
            other = self.algebra.multivector({0: float(other)})
        return _product(self, other, EProduct.GP)

    def __rmul__(
        self, other: "MV | Variable | Expression | int | float"
    ) -> "Expression":
        from pytanga.algebra import EProduct

        from ._expression import _product

        if isinstance(other, (int, float)):
            other = self.algebra.multivector({0: float(other)})
        return _product(other, self, EProduct.GP)

    def __or__(self, other: "MV | Variable | Expression") -> "Expression":
        from pytanga.algebra import EProduct

        from ._expression import _product

        return _product(self, other, EProduct.IP)

    def __ror__(self, other: "MV | Variable | Expression") -> "Expression":
        from pytanga.algebra import EProduct

        from ._expression import _product

        return _product(other, self, EProduct.IP)

    def __xor__(self, other: "MV | Variable | Expression") -> "Expression":
        from pytanga.algebra import EProduct

        from ._expression import _product

        return _product(self, other, EProduct.OP)

    def __rxor__(self, other: "MV | Variable | Expression") -> "Expression":
        from pytanga.algebra import EProduct

        from ._expression import _product

        return _product(other, self, EProduct.OP)

    def __neg__(self) -> "Expression":
        return self.__rmul__(-1.0)

    def __add__(
        self, other: "MV | Variable | Expression | int | float"
    ) -> "Expression | AffineExpression":
        from ._expression import _add, _to_expression

        return _add(_to_expression(self), other)

    def __radd__(
        self, other: "MV | Variable | Expression | int | float"
    ) -> "Expression | AffineExpression":
        from ._expression import _add, _to_expression

        return _add(other, _to_expression(self))

    def __sub__(
        self, other: "MV | Variable | Expression | int | float"
    ) -> "Expression | AffineExpression":
        from ._expression import _add, _to_expression

        return _add(_to_expression(self), other, subtract=True)

    def __rsub__(
        self, other: "MV | Variable | Expression | int | float"
    ) -> "Expression | AffineExpression":
        from ._expression import _add, _to_expression

        return _add(other, _to_expression(self), subtract=True)

    def __invert__(self) -> "Expression":
        from pytanga.algebra import EInv

        from ._expression import _involution

        return _involution(self, EInv.REV)

    def conj(self) -> "Expression":
        from pytanga.algebra import EInv

        from ._expression import _involution

        return _involution(self, EInv.CONJ)
