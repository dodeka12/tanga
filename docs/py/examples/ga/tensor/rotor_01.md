# Product tensor basics — compute the geometric product *via* tensor contraction

**Keywords:** tensor · product tensor · rotor · einsum · E3

This example shows how to

1. build a full-algebra product tensor for GP in E3,
2. contract it with two random multivectors via `numpy.einsum`,
3. compare the result against the standard `A * B` operand.

## Run

```bash
uv run python py/examples/ga/tensor/rotor_01.py
```

## Source

[`ga/tensor/rotor_01.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/ga/tensor/rotor_01.py)

## Code

````python
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

    uv run python py/examples/ga/tensor/rotor_01.py

Keywords: tensor, product tensor, rotor, einsum, E3
"""

import numpy as np
import pytanga as pt
from pytanga.algebra import EInv, to_rotor
from pytanga.geometry import RndMV
from pytanga.tensor.convert import from_tensor, to_tensor
from pytanga.tensor.ops import contract
from pytanga.tensor.product import product_tensor


def main() -> None:
    # --- 1. create algebra -----------------------------------------------------
    alg = pt.Algebra(3, 0, "float64")
    print(f"Algebra dimension: {alg.algebra_dim}  blades")

    # --- 2. generate two random multivectors with random masks -----------------
    rng = np.random.default_rng(2025)

    # Rotor mask in G3
    rot_mask = pt.BladeMask(alg, "1 + e12 + e13 + e23")

    # Point mask in G3
    point_mask = pt.BladeMask(alg, "e1 + e2 + e3")

    # The product tensor for R * P, where R is a rotor and P is a point.
    G_RP = product_tensor(rot_mask, point_mask, product=pt.EProduct.GP)
    # The tensor shape is (8, 4, 4) because the rotor has 4 blades and the point has 4 blades.
    print(
        f"  shape = {G_RP.shape}   "
        f"(|c_mask|={len(G_RP.masks[0])}, |a_mask|={len(G_RP.masks[1])}, "
        f"|b_mask|={len(G_RP.masks[2])})"
    )
    # We now create the product tensor for R * P * ~R.
    # The mask of the left element is the result mask of the previous product tensor,
    # and the mask of the right element is the rotor mask.
    # We also need to set the right involution to be the reverse, because we want to compute R * P * ~R.
    # The result mask is the point mask, because we want to compute R * P * ~R,
    # which is a point.
    G_rpR = product_tensor(
        G_RP.masks[0],
        rot_mask,
        c_mask=point_mask,
        product=pt.EProduct.GP,
        b_inv=EInv.REV,
    )
    print(
        f"  shape = {G_rpR.shape}   "
        f"(|c_mask|={len(G_rpR.masks[0])}, |a_mask|={len(G_rpR.masks[1])}, "
        f"|b_mask|={len(G_rpR.masks[2])})"
    )

    # Let's now contract the two product tensors with one another.
    # Inidices i and l are the indices for the rotor and j is the index for the point.
    G_RPR = contract("kij,mkl->mijl", G_RP, G_rpR)
    print(
        f"  shape = {G_RPR.shape}   "
        f"(|c_mask|={len(G_RPR.masks[0])}, |a_mask|={len(G_RPR.masks[1])}, "
        f"|b_mask|={len(G_RPR.masks[2])}, |d_mask|={len(G_RPR.masks[3])})"
    )

    # Create a random rotor and a random point.
    angle = rng.uniform(0, 2 * np.pi)
    rotor = to_rotor(angle, bivec=alg("e1+e2+e3").complement())
    print(f"\n  Angle: {angle:.4f} rad")
    print(f"\n  Rotor: {rotor!s}")

    point = RndMV(point_mask, [(-1.0, 1.0)] * len(point_mask))(rng)

    rot_t = to_tensor(rotor, mask=rot_mask)
    point_t = to_tensor(point, mask=point_mask)

    # If we contract G_RPR with just the rotor, we obtain a rotation matrix for points.
    G_rot = contract("mijl,i,l->mj", G_RPR, rot_t, rot_t)
    print(
        f"  shape = {G_rot.shape}   "
        f"(|c_mask|={len(G_rot.masks[0])}, |a_mask|={len(G_rot.masks[1])}, "
    )

    # Now we can contract the rotation matrix with the point to obtain the rotated point.
    rotated_point_t = contract("mj,j->m", G_rot, point_t)
    rotated_point = from_tensor(rotated_point_t)
    print(f"\n  Original point: {point!s}")
    print(f"  Rotated point:  {rotated_point!s}")


if __name__ == "__main__":
    main()
````
