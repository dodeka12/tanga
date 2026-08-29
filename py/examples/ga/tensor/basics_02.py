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

    uv run python py/examples/ga/tensor/basics_02.py

Keywords: tensor, product tensor, geometric product, einsum, batched
"""

import numpy as np
import pytanga as pt
from pytanga.algebra import random_mask, random_mv
from pytanga.tensor.convert import from_tensor, to_tensor
from pytanga.tensor.ops import contract
from pytanga.tensor.product import product_tensor


def main() -> None:
    # --- 1. create algebra -----------------------------------------------------
    alg = pt.Algebra(3, 0, "float64")
    print(f"Algebra dimension: {alg.algebra_dim}  blades")

    # --- 2. generate two random multivectors with random masks -----------------
    rng = np.random.default_rng(2025)

    # Create a list of random masks and corresponding random multivectors for A and B
    A_mask_list = [random_mask(alg, 4) for _ in range(5)]
    B_mask_list = [random_mask(alg, 4) for _ in range(5)]

    A_list = [
        random_mv(alg, low=-1, high=1, mask=A_mask_list[i], rng=rng) for i in range(5)
    ]
    B_list = [
        random_mv(alg, low=-1, high=1, mask=B_mask_list[i], rng=rng) for i in range(5)
    ]

    # The BladeMask constructor can take a multivector or a list of blade ids
    # The union of the blade ids of each list is used to create the masks for the product tensor
    a_mask = pt.BladeMask(A_list)
    b_mask = pt.BladeMask(B_list)
    print(f"\n  A[0]  ({len(a_mask)} blades) = {A_list[0]!s}")
    print(f"  B[0]  ({len(b_mask)} blades) = {B_list[0]!s}")

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
    a_t = to_tensor(A_list, mask=a_mask)
    b_t = to_tensor(B_list, mask=b_mask)
    print(f"\n  MVTensor shapes: a_t.shape={a_t.shape}, b_t.shape={b_t.shape}")

    # --- 5. compute C = A * B via tensor contraction ---------------------------
    # Compute A * B for each pair of multivectors in the lists using the product tensor
    c_t = contract("kij,in,jn->kn", GP, a_t, b_t)
    print(
        "\nThe C_tensor has 5 columns corresponding to the 5 pairs of multivectors in A_list and B_list."
    )
    print(f">> C_tensor = {c_t!s}")

    C_from_tensor = from_tensor(c_t)
    print(
        "\nThe C_from_tensor is a list of multivectors corresponding to the contracted tensor result."
    )
    print(f">> C_from_tensor = {C_from_tensor!s}")

    C_list = [A_list[i] * B_list[i] for i in range(len(A_list))]
    C_delta = [C_from_tensor[i] - C_list[i] for i in range(len(C_list))]
    C_mag = [C_delta[i].mag for i in range(len(C_delta))]

    print(f"Sum of differences between C_from_tensor and C_list: {sum(C_mag):.2e}")


if __name__ == "__main__":
    main()
