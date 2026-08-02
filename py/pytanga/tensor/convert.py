# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
"""pytanga.tensor.convert — MV ↔ MVTensor conversion helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from pytanga.blade_mask import BladeMask
from pytanga.algebra import MV
from . import MVTensor

if TYPE_CHECKING:
    from pytanga.algebra import Algebra

from pytanga.algebra import MVLike, _as_mv
from pytanga.matrix.convert import to_matrix


def to_tensor(
    a: MVLike | list[MVLike],
    *,
    mask: BladeMask | None = None,
    algebra: "Algebra | None" = None,
) -> MVTensor:
    """Convert one or more multivectors into an MVTensor.

    - Single MV → rank‑1 tensor with ``masks = (BladeMask,)``.
    - List of *n* MVs → rank‑2 tensor with ``masks = (BladeMask, None)``
      where axis 1 is the list‑ordering axis (no blade mask).

    Parameters
    ----------
    a : MVLike | list[MVLike]
        Single multivector or list thereof.
    mask : BladeMask | None
        Row index space.  If None, auto‑derived from the MV(s).
    algebra : Algebra | None
        Needed only when *a* is a bare string/scalar without mask context.

    Returns
    -------
    MVTensor
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

    if isinstance(a, list):
        mvs = [_as_mv(alg, x) for x in a]
        n = len(mvs)
        dtype = np.float64 if alg.dtype.startswith("float") else np.int64
        arr = np.zeros((len(mask), n), dtype=dtype)
        for i, mv in enumerate(mvs):
            mat = to_matrix(mv, mask=mask)
            arr[:, i] = mat.data[:, 0]
        return MVTensor(data=arr, masks=(mask, None))

    # Single MV
    mv = _as_mv(alg, a)
    arr = to_matrix(mv, mask=mask).data.ravel()
    return MVTensor(data=arr, masks=(mask,))


def from_tensor(t: MVTensor) -> "MV | list":
    """Reconstruct multivector(s) from an MVTensor.

    Accepts any MVTensor that has **exactly one** axis with a ``BladeMask``
    and any number of axes with ``None``.  The blade‑mask axis is interpreted
    as the coefficient axis; all ``None`` axes are nested list axes.

    Returns
    -------
    MV | list[...]
        - **Rank 1** ``(BladeMask,)`` → a single ``MV``.
        - **Rank 2** ``(BladeMask, None)`` → ``list[MV]`` (one per column).
        - **Rank N** with one mask + (N‑1) ``None`` axes →
          nested list of ``MV``, e.g. ``list[list[MV]]`` for rank 3, etc.
    """
    # Find the single blade‑mask axis
    mask_axes = [i for i, m in enumerate(t.masks) if m is not None]
    if len(mask_axes) != 1:
        raise ValueError(
            f"from_tensor expects exactly one BladeMask axis, got {len(mask_axes)}"
        )
    baxis = mask_axes[0]
    mask = t.masks[baxis]  # type: ignore[assignment]
    alg = mask.algebra

    # Move the blade‑mask axis to position 0 for easy slicing
    data = np.moveaxis(t.data, baxis, 0)  # shape: (|mask|, ...)
    n_blades = data.shape[0]

    # Build nested list structure for the non‑blade axes
    other_shape = data.shape[1:]  # the None‑axis dimensions

    def _build(idx: tuple[int, ...]) -> MV:
        """Construct a single MV from a sub‑array indexed by *idx*."""
        coeffs = data[(slice(None),) + idx]
        mv_dict = {int(bid): float(coeffs[j]) for j, bid in enumerate(mask.ids)}
        return alg.multivector(mv_dict)

    if len(other_shape) == 0:
        # Rank 1 — single MV
        return _build(())

    # Rank ≥ 2 — build nested list recursively
    def _recurse(dims: tuple[int, ...], prefix: tuple[int, ...]) -> list:
        if len(dims) == 0:
            return _build(prefix)
        result = []
        for k in range(dims[0]):
            result.append(_recurse(dims[1:], prefix + (k,)))
        return result

    return _recurse(other_shape, ())
