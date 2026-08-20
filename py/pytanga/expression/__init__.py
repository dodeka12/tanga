# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""pytanga.expression — symbolic variables and expressions over the tensor stack.

A :class:`Variable` is a named slot with a fixed :class:`~pytanga.BladeMask`.
Combining variables with constant multivectors (and with each other) builds an
:class:`Expression` — a reduced product tensor with one axis per variable and
one output axis.  Evaluate an expression by binding variables to multivectors::

    from pytanga import BladeMask, Variable
    from pytanga.basis import BasisE3

    alg = BasisE3()
    mask = BladeMask.full(alg)
    v = Variable("V1", mask)
    a = alg.multivector({"e1": 2.0})

    e = v * a
    e(V1=alg.multivector({"e1": 1.0}))  # -> e1 * (2 e1) = 2

Binding a variable to a ``list`` of multivectors returns a ``list`` of results
(nested lists for several batched variables).
"""

from ._expression import AffineExpression, Expression
from ._variable import Variable

__all__ = ["AffineExpression", "Expression", "Variable"]
