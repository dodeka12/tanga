# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
"""pytanga.blade_mask._dispatch — C++ binding dispatch for blade-mask prediction.

These are **implementation details**, not part of the public API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pytanga.algebra import EProduct

if TYPE_CHECKING:
    from pytanga.algebra import Algebra


def _dispatch_product_blade_mask(
    alg: "Algebra",
    product: EProduct,
    a_ids: list[int],
    b_ids: list[int],
    left: bool,
    complete: bool,
) -> list[int]:
    """Call the mask‑based blade‑mask prediction C++ binding.

    Returns the predicted output blade ids.
    """
    _fn_map = {
        EProduct.GP: "product_blade_mask_gp",
        EProduct.IP: "product_blade_mask_ip",
        EProduct.OP: "product_blade_mask_op",
    }
    try:
        fn = _fn_map[product]
    except KeyError:
        raise ValueError(f"Unknown product {product!r}")

    try:
        f = getattr(alg._mod, fn + "_a")
    except AttributeError:
        raise RuntimeError(f"C++ binding {fn}_a not found on algebra module")
    return f(a_ids, b_ids, left, complete)
