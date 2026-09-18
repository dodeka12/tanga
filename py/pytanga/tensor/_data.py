# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""pytanga.tensor._data — MVTensor data class."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from dataclasses import dataclass
from typing import Any, TYPE_CHECKING, cast, overload

import numpy as np

from pytanga.algebra import MV
from pytanga.blade_mask import BladeMask

if TYPE_CHECKING:
    from pytanga.algebra import Algebra

    from ._labeled import MVLabeledTensor


def _rebuild_mvtensor(
    tensor: MVTensor, key: Any, result: np.ndarray
) -> MVTensor | np.ndarray:
    """Attempt to preserve mask metadata when slicing an MVTensor.

    Parameters
    ----------
    tensor : MVTensor
        The original tensor being indexed.
    key : int | slice | tuple | None | Ellipsis | np.ndarray | list
        The indexing key passed to ``__getitem__``.
    result : np.ndarray
        The result of ``tensor.data[key]``.

    Returns
    -------
    MVTensor | np.ndarray
        An MVTensor with inferred masks, or a raw ndarray when masks
        cannot be reliably preserved.
    """
    # Normalise key to a tuple matching original ndim
    if not isinstance(key, tuple):
        key = (key,)

    ndim_orig = tensor.data.ndim
    new_masks: list[BladeMask | None] = []

    # Expand ellipsis / None to track all axes
    # We use numpy's index expansion logic to map old axes → new axes
    # Simple approach: iterate original axes, determine if collapsed
    ellipsis_seen = False
    n_ellipsis = ndim_orig - len(key) + sum(1 for k in key if k is not Ellipsis)

    key_expanded: list[Any] = []
    for k in key:
        if k is Ellipsis:
            if ellipsis_seen:
                raise IndexError("only one Ellipsis allowed")
            ellipsis_seen = True
            key_expanded.extend([slice(None)] * n_ellipsis)
        elif k is None:
            key_expanded.append(k)
        else:
            key_expanded.append(k)

    # Pad with full slices if key is shorter than ndim (implicit trailing slices)
    while len(key_expanded) < ndim_orig:
        key_expanded.append(slice(None))

    # Now iterate over original axes
    orig_axis = 0
    for k in key_expanded:
        if orig_axis >= ndim_orig:
            break
        if k is None:
            # np.newaxis — insert None mask
            new_masks.append(None)
            continue
        mask = tensor.masks[orig_axis]
        if isinstance(k, int):
            # Integer indexing collapses the axis
            orig_axis += 1
        elif isinstance(k, slice):
            # Slice preserves the axis — filter mask if present
            if mask is not None:
                # Compute the slice indices to build a filtered mask
                start, stop, step = k.indices(tensor.data.shape[orig_axis])
                sliced_ids = [mask.ids[idx] for idx in range(start, stop, step)]
                filtered_mask = BladeMask(mask.algebra, sliced_ids)
                new_masks.append(filtered_mask)
            else:
                new_masks.append(None)
            orig_axis += 1
        elif isinstance(k, (np.ndarray, list)):
            # Fancy indexing — ambiguous, fall back to raw ndarray
            return result
        else:
            # Unknown key type, fall back
            return result

    if len(new_masks) != result.ndim:
        # Dimension mismatch indicates ambiguous indexing
        return result

    return MVTensor(data=result, masks=tuple(new_masks))


def _resolve_basis_directions(
    mask: BladeMask, spec: Any
) -> tuple[list[str], list[MV]]:
    """Resolve a basis spec into ``(names, vectors)`` over *mask*."""
    if spec is None:
        return mask.basis_names, mask.basis_vectors
    if isinstance(spec, BladeMask):
        return spec.basis_names, spec.basis_vectors
    if isinstance(spec, Mapping):
        names = [str(name) for name in spec.keys()]
        return names, [cast(MV, spec[name]) for name in names]
    if isinstance(spec, Sequence) and not isinstance(spec, (str, bytes)):
        vecs = [cast(MV, v) for v in spec]
        return [f"d{i}" for i in range(len(vecs))], vecs
    raise TypeError(f"unsupported basis spec: {type(spec).__name__}")


def _basis_right_matrix(mask: BladeMask, vecs: Sequence[MV]) -> np.ndarray:
    """Raw→named change-of-basis matrix, shape ``(len(mask), n_directions)``."""
    from pytanga.matrix.convert import to_matrix

    if not vecs:
        return np.empty((len(mask), 0), dtype=np.float64)
    return to_matrix(list(vecs), mask=mask).data


def _basis_left_matrix(mask: BladeMask, vecs: Sequence[MV]) -> np.ndarray:
    """Named→raw coefficient matrix, shape ``(n_directions, len(mask))``."""
    return np.linalg.pinv(_basis_right_matrix(mask, vecs))


@dataclass
class MVTensor:
    """A general N‑D tensor labelled by blade masks.

    Each axis is either associated with a ``BladeMask`` (the data along
    that axis is indexed by blade ids) or with ``None`` (the axis is a
    batch / counting dimension, e.g. a list of multivectors).

    Parameters
    ----------
    data : np.ndarray
        N‑D numpy array.
    masks : tuple[BladeMask | None, ...]
        One mask (or None) per axis.  ``len(masks) == data.ndim``.
    """

    data: np.ndarray
    masks: Sequence[BladeMask | None]

    def __post_init__(self) -> None:
        """Validate that masks length matches ndim and mask sizes match data shape."""
        if len(self.masks) != self.data.ndim:
            raise ValueError(
                f"len(masks)={len(self.masks)} must equal data.ndim={self.data.ndim}"
            )
        for i, mask in enumerate(self.masks):
            if mask is not None and len(mask) != self.data.shape[i]:
                raise ValueError(
                    f"axis {i}: mask size {len(mask)} != data shape {self.data.shape[i]}"
                )

    @property
    def shape(self) -> tuple[int, ...]:
        """Shape of the underlying data array."""
        return cast("tuple[int, ...]", self.data.shape)

    @property
    def algebra(self) -> "Algebra":
        """The algebra this tensor belongs to (from the first non-None mask)."""
        for mask in self.masks:
            if mask is not None:
                return mask.algebra
        raise ValueError("MVTensor has no blade mask — cannot infer algebra")

    def __repr__(self) -> str:
        mask_reprs = [repr(m) if m is not None else "None" for m in self.masks]
        return f"MVTensor(shape={self.data.shape}, masks=({', '.join(mask_reprs)}))"

    # ------------------------------------------------------------------
    # 1.1 – __getitem__
    # ------------------------------------------------------------------

    @overload
    def __getitem__(self, key: str) -> "MVLabeledTensor": ...
    @overload
    def __getitem__(self, key: Any) -> "MVTensor | np.ndarray | MVLabeledTensor": ...
    def __getitem__(self, key: Any) -> "MVTensor | np.ndarray | MVLabeledTensor":
        """Label or NumPy indexing.

        String keys create an ``MVLabeledTensor`` (lazy import).
        All other keys (slices, integers, tuples, ellipsis) are forwarded
        to the underlying ``self.data`` with mask metadata preserved when
        possible.
        """
        if isinstance(key, str):
            from ._labeled import MVLabeledTensor

            return MVLabeledTensor(self, key)
        result = self.data[key]
        if isinstance(result, np.ndarray):
            return _rebuild_mvtensor(self, key, result)
        return result

    # ------------------------------------------------------------------
    # 1.2 – Scalar ops
    # ------------------------------------------------------------------

    def mul_scalar(self, scalar: float) -> MVTensor:
        """Multiply tensor data by a scalar (element‑wise)."""
        return MVTensor(data=self.data * scalar, masks=self.masks)

    def div_scalar(self, scalar: float) -> MVTensor:
        """Divide tensor data by a scalar (element‑wise)."""
        return MVTensor(data=self.data / scalar, masks=self.masks)

    def rdiv_scalar(self, scalar: float) -> MVTensor:
        """Scalar divided by tensor data (element‑wise)."""
        return MVTensor(data=scalar / self.data, masks=self.masks)

    # ------------------------------------------------------------------
    # 1.3 – Factory constructors
    # ------------------------------------------------------------------

    @staticmethod
    def zeros(
        specs: list[BladeMask | int],
        dtype: np.dtype | str | None = None,
    ) -> MVTensor:
        """Create a zero-initialised MVTensor from a list of specifiers.

        Each element is either a ``BladeMask`` or an ``int``:

        - ``BladeMask`` → the axis uses that mask; its size is ``len(mask)``.
        - ``int`` → the axis has mask ``None`` (batch/counting axis); the
          integer gives the dimension size.

        Parameters
        ----------
        specs : list[BladeMask | int]
            Axis specifiers.
        dtype : np.dtype | str | None
            Data type.  Defaults to ``float64``.
        """
        masks: list[BladeMask | None] = []
        shape: list[int] = []
        for spec in specs:
            if isinstance(spec, BladeMask):
                masks.append(spec)
                shape.append(len(spec))
            elif isinstance(spec, int):
                masks.append(None)
                shape.append(spec)
            else:
                raise TypeError(f"expected BladeMask or int, got {type(spec).__name__}")
        if dtype is None:
            dtype = "float64"
        return MVTensor(data=np.zeros(tuple(shape), dtype=dtype), masks=tuple(masks))

    @staticmethod
    def zeros_like(other: MVTensor, *, dtype: np.dtype | str | None = None) -> MVTensor:
        """Create a zero-initialised MVTensor with the same shape and masks."""
        if dtype is None:
            dtype = other.data.dtype
        return MVTensor(data=np.zeros(other.data.shape, dtype=dtype), masks=other.masks)

    def get_array(
        self,
        *,
        out_basis: Any = None,
        axis_bases: Mapping[int, Any] | None = None,
    ) -> np.ndarray:
        """Return the tensor recombined into named bases as a raw numpy array.

        Each ``BladeMask`` axis is expressed in its named directions (the mask's
        ``basis_vectors`` by default).  Axis 0 (the output axis) uses the dual
        mapping ``pinv(B_out) @ data``; every other blade axis uses the direct
        mapping ``data @ B_axis``.  ``None`` (batch/counting) axes are left
        unchanged.  ``out_basis`` overrides axis 0's directions; ``axis_bases``
        maps axis index → directions for the remaining axes.
        """
        data = np.asarray(self.data, dtype=np.float64)
        masks = self.masks
        axis_bases = axis_bases or {}

        # Output axis (axis 0) — dual mapping (express the result in the basis).
        out_mask = masks[0]
        if isinstance(out_mask, BladeMask):
            out_vecs = _resolve_basis_directions(out_mask, out_basis)[1]
            c_out = _basis_left_matrix(out_mask, out_vecs)
            data = np.tensordot(c_out, data, axes=([1], [0]))

        # Remaining blade axes — direct mapping, in descending axis order.
        pairs: list[tuple[int, np.ndarray]] = []
        for i in range(1, len(masks)):
            mask = masks[i]
            if isinstance(mask, BladeMask):
                vecs = _resolve_basis_directions(mask, axis_bases.get(i))[1]
                pairs.append((i, _basis_right_matrix(mask, vecs)))
        for i, b_var in sorted(pairs, key=lambda p: -p[0]):
            data = np.moveaxis(data, i, -1)
            data = np.tensordot(data, b_var, axes=([-1], [0]))
            data = np.moveaxis(data, -1, i)
        return data
