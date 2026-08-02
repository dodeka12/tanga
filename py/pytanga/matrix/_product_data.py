# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""pytanga.matrix._product_data — MVProductMatrix data class."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from pytanga.blade_mask import BladeMask
from pytanga.algebra import EInv, EProduct

if TYPE_CHECKING:
    from pytanga.algebra import Algebra


@dataclass
class MVProductMatrix:
    """A 3‑D tensor encoding one product matrix per blade of a_mask.

    Each slice ``data[i, :, :]`` is the ``(|c_mask| x |b_mask|)`` product
    matrix for multivector ``data[i]``.

    A standard numpy matrix product with an MVMatrix column vector V
    contracts the last axis and broadcasts over the first::

        np.matmul(M.data, V.data)   →  (|a_mask|, |c_mask|, 1)
        .squeeze(-1).T              →  (|c_mask|, |a_mask|)   (MVMatrix layout)

    Parameters
    ----------
    data : np.ndarray
        Shape ``(|multivectors|, |c_mask|, |b_mask|)``.  3‑D tensor.
    a_mask : BladeMask
        First  axis — the blade subspace of multivector.
    b_mask : BladeMask
        Last   axis — the subspace of the unknown X.
    c_mask : BladeMask
        Middle axis — the output subspace.
    left_inv : EInv
        Involution applied to the left operand (A). Default: identity.
    right_inv : EInv
        Involution applied to the right operand (X). Default: identity.
    """

    data: np.ndarray
    a_mask: BladeMask
    b_mask: BladeMask
    c_mask: BladeMask
    product: EProduct
    left: bool
    left_inv: EInv = EInv.ID
    right_inv: EInv = EInv.ID

    def __post_init__(self) -> None:
        if self.data.ndim != 3:
            raise ValueError(
                f"MVProductMatrix.data must be 3-D, got ndim={self.data.ndim}"
            )
        nc = len(self.c_mask)
        nb = len(self.b_mask)
        if self.data.shape[1] != nc or self.data.shape[2] != nb:
            raise ValueError(
                f"data.shape={self.data.shape} does not match "
                f"N x |c_mask|={nc} x |b_mask|={nb}"
            )
        if self.b_mask.algebra is not self.c_mask.algebra:
            raise ValueError("b_mask and c_mask belong to different algebras")

    @property
    def n_mvs(self) -> int:
        """Number of multivectors encoded in this tensor (= |a_mask|)."""
        return self.data.shape[0]

    @property
    def shape(self) -> tuple[int, ...]:
        return self.data.shape

    @property
    def algebra(self) -> "Algebra":
        return self.b_mask.algebra

    def __repr__(self) -> str:
        return (
            f"MVProductMatrix(shape={self.data.shape}, "
            f"a_mask={self.a_mask}, b_mask={self.b_mask}, c_mask={self.c_mask}, "
            f"product={self.product.name}, left={self.left}, "
            f"left_inv={self.left_inv.name}, right_inv={self.right_inv.name})"
        )
