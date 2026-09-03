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

Variables may also be bound to NumPy arrays via the ``(array, specs)`` form,
where ``specs`` is a per-axis sequence mixing a ``BladeMask`` (the blade axis)
and ``str`` names for counting axes::

    expr(x_pnt=(points, ("pnt_idx", point_mask)))

A plain ``MVTensor`` with one matching blade axis and one ``None`` axis is
equivalent to a list of multivectors::

    expr(x_pnt=MVTensor(points, masks=(None, point_mask)))

A counting axis introduced this way can then be reduced, either summed away or
multiplied element-wise and kept::

    expr(x_pnt=(points, ("pnt_idx", point_mask)))(pnt_idx=scalars)
    expr(x_pnt=(points, ("pnt_idx", point_mask)))(pnt_idx=(scalars, "pnt_idx_"))

.. note::

    The geometric-product operators ``^`` and ``|`` bind more loosely than
    ``+``/``-`` in Python, so sums/differences of products must be
    parenthesised.  ``a * (v | e3) ^ e3 + (b * (v ^ e3) | e3)`` parses as
    ``(a * (v | e3)) ^ (e3 + (b * (v ^ e3) | e3))``; write
    ``(a * (v | e3) ^ e3) + (b * (v ^ e3) | e3)`` instead.
"""

from ._data_array import DataArray
from ._expression import AffineExpression, Expression
from ._variable import Variable

__all__ = ["AffineExpression", "DataArray", "Expression", "Variable"]
