# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
"""pytanga.tensor.product — build the 3-D product tensor from blade masks."""

from __future__ import annotations

from pytanga.blade_mask import BladeMask
from pytanga.blade_mask.predict import product_blade_mask
from pytanga.algebra import EInv, EProduct

from . import MVTensor


def product_tensor(
    a_mask: BladeMask,
    b_mask: BladeMask,
    c_mask: BladeMask | None = None,
    *,
    product: EProduct = EProduct.GP,
    left: bool = True,
    a_inv: EInv = EInv.ID,
    b_inv: EInv = EInv.ID,
    c_inv: EInv = EInv.ID,
) -> MVTensor:
    """Build the 3-D product tensor O from blade masks as an MVTensor.

    The algebra is obtained from *a_mask*; both masks must belong to the
    same algebra.

    When *c_mask* is ``None`` (default), it is computed automatically via
    :func:`~pytanga.blade_mask.predict.product_blade_mask` for the given
    *a_mask*, *b_mask*, and *product*.

    The returned tensor has ``masks = (c_mask, a_mask, b_mask)`` -- axis 0
    corresponds to the result blade, axis 1 to the left operand A, and
    axis 2 to the right operand B.

    If *left* is True: the tensor encodes A ∘ B = C.
    If *left* is False: the tensor encodes B ∘ A = C.

    *a_inv* / *b_inv* specify an optional involution (reverse or
    conjugate) applied to the a-mask / b-mask blades before the product.
    *c_inv* specifies an involution applied to the result multivector
    after the product.  All involutions are applied implicitly on the
    C++ side by adjusting the ±1 entries of the tensor.

    Parameters
    ----------
    a_mask : BladeMask
        Blade ids of the A operand.
    b_mask : BladeMask
        Blade ids of the B operand.
    c_mask : BladeMask | None
        Blade ids of the result C.  Computed from *a_mask* and *b_mask* if ``None``.
    product : EProduct
        Which GA operation to encode (``GP``, ``IP``, or ``OP``).
    left : bool
        If True (default): A ∘ B = C.  If False: B ∘ A = C.
    a_inv : EInv
        Involution applied to the A operand (``ID``, ``REV``, or ``CONJ``).
    b_inv : EInv
        Involution applied to the B operand (``ID``, ``REV``, or ``CONJ``).
    c_inv : EInv
        Involution applied to the result multivector (``ID``, ``REV``, or ``CONJ``).

    Returns
    -------
    MVTensor
        Shape ``(|c_mask|, |a_mask|, |b_mask|)`` with +-1/0 entries.
    """
    assert b_mask.algebra is a_mask.algebra, (
        "b_mask belongs to a different algebra than a_mask"
    )
    alg = a_mask.algebra

    if c_mask is None:
        c_mask = product_blade_mask(a_mask, b_mask, product=product)

    assert c_mask.algebra is alg

    _fn_map = {
        EProduct.GP: "product_tensor_gp",
        EProduct.IP: "product_tensor_ip",
        EProduct.OP: "product_tensor_op",
    }
    fn = getattr(alg._mod, _fn_map[product])
    arr = fn(
        a_mask.ids,
        b_mask.ids,
        c_mask.ids,
        left,
        str(a_inv),
        str(b_inv),
        str(c_inv),
    )
    # arr is already 3-D from the binding (via _tensor_to_arr in C++)

    return MVTensor(
        data=arr,
        masks=(c_mask, a_mask, b_mask),
    )


def product_tensor_rev(mask: BladeMask) -> MVTensor:
    """Build a diagonal product tensor encoding the reverse sign for each blade.

    The reverse of a blade of grade k introduces a sign (-1)^(k(k-1)/2):
    grades 2 and 3 mod 4 are negated.  The result is a square
    |mask| × |mask| diagonal matrix where M[i,i] = ±1.
    """
    alg = mask.algebra
    arr = alg._mod.product_matrix_rev(mask.ids)
    return MVTensor(
        data=arr.reshape(len(mask), len(mask)),
        masks=(mask, mask),
    )


def product_tensor_conj(mask: BladeMask) -> MVTensor:
    """Build a diagonal product tensor encoding the conjugate sign for each blade.

    The Clifford conjugate introduces a sign (-1)^(k(k-1)/2 + r) where k
    is the grade and r is the count of negative-metric basis vectors in
    the blade.  In a pure Euclidean algebra this reduces to the reverse.

    The result is a square |mask| × |mask| diagonal matrix where
    M[i,i] = ±1.
    """
    alg = mask.algebra
    arr = alg._mod.product_matrix_conj(mask.ids)
    return MVTensor(
        data=arr.reshape(len(mask), len(mask)),
        masks=(mask, mask),
    )
