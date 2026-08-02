# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
"""pytanga.matrix._dispatch — C++ binding dispatch for product matrices.

These are **implementation details**, not part of the public API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from pytanga.algebra import EInv, EProduct

if TYPE_CHECKING:
    from pytanga.algebra import Algebra


def _dispatch_product_matrix(
    alg: "Algebra",
    product: EProduct,
    mv_impl,
    b_ids: list[int],
    c_ids: list[int],
    left: bool,
    left_inv: EInv = EInv.ID,
    right_inv: EInv = EInv.ID,
) -> np.ndarray:
    """Call the 2‑mask C++ binding.

    Iterates over ALL blades of the MV, contracts each blade's
    coefficient: matA(idxC, idxB) = Σ fValA·sign.

    Returns a 2‑D numpy array of shape ``(|c_mask|, |b_mask|)``.
    """
    _fn_map = {
        EProduct.GP: "product_matrix_gp",
        EProduct.IP: "product_matrix_ip",
        EProduct.OP: "product_matrix_op",
    }
    try:
        fn = _fn_map[product]
    except KeyError:
        raise ValueError(f"Unknown product {product!r}")

    try:
        f = getattr(alg._mod, fn)
    except AttributeError:
        raise RuntimeError(f"C++ binding {fn!r} not found on algebra module")
    return f(mv_impl, b_ids, c_ids, left, str(left_inv), str(right_inv))


def _dispatch_product_matrix_masked(
    alg: "Algebra",
    product: EProduct,
    mv_impl,
    a_ids: list[int],
    b_ids: list[int],
    c_ids: list[int],
    left: bool,
    left_inv: EInv = EInv.ID,
    right_inv: EInv = EInv.ID,
) -> np.ndarray:
    """Call the 3‑mask C++ binding.

    Iterates over xMaskA, looks up coefficients from the MV.
    Blades in a_mask but absent from MV → treated as zero.
    Blades of MV outside a_mask → ignored.

    Returns a 2‑D numpy array of shape ``(|c_mask|, |b_mask|)``.
    """
    _fn_map = {
        EProduct.GP: "product_matrix_gp_masked",
        EProduct.IP: "product_matrix_ip_masked",
        EProduct.OP: "product_matrix_op_masked",
    }

    try:
        fn = _fn_map[product]
    except KeyError:
        raise ValueError(f"Unknown product {product!r}")

    try:
        f = getattr(alg._mod, fn)
    except AttributeError:
        raise RuntimeError(f"C++ binding {fn!r} not found on algebra module")
    return f(mv_impl, a_ids, b_ids, c_ids, left, str(left_inv), str(right_inv))


def _dispatch_product_matrix_array(
    alg: "Algebra",
    product: EProduct,
    mv_impls: list,
    b_ids: list[int],
    c_ids: list[int],
    left: bool,
) -> np.ndarray:
    """Call the array C++ binding (stacked product matrix from MV list).

    Returns a 2‑D numpy array of shape (len(impls)·|c_mask|, |b_mask|).
    """
    _fn_map = {
        EProduct.GP: "product_matrix_array_gp",
        EProduct.IP: "product_matrix_array_ip",
        EProduct.OP: "product_matrix_array_op",
    }
    try:
        fn = _fn_map[product]
    except KeyError:
        raise ValueError(f"Unknown product {product!r}")

    try:
        f = getattr(alg._mod, fn)
    except AttributeError:
        raise RuntimeError(f"C++ binding {fn!r} not found on algebra module")
    return f(mv_impls, b_ids, c_ids, left)
