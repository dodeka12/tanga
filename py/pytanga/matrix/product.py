# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
"""pytanga.matrix.product — build product matrices for GA equations."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from pytanga.blade_mask import BladeMask
from . import MVProductMatrix
from pytanga.algebra import EInv, EProduct

if TYPE_CHECKING:
    from pytanga.algebra import Algebra

from pytanga.algebra import MVLike, _as_mv
from ._dispatch import _dispatch_product_matrix_masked
from pytanga.blade_mask.predict import product_blade_mask


def _resolve_alg(
    a: MVLike | list[MVLike] | None = None,
    a_mask: BladeMask | None = None,
    b_mask: BladeMask | None = None,
    c_mask: BladeMask | None = None,
    algebra: "Algebra | None" = None,
) -> "Algebra":
    """Resolve the algebra from masks, MVs, or explicit kwarg."""
    from pytanga.algebra._mv import MV as _MV

    for mask in (a_mask, b_mask, c_mask):
        if mask is not None:
            return mask.algebra

    if isinstance(a, list):
        for x in a:
            if isinstance(x, _MV):
                return x.algebra
    else:
        if isinstance(a, _MV):
            return a.algebra

    if algebra is not None:
        return algebra

    raise ValueError("Cannot determine algebra — provide a mask, an MV, or algebra=")


def product_matrix(
    a: MVLike | list[MVLike],
    *,
    a_mask: BladeMask | None = None,
    b_mask: BladeMask | None = None,
    c_mask: BladeMask | None = None,
    product: EProduct = EProduct.GP,
    left: bool = True,
    left_inv: EInv = EInv.ID,
    right_inv: EInv = EInv.ID,
    algebra: "Algebra | None" = None,
) -> MVProductMatrix:
    """Build the product matrix M such that M · vec(B) = vec(C).

    Accepts either a single multivector or a list of multivectors.
    Returns a 3‑D MVProductMatrix of shape ``(|a_mask|, |c_mask|, |b_mask|)``
    where ``|a_mask| == 1`` for a single MV and ``|a_mask| == n_mvs`` for a list.

    If ``left`` is True: A ∘ B = C.
    If ``left`` is False: B ∘ A = C.

    *left_inv* / *right_inv* specify an optional involution (reverse or
    conjugate) applied to the left / right operand before contraction.

    Parameters
    ----------
    a : MVLike | list[MVLike]
        The fixed-coefficient operand(s).
    algebra : Algebra | None
        Needed only when *a* consists of bare strings or scalars and no
        mask with an algebra reference is given.
    """
    alg = _resolve_alg(a, a_mask, b_mask, c_mask, algebra=algebra)

    is_list = isinstance(a, list)
    if is_list:
        mvs = [_as_mv(alg, x) for x in a]
        if a_mask is None:
            a_mask = BladeMask.from_array(mvs)
    else:
        mv = _as_mv(alg, a)
        if a_mask is None:
            a_mask = BladeMask(mv)

    if b_mask is None:
        b_mask = BladeMask(alg)

    if c_mask is None:
        c_mask = product_blade_mask(a_mask, b_mask, product=product, left=left)

    n_mvs = len(mvs) if is_list else 1
    nc, nb = len(c_mask), len(b_mask)
    dtype = np.float64 if alg.dtype.startswith("float") else np.int64
    arr = np.zeros((n_mvs, nc, nb), dtype=dtype)

    if not is_list:
        arr[0] = _dispatch_product_matrix_masked(
            alg,
            product,
            mv._impl,
            a_mask.ids,
            b_mask.ids,
            c_mask.ids,
            left,
            left_inv=left_inv,
            right_inv=right_inv,
        )
    else:
        for i, mv_impl in enumerate(mvs):
            arr[i] = _dispatch_product_matrix_masked(
                alg,
                product,
                mv_impl._impl,
                a_mask.ids,
                b_mask.ids,
                c_mask.ids,
                left,
                left_inv=left_inv,
                right_inv=right_inv,
            )

    return MVProductMatrix(
        data=arr,
        a_mask=a_mask,
        b_mask=b_mask,
        c_mask=c_mask,
        product=product,
        left=left,
        left_inv=left_inv,
        right_inv=right_inv,
    )


def product_matrix_rev(mask: BladeMask) -> MVProductMatrix:
    """Build a diagonal product matrix encoding the reverse sign for each blade.

    The reverse of a blade of grade k introduces a sign (-1)^(k(k-1)/2):
    grades 2 and 3 mod 4 are negated.  The result is a square
    |mask| × |mask| diagonal matrix where M[i,i] = ±1.
    """
    alg = mask.algebra
    arr = alg._mod.product_matrix_rev(mask.ids)
    return MVProductMatrix(
        data=arr.reshape(1, len(mask), len(mask)),
        a_mask=mask,
        b_mask=mask,
        c_mask=mask,
        product=EProduct.GP,
        left=True,
    )


def product_matrix_conj(mask: BladeMask) -> MVProductMatrix:
    """Build a diagonal product matrix encoding the conjugate sign for each blade.

    The Clifford conjugate introduces a sign (-1)^(k(k-1)/2 + r) where k
    is the grade and r is the count of negative-metric basis vectors in
    the blade.  In a pure Euclidean algebra this reduces to the reverse.

    The result is a square |mask| × |mask| diagonal matrix where
    M[i,i] = ±1.
    """
    alg = mask.algebra
    arr = alg._mod.product_matrix_conj(mask.ids)
    return MVProductMatrix(
        data=arr.reshape(1, len(mask), len(mask)),
        a_mask=mask,
        b_mask=mask,
        c_mask=mask,
        product=EProduct.GP,
        left=True,
    )
