# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""pytanga.expression._data_array — DataArray: labeled array data for bindings."""

from __future__ import annotations

import numpy as np

from pytanga.algebra import MV
from pytanga.blade_mask import BladeMask

from pytanga.tensor.convert import to_tensor


class DataArray:
    """Labeled array data: a NumPy array plus per-axis specs.

    Each axis spec is either a :class:`~pytanga.BladeMask` (a blade axis) or a
    ``str`` (a counting-axis name, stored as a ``None``-mask axis).  ``DataArray``
    is the data container accepted by ``Expression.__call__`` for variable
    binding and counting-axis reduction.
    """

    __slots__ = ("_array", "_masks")

    def __init__(self, array: "np.ndarray | list | tuple", masks) -> None:
        specs = tuple(masks)
        data = self._normalize(array, specs)
        self._validate_specs(specs, data.ndim)
        self._array = np.asarray(data)
        self._masks = specs

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize(array, specs) -> np.ndarray:
        """Return the underlying NumPy array for *array* and *specs*."""
        if isinstance(array, np.ndarray):
            return array
        if isinstance(array, (list, tuple)):
            if array and all(isinstance(x, MV) for x in array):
                blade_axes = [
                    i for i, s in enumerate(specs) if isinstance(s, BladeMask)
                ]
                str_axes = [i for i, s in enumerate(specs) if isinstance(s, str)]
                if len(blade_axes) != 1 or len(str_axes) != 1 or len(specs) != 2:
                    raise ValueError(
                        "DataArray from a list of MVs requires exactly one "
                        "BladeMask and one counting-axis name"
                    )
                blade_axis = blade_axes[0]
                blade_mask = specs[blade_axis]
                # to_tensor(list, mask) -> shape (|mask|, n), masks (blade, None).
                tensor = to_tensor(list(array), mask=blade_mask)
                if blade_axis == 0:
                    return tensor.data
                return tensor.data.T  # (n, |mask|)
            return np.asarray(array)
        raise TypeError(
            f"DataArray data must be an ndarray, list of MVs, or list of "
            f"scalars, got {type(array).__name__}"
        )

    @staticmethod
    def _validate_specs(specs: tuple, ndim: int) -> None:
        if len(specs) != ndim:
            raise ValueError(
                f"DataArray has {len(specs)} axis specs but data has {ndim} axes"
            )
        names: set[str] = set()
        markers = 0
        for spec in specs:
            if isinstance(spec, BladeMask):
                continue
            if isinstance(spec, str):
                if spec in ("_", "*"):
                    markers += 1
                if spec in names:
                    raise ValueError(f"duplicate counting-axis name {spec!r}")
                names.add(spec)
            else:
                raise TypeError(
                    f"DataArray axis spec must be a BladeMask or str, "
                    f"got {type(spec).__name__}"
                )
        if markers > 1:
            raise ValueError("at most one '_' or '*' marker is allowed")

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def array(self) -> np.ndarray:
        """The underlying NumPy array."""
        return self._array

    @property
    def masks(self) -> tuple:
        """The per-axis specs (``BladeMask | str``)."""
        return self._masks

    @property
    def ndim(self) -> int:
        """Number of axes."""
        return self._array.ndim

    @property
    def shape(self) -> tuple[int, ...]:
        """Shape of the underlying array."""
        return self._array.shape

    def __repr__(self) -> str:
        parts = []
        for spec in self._masks:
            parts.append(repr(spec) if isinstance(spec, BladeMask) else spec)
        return f"DataArray(shape={self._array.shape}, masks=({', '.join(parts)}))"

    # ------------------------------------------------------------------
    # Renaming
    # ------------------------------------------------------------------

    def _rename_mask(self, old: str, new: str) -> tuple:
        masks = list(self._masks)
        if old != new and new in masks:
            raise ValueError(f"counting-axis name {new!r} is already in use")
        for i, spec in enumerate(masks):
            if spec == old:
                masks[i] = new
                return tuple(masks)
        raise ValueError(f"counting-axis name {old!r} not found")

    def rename_axis(self, old: str, new: str) -> "DataArray":
        """Return a new ``DataArray`` with counting axis *old* renamed to *new*."""
        return DataArray(self._array, self._rename_mask(old, new))

    def __call__(self, **renames: str) -> "DataArray":
        """Rename counting axes in place (``old=new``) and return ``self``."""
        masks = self._masks
        for old, new in renames.items():
            masks = self._rename_mask(old, new)
        self._masks = masks
        self._validate_specs(self._masks, self._array.ndim)
        return self
