# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
"""pytanga.matrix.convert — MV ↔ MVMatrix conversion helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from pytanga.blade_mask import BladeMask
from pytanga.algebra import MV
from . import MVMatrix

if TYPE_CHECKING:
    from pytanga.algebra import Algebra

from pytanga.algebra import MVLike, _as_mv


def to_matrix(
    a: MVLike | list[MVLike],
    *,
    mask: BladeMask | None = None,
    algebra: "Algebra | None" = None,
) -> MVMatrix:
    """Extract coefficients of *a* into an MVMatrix.

    Parameters
    ----------
    a : MVLike | list[MVLike]
        Single multivector, scalar, string expression, or list thereof.
    mask : BladeMask | None
        Row index space.  If ``None``, the full algebra mask is used.
    algebra : Algebra | None
        The algebra to use.  Required when *a* is a string or scalar
        and no *mask* is given.  Ignored if the algebra can be inferred
        from *mask* or from an MV in *a*.

    Returns
    -------
    MVMatrix
        Shape ``(len(mask), n_mvs)``.
    """
    # --- resolve algebra ------------------------------------------------
    alg: Algebra | None = None
    if mask is not None:
        alg = mask.algebra
    elif isinstance(a, list):
        for x in a:
            if isinstance(x, MV):
                alg = x.algebra
                break
    elif isinstance(a, MV):
        alg = a.algebra

    if alg is None:
        if algebra is not None:
            alg = algebra
        else:
            raise ValueError("Cannot determine algebra — provide mask= or algebra=")

    # --- resolve mask ----------------------------------------------------
    if mask is None:
        mask = BladeMask.full(alg)

    # --- build MVMatrix --------------------------------------------------
    if isinstance(a, list):
        mvs = [_as_mv(alg, x) for x in a]
        cols = [alg._mod.to_matrix(mv._impl, mask.ids) for mv in mvs]
        arr = np.hstack(cols)
        return MVMatrix(data=arr, row_mask=mask)

    mv = _as_mv(alg, a)
    arr = alg._mod.to_matrix(mv._impl, mask.ids)
    return MVMatrix(data=arr, row_mask=mask)


def from_matrix(m: MVMatrix) -> "MV | list[MV]":
    """Reconstruct MV(s) from an MVMatrix.

    Returns a single MV when ``m.is_single``, otherwise a list of MVs.
    """
    alg = m.algebra
    if m.is_single:
        impl = alg._mod.from_matrix(m.data, m.row_mask.ids)
        return MV(impl, alg)
    mvs: list[MV] = []
    for col_idx in range(m.n_cols):
        col_data = m.data[:, col_idx : col_idx + 1]
        impl = alg._mod.from_matrix(col_data, m.row_mask.ids)
        mvs.append(MV(impl, alg))
    return mvs
