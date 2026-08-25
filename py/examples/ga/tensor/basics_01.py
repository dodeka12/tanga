#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
r"""Product tensor basics — compute the geometric product *via* tensor contraction.

This example shows how to

1. build a full-algebra product tensor for GP in E3,
2. contract it with two random multivectors via :func:`numpy.einsum`,
3. compare the result against the standard ``A * B`` operand.

Run
----

.. code-block:: bash

    uv run python py/examples/ga/tensor/basics_01.py
"""

import numpy as np
import pytanga as pt
from pytanga.algebra import random_mv
from pytanga.tensor.convert import from_tensor, to_tensor
from pytanga.tensor.ops import contract
from pytanga.tensor.product import product_tensor


def main() -> None:
    # --- 1. create algebra -----------------------------------------------------
    alg = pt.Algebra(3, 0, "float64")
    print(f"Algebra dimension: {alg.algebra_dim}  blades")

    # --- 2. generate two random multivectors with random masks -----------------
    rng = np.random.default_rng(2025)
    A = random_mv(alg, low=-1, high=1, rng=rng)
    B = random_mv(alg, low=-1, high=1, rng=rng)

    a_mask = pt.BladeMask(A)
    b_mask = pt.BladeMask(B)
    print(f"\n  A  ({len(a_mask)} blades) = {A!s}")
    print(f"  B  ({len(b_mask)} blades) = {B!s}")

    # --- 3. build the GP product tensor for their masks ------------------------
    # c_mask is auto-computed from mask_a and mask_b
    # The algebra is obtained from the blade masks — no need to pass it explicitly.
    print("\n--- Building GP product tensor ---")
    GP = product_tensor(a_mask, b_mask, product=pt.EProduct.GP)
    print(
        f"  shape = {GP.shape}   "
        f"(|c_mask|={len(GP.masks[0])}, |a_mask|={len(GP.masks[1])}, "
        f"|b_mask|={len(GP.masks[2])})"
    )
    print(f"  entry range: {GP.data.min():.0f} … {GP.data.max():.0f}")

    # --- 4. extract coefficient vectors ordered by the tensor masks ------------
    # to_matrix() returns an MVMatrix; .data is a (len(mask), 1) column.
    # The einsum subscript "kij,in,jn->kn" is therefore used to contract
    # the tensor with the column vectors and result in a column vector.
    a_t = to_tensor(A, mask=a_mask)
    b_t = to_tensor(B, mask=b_mask)
    print(f"\n  MVTensor shapes: a_t.shape={a_t.shape}, b_t.shape={b_t.shape}")

    # --- 5. compute C = A * B via tensor contraction ---------------------------
    c_t = contract("kij,i,j->k", GP, a_t, b_t)
    print(f"  C_tensor = {c_t!s}")

    C_from_tensor = from_tensor(c_t)
    print(f"\n  C_from_tensor ({len(GP.masks[0])} blades) = {C_from_tensor!s}")

    C = A * B
    print(f"  C = A * B ({len(pt.BladeMask(C))} blades) = {C!s}")


if __name__ == "__main__":
    main()
