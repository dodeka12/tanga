#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

r"""tensor_named_basis.py — get_tensor() (raw MVTensor) + get_array() (named bases).

Demonstrates the two-stage tensor access on a TwistBivector variable:
``Expression.get_tensor()`` returns the raw ``MVTensor`` (one raw ``BladeMask``
per dimension), and ``MVTensor.get_array()`` recombines each axis into its named
basis.  The twist mask has 9 raw blades but a 6-direction physical basis
(3 rotations + 3 translations), so the same tensor collapses to (9×9), (9×6),
(6×6) or (3×3) depending on which bases are chosen.

Run with:  uv run python py/examples/ga/expression/tensor_named_basis.py

Keywords: expressions, get_tensor, get_array, TwistBivector, BladeMask, N3, basis
"""

import numpy as np
from typing import cast

from pytanga import BladeMask, Variable
from pytanga.basis import BasisN3
from pytanga.geometry import Geometry, TwistBivector


def main() -> None:
    alg = BasisN3()
    geo = Geometry(alg)
    twist_mask = geo.mask_for(TwistBivector)

    # The 6 physical DOF of a twist: 3 rotations + 3 translations.
    rot_only = [alg.e12, alg.e13, alg.e23]

    x = Variable("X", twist_mask)
    expr = x * 1.0  # identity operator on the twist subspace

    # 1. Raw tensor — an MVTensor with one raw BladeMask per dimension.
    t = expr.get_tensor()
    out_mask = cast(BladeMask, t.masks[0])
    var_mask = cast(BladeMask, t.masks[1])
    print("get_tensor() — raw MVTensor:")
    print("  shape:             ", t.shape)  # (9, 9)
    print("  output mask basis:  ", out_mask.basis_names)
    print("  variable mask basis:", var_mask.basis_names)

    # 2. Default recombination: output in its display basis (9), variable in the
    #    6 physical DOF directions.
    a = t.get_array()
    print("\nget_array() — defaults (out display basis × 6 DOF):", a.shape)

    # 3. Output also in the 6 physical DOF -> square 6×6 operator matrix.
    six = t.get_array(out_basis=twist_mask.basis_vectors)
    print("\nget_array(out_basis=twist) — 6×6:", six.shape)
    print(np.round(six, 6))  # identity: each physical DOF maps to itself

    # 4. Restrict both axes to the 3 rotation DOF -> 3×3 rotation block.
    three = t.get_array(out_basis=rot_only, axis_bases={1: rot_only})
    print("\nget_array(out_basis=rot, axis_bases={1: rot}) — 3×3:", three.shape)
    print(np.round(three, 6))


if __name__ == "__main__":
    main()

