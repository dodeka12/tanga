# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""pytanga.matrix._data — MVMatrix data class."""

from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from pytanga.blade_mask import BladeMask

if TYPE_CHECKING:
    from .algebra import Algebra


@dataclass
class MVMatrix:
    """A numpy matrix whose rows are labelled by a blade mask.

    Each column stores the coefficients of one multivector, all ordered
    by the same ``row_mask``.  For a single multivector this is a column
    vector (``n_cols == 1``); for a list of MVs this is an ``(n_rows, n_mvs)``
    matrix.

    Parameters
    ----------
    data : np.ndarray
        Shape ``(len(row_mask), n_cols)``.
    row_mask : BladeMask
        Ordered blade ids labelling each row.
    """

    data: np.ndarray
    row_mask: BladeMask

    def __post_init__(self) -> None:
        if self.data.ndim != 2:
            raise ValueError(f"MVMatrix.data must be 2-D, got ndim={self.data.ndim}")
        if len(self.row_mask) != self.data.shape[0]:
            raise ValueError(
                f"len(row_mask)={len(self.row_mask)} does not match "
                f"data.shape[0]={self.data.shape[0]}"
            )

    # ------------------------------------------------------------------
    # Convenience properties
    # ------------------------------------------------------------------

    @property
    def shape(self) -> tuple[int, ...]:
        """Shape of the underlying data array."""
        return self.data.shape

    @property
    def n_cols(self) -> int:
        """Number of multivectors stored (columns)."""
        return self.data.shape[1]

    @property
    def is_single(self) -> bool:
        """True when exactly one multivector is stored."""
        return self.data.shape[1] == 1

    @property
    def algebra(self) -> "Algebra":
        """The algebra this matrix belongs to (from row_mask)."""
        return self.row_mask._alg


