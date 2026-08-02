# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
"""pytanga.solver — equation-solving machinery for geometric algebra.

Each submodule provides free functions that take an :class:`~pytanga.algebra.Algebra`
as their first argument.  Import from the specific file you need:

.. code-block:: python

    from pytanga.solver.solve import solve, solve_lsq, solve_mod
    from pytanga.solver.product_matrix import product_matrix
    from pytanga.solver.blade_masks import inverse_blade_mask
    from pytanga.solver.matrix_convert import to_matrix, from_matrix

"""
