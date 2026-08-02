# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
"""pytanga.blade_mask.predict — inverse and forward blade-mask prediction."""

from __future__ import annotations

from pytanga.blade_mask import BladeMask
from pytanga.algebra import EProduct

from ._dispatch import _dispatch_product_blade_mask


def inverse_blade_mask(
    a_mask: BladeMask,
    c_mask: BladeMask,
    *,
    product: EProduct = EProduct.GP,
    left: bool = True,
) -> BladeMask:
    """Compute the maximal B-mask for A ∘ B = C from the A and C blade masks.

    Uses bitmask algebra on blade ids (which encode basis-vector sets as
    bitmaps) to compute the inverse blade mask in O(|A|·|C|) time without
    iterating over the full 2^D blade space.

    - **Geometric product**: ``E_k = ±E_i⁻¹·E_j``, and ``E_i⁻¹`` has the
      same blade id as ``E_i`` in a Euclidean metric, so every pair (i, j)
      yields a candidate ``k = i ^ j``.
    - **Outer product**: ``E_i ∧ E_k = E_j`` requires ``i ⊆ j`` (all vectors
      of ``i`` appear in ``j``); then ``k = j \\ i = j ^ i``.
    - **Inner product**: ``E_i | E_k = E_j`` requires ``i ∩ j = ∅`` (the
      removed vectors must not be in the result); then ``k = i ∪ j = i | j``.

    When *left* is False the roles of *a_mask* and *c_mask* are swapped.
    """
    assert c_mask.algebra is a_mask.algebra, (
        "c_mask belongs to a different algebra than a_mask"
    )
    alg = a_mask.algebra

    a_ids = a_mask.ids
    c_ids = c_mask.ids

    if not left:
        # X ∘ A = C  → swap roles
        a_ids, c_ids = c_ids, a_ids

    if product == EProduct.GP:
        # Every (i,j) pair is valid; k = i ^ j
        ids = sorted({i ^ j for i in a_ids for j in c_ids})
    elif product == EProduct.OP:
        # i ⊆ j required; k = j \ i = j ^ i
        ids = sorted({j ^ i for i in a_ids for j in c_ids if (i & j) == i})
    elif product == EProduct.IP:
        # i ∩ j = ∅ required; k = i ∪ j = i | j
        ids = sorted({i | j for i in a_ids for j in c_ids if (i & j) == 0})
    else:
        raise ValueError(f"Unknown product {product!r}")

    return BladeMask(alg, ids)


def product_blade_mask(
    a_mask: BladeMask,
    b_mask: BladeMask,
    *,
    product: EProduct = EProduct.GP,
    left: bool = True,
    complete: bool = False,
) -> BladeMask:
    """Predict the output blade mask (c_mask) of A ∘ B.

    All blade masks must belong to the same algebra.

    Parameters
    ----------
    a_mask : BladeMask
        Blade mask of the fixed operand A.
    b_mask : BladeMask
        Blade mask of the unknown X (B).
    product : 'gp' | 'ip' | 'op'
    left : bool
        True = A ∘ B → C; False = B ∘ A → C.
    complete : bool
        When True, iterate to the fixed-point sub-algebra closure.

    Returns
    -------
    BladeMask
        c_mask — the blade mask of the result C.
    """
    assert b_mask.algebra is a_mask.algebra, (
        "b_mask belongs to a different algebra than a_mask"
    )
    alg = a_mask.algebra
    raw_ids = _dispatch_product_blade_mask(
        alg, product, a_mask.ids, b_mask.ids, left, complete
    )
    return BladeMask(alg, raw_ids)
