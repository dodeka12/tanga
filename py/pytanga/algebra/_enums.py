# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""pytanga.enums — EProduct and EInv: StrEnum types for GA product operations and involution."""

from enum import StrEnum


class EProduct(StrEnum):
    """Product operations supported by the solver pipeline.

    Members are string‑compatible (``EProduct.GP == "gp"`` is True)
    so they can be passed directly to C++ bindings and used as dict keys.
    """

    GP = "gp"  # geometric product
    IP = "ip"  # inner (left‑contraction) product
    OP = "op"  # outer (wedge) product


class EInv(StrEnum):
    """Involution applied to a multivector operand.

    Members are string‑compatible (``EInv.REV == "rev"`` is True)
    so they can be passed directly to C++ bindings.
    """

    ID = "id"  # identity – no involution
    REV = "rev"  # reverse: rev(blade) = (-1)^(k(k-1)/2) · blade
    CONJ = "conj"  # Clifford conjugate: conj(blade) = rev(blade) · (-1)^r
