# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""pytanga.tensor._labeled — MVLabeledTensor wrapper class."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from pytanga.blade_mask import BladeMask

if TYPE_CHECKING:
    from ._data import MVTensor

# ---------------------------------------------------------------------------
# Label canonicalisation & helpers
# ---------------------------------------------------------------------------

_LABEL_PAIR_RE = re.compile(r"^([a-zA-Z])([_*]|$)")


def _canonicalise(user_labels: str) -> str:
    """Convert a user label string to the canonical extended format.

    Rules
    -----
    * A raw name is a single letter ``[a-zA-Z]``.
    * If the next character is ``_`` → element‑wise mode.
    * If the next character is ``*`` → explicit contraction, skip it.
    * If the next character is another letter (or end) → contraction
      mode (default ``*`` inserted).
    * ``_`` must immediately follow a raw name; leading/trailing
      underscores or doubled underscores are errors.

    Examples
    --------
    ``'kij'``   → ``'k*i*j*'``
    ``'in_'``   → ``'i*n_'``
    ``'i*n_'``  → ``'i*n_'``   (already canonical)
    ``'_i'``    → ``ValueError``
    ``'ij_n'``  → ``'i*j_n*'``  (``_`` is always a suffix on the
                 preceding letter)
    """
    if not user_labels:
        return ""  # empty labels are valid for scalar tensors

    result: list[str] = []
    i = 0
    while i < len(user_labels):
        ch = user_labels[i]
        # ``_`` may not appear as a free‑standing character
        if ch == "_":
            raise ValueError(
                f"stray underscore at position {i} in '{user_labels}' "
                f"(underscore must immediately follow a letter)"
            )
        if ch == "*":
            # Stray ``*`` — already‑canonical string was passed; skip
            i += 1
            continue
        if not ("a" <= ch <= "z" or "A" <= ch <= "Z"):
            raise ValueError(
                f"expected a letter (raw index name) at position {i} "
                f"in '{user_labels}', got '{ch}'"
            )
        name = ch
        i += 1
        if i < len(user_labels) and user_labels[i] == "_":
            # Element‑wise mode
            result.append(name + "_")
            i += 1
            # Check for double underscore
            if i < len(user_labels) and user_labels[i] == "_":
                raise ValueError(
                    f"double underscore at position {i} in '{user_labels}'"
                )
        elif i < len(user_labels) and user_labels[i] == "*":
            # Already‑canonical contraction marker — skip the '*'
            result.append(name + "*")
            i += 1
        else:
            # Contraction mode (default, next char is a letter or EOF)
            result.append(name + "*")
    return "".join(result)


def _raw_names(extended_labels: str) -> str:
    """Extract raw index names from extended labels.

    ``'k*i*j*'`` → ``'kij'``
    """
    if not extended_labels:
        return ""
    if len(extended_labels) % 2 != 0:
        raise ValueError(
            f"extended label string must have even length, got '{extended_labels}'"
        )
    return "".join(extended_labels[i] for i in range(0, len(extended_labels), 2))


def _mode_at(extended_labels: str, axis: int) -> str:
    """Return the mode character (``'*'`` or ``'_'``) for *axis*."""
    pos = 2 * axis + 1
    if pos >= len(extended_labels):
        raise IndexError(f"axis {axis} out of range for labels '{extended_labels}'")
    return extended_labels[pos]


def _is_elemwise(extended_labels: str, axis: int) -> bool:
    """Check if *axis* is marked element‑wise."""
    return _mode_at(extended_labels, axis) == "_"


def _validate_labels(labels: str, ndim: int) -> None:
    """Validate that *labels* has length 2*ndim and contains valid names."""
    if len(labels) != 2 * ndim:
        raise ValueError(
            f"labels '{labels}' have {len(labels)//2} axes "
            f"but tensor has ndim={ndim}"
        )
    # Check each pair
    for a in range(ndim):
        name = labels[2 * a]
        mode = labels[2 * a + 1]
        if not ("a" <= name <= "z" or "A" <= name <= "Z"):
            raise ValueError(f"invalid raw name '{name}' in labels '{labels}'")
        if mode not in ("*", "_"):
            raise ValueError(f"invalid mode '{mode}' in labels '{labels}'")
    # Check for duplicate raw names
    raw = _raw_names(labels)
    if len(set(raw)) != len(raw):
        raise ValueError(
            f"duplicate raw index names in labels '{labels}'"
        )


def _extended_from_raw(raw: str, modes: dict[str, str]) -> str:
    """Build extended label string from raw names and a modes dict.

    *modes* maps raw name → ``'*'`` or ``'_'``.  Missing entries default
    to ``'*'``.
    """
    return "".join(ch + modes.get(ch, "*") for ch in raw)


# ---------------------------------------------------------------------------
# MVLabeledTensor
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MVLabeledTensor:
    """A labeled tensor wrapping an ``MVTensor`` with axis labels.

    Parameters
    ----------
    tensor : MVTensor
        The underlying multi‑vector tensor.
    labels : str
        User label string (canonicalised internally).
    """

    tensor: MVTensor
    labels: str  # stored in canonical (extended) form

    def __post_init__(self) -> None:
        # Canonicalise the user‑supplied labels string
        canonical = _canonicalise(self.labels)
        if canonical != self.labels:
            # Use object.__setattr__ because the dataclass is frozen
            object.__setattr__(self, "labels", canonical)
        _validate_labels(self.labels, self.tensor.data.ndim)

    def __repr__(self) -> str:
        return f"MVLabeledTensor(labels='{self.labels}', tensor={self.tensor!r})"

    @property
    def ndim(self) -> int:
        """Number of axes (rank) of the tensor."""
        return self.tensor.data.ndim

    @property
    def shape(self) -> tuple[int, ...]:
        """Shape of the underlying tensor."""
        return self.tensor.shape

    @property
    def data(self) -> np.ndarray:
        """The data numpy array of the referenced MVTensor."""
        return self.tensor.data

    # ------------------------------------------------------------------
    # 2.3 – __getitem__ (relabel & transpose)
    # ------------------------------------------------------------------

    def __getitem__(self, key):
        """Relabel or transpose via string key; forward slices to tensor.

        - ``A[\"ijk\"]`` → new ``MVLabeledTensor`` with labels ``\"i*j*k*\"``.
        - ``B[\"ij->ji\"]`` → transposed ``MVLabeledTensor``.
        - Slices / ints / tuples → forwarded to ``self.tensor[key]``.
        """
        if isinstance(key, str):
            if "->" in key:
                return _transpose(self, key)
            return MVLabeledTensor(self.tensor, _canonicalise(key))
        # Forward non‑string keys to MVTensor.__getitem__
        return self.tensor[key]

    # ------------------------------------------------------------------
    # 2.5 – __setitem__ (label‑aware assignment)
    # ------------------------------------------------------------------

    def __setitem__(self, key, value) -> None:
        """Assign data from *value* into *self* using label alignment.

        ``A[\"kij\"] = B[\"ji\"]`` aligns on shared labels and
        broadcasts missing dimensions.
        """
        from ._data import MVTensor as _MVTensor

        key_canon = _canonicalise(key)
        key_raw = _raw_names(key_canon)
        self_raw = _raw_names(self.labels)

        if set(key_raw) != set(self_raw):
            raise ValueError(
                f"key labels '{key_raw}' do not match tensor labels "
                f"'{self_raw}'"
            )

        # If value is a plain MVTensor, wrap it with the key labels
        if isinstance(value, _MVTensor):
            value = MVLabeledTensor(value, key_canon)

        if not isinstance(value, MVLabeledTensor):
            raise TypeError(
                f"expected MVLabeledTensor or MVTensor, got "
                f"{type(value).__name__}"
            )

        val_raw = _raw_names(value.labels)

        # Check masks compatibility on shared axes
        for name in set(self_raw) & set(val_raw):
            s_ax = self_raw.index(name)
            v_ax = val_raw.index(name)
            s_mask = self.tensor.masks[s_ax]
            v_mask = value.tensor.masks[v_ax]
            if s_mask is not None and v_mask is not None:
                if s_mask.algebra is not v_mask.algebra:
                    raise ValueError(
                        f"label '{name}': algebra mismatch"
                    )
                if s_mask.ids != v_mask.ids:
                    raise ValueError(
                        f"label '{name}': mask ids differ"
                    )
            elif (s_mask is None) != (v_mask is None):
                raise ValueError(
                    f"label '{name}': one side has a mask, the other does not"
                )
            if self.tensor.shape[s_ax] != value.tensor.shape[v_ax]:
                raise ValueError(
                    f"label '{name}': axis length mismatch "
                    f"({self.tensor.shape[s_ax]} vs {value.tensor.shape[v_ax]})"
                )

        # Names in value but not self → error
        extra = set(val_raw) - set(self_raw)
        if extra:
            raise ValueError(
                f"value has extra labels {extra} not in target {self_raw}"
            )

        # Build broadcast mapping: for each self axis, find the
        # corresponding axis in value (or insert newaxis)
        val_data = value.tensor.data
        # Build a map from val axis → val position
        val_pos = {val_raw[i]: i for i in range(len(val_raw))}
        # Expand val_data to match self_raw order, adding newaxis for
        # axes in self but not in val
        for idx, name in enumerate(self_raw):
            if name not in val_pos:
                val_data = np.expand_dims(val_data, idx)
        self.tensor.data[:] = np.broadcast_to(val_data, self.tensor.data.shape)

    # ------------------------------------------------------------------
    # 2.6 – Factory constructors
    # ------------------------------------------------------------------

    @staticmethod
    def zeros(
        labels: str,
        specs: list[BladeMask | int],
        dtype: np.dtype | str | None = None,
    ) -> MVLabeledTensor:
        """Create a zero-initialised ``MVLabeledTensor``.

        Parameters
        ----------
        labels : str
            User label string (canonicalised internally).
        specs : list[BladeMask | int]
            Same semantics as ``MVTensor.zeros``.  Must match ``ndim``.
        dtype : np.dtype | str | None
            Data type, defaults to ``float64``.
        """
        from ._data import MVTensor as _MVTensor

        tensor = _MVTensor.zeros(specs, dtype=dtype)
        return MVLabeledTensor(tensor, labels)

    @staticmethod
    def zeros_from_dict(
        labels: str,
        specs: dict[str, BladeMask | int],
        dtype: np.dtype | str | None = None,
    ) -> MVLabeledTensor:
        """Create a zero-initialised ``MVLabeledTensor`` from per‑label specs.

        Parameters
        ----------
        labels : str
            User label string.  Each raw name must appear as a key in *specs*.
        specs : dict[str, BladeMask | int]
            Maps raw index names to a ``BladeMask`` or integer size.
        dtype : np.dtype | str | None
            Data type, defaults to ``float64``.
        """
        canonical = _canonicalise(labels)
        raw = _raw_names(canonical)
        for name in raw:
            if name not in specs:
                raise ValueError(
                    f"label '{name}' not found in specs dict"
                )
        positional_specs = [specs[name] for name in raw]
        return MVLabeledTensor.zeros(labels, positional_specs, dtype=dtype)

    # ------------------------------------------------------------------
    # 3.4 / 4.3 – Scalar ops
    # ------------------------------------------------------------------

    def mul_scalar(self, scalar: float) -> MVLabeledTensor:
        """Multiply tensor data by a scalar (element‑wise)."""
        return MVLabeledTensor(self.tensor.mul_scalar(scalar), self.labels)

    def div_scalar(self, scalar: float) -> MVLabeledTensor:
        """Divide tensor data by a scalar (element‑wise)."""
        return MVLabeledTensor(self.tensor.div_scalar(scalar), self.labels)

    def rdiv_scalar(self, scalar: float) -> MVLabeledTensor:
        """Scalar divided by tensor data (element‑wise)."""
        return MVLabeledTensor(self.tensor.rdiv_scalar(scalar), self.labels)

    # ------------------------------------------------------------------
    # sum – reduce over labelled axes
    # ------------------------------------------------------------------

    def sum(self, labels: str) -> MVLabeledTensor:
        """Sum over the given labelled axes.

        Parameters
        ----------
        labels : str
            User label string identifying which axes to sum over.
            For example, ``A[\"ij\"].sum(\"j\")`` sums over axis ``j``,
            returning a tensor with only label ``i``.  ``A[\"ij\"].sum(\"ij\")``
            sums over both axes, returning a scalar (0‑dimensional) tensor.

        Returns
        -------
        MVLabeledTensor
            A new tensor with the summed axes removed.
        """
        sum_canon = _canonicalise(labels)
        sum_raw = _raw_names(sum_canon)
        self_raw = _raw_names(self.labels)

        # Validate that all sum labels exist on this tensor
        missing = set(sum_raw) - set(self_raw)
        if missing:
            raise ValueError(
                f"sum labels {missing} not found in tensor labels "
                f"'{self_raw}'"
            )

        # Determine which axes to keep and which to sum over
        sum_axes: list[int] = []
        keep_names: list[str] = []
        keep_modes: dict[str, str] = {}

        for ax, name in enumerate(self_raw):
            mode = _mode_at(self.labels, ax)
            if name in sum_raw:
                sum_axes.append(ax)
            else:
                keep_names.append(name)
                keep_modes[name] = mode

        # Perform the sum
        if not sum_axes:
            # Nothing to sum — return a copy
            from ._data import MVTensor as _MVTensor
            return MVLabeledTensor(
                _MVTensor(data=self.tensor.data.copy(), masks=self.tensor.masks),
                self.labels,
            )

        axis_tuple = tuple(sum_axes)
        new_data = np.sum(self.tensor.data, axis=axis_tuple)
        new_masks = tuple(
            self.tensor.masks[ax]
            for ax in range(self.ndim)
            if ax not in sum_axes
        )

        new_labels = _extended_from_raw("".join(keep_names), keep_modes)

        from ._data import MVTensor as _MVTensor

        return MVLabeledTensor(
            _MVTensor(data=new_data, masks=new_masks), new_labels
        )

    def norm(self, labels: str) -> MVLabeledTensor:
        """L2 norm over the given labelled axes.

        Computes :math:`\\sqrt{\\sum A^2}` element‑wise over the
        specified axes.

        Parameters
        ----------
        labels : str
            User label string identifying which axes to compute the
            norm over.  For example, ``A[\"ij\"].norm(\"j\")``
            returns a tensor with only label ``i`` where each entry
            is the L2 norm along axis ``j``.

        Returns
        -------
        MVLabeledTensor
            A new tensor with the normed axes removed.
        """
        squared = np.square(self.tensor.data)
        sum_canon = _canonicalise(labels)
        sum_raw = _raw_names(sum_canon)
        self_raw = _raw_names(self.labels)

        missing = set(sum_raw) - set(self_raw)
        if missing:
            raise ValueError(
                f"norm labels {missing} not found in tensor labels "
                f"'{self_raw}'"
            )

        sum_axes: list[int] = []
        keep_names: list[str] = []
        keep_modes: dict[str, str] = {}

        for ax, name in enumerate(self_raw):
            mode = _mode_at(self.labels, ax)
            if name in sum_raw:
                sum_axes.append(ax)
            else:
                keep_names.append(name)
                keep_modes[name] = mode

        if not sum_axes:
            from ._data import MVTensor as _MVTensor

            return MVLabeledTensor(
                _MVTensor(data=np.abs(self.tensor.data), masks=self.tensor.masks),
                self.labels,
            )

        summed = np.sum(squared, axis=tuple(sum_axes))
        new_data = np.sqrt(summed)
        new_masks = tuple(
            self.tensor.masks[ax]
            for ax in range(self.ndim)
            if ax not in sum_axes
        )

        new_labels = _extended_from_raw("".join(keep_names), keep_modes)

        from ._data import MVTensor as _MVTensor

        return MVLabeledTensor(
            _MVTensor(data=new_data, masks=new_masks), new_labels
        )

    # ------------------------------------------------------------------
    # Phase 4 – __mul__ (contraction)
    # ------------------------------------------------------------------

    def __mul__(self, other) -> MVLabeledTensor:
        """Label‑driven tensor contraction (like Einsum).

        ``G[\"kij\"] * A[\"i\"]`` contracts on shared label ``i``,
        producing a result with labels ``\"kj\"``.

        If *other* is a scalar (int/float), delegates to
        :meth:`mul_scalar`.
        """
        if isinstance(other, (int, float)):
            return self.mul_scalar(float(other))
        if not isinstance(other, MVLabeledTensor):
            return NotImplemented

        from .ops import contract_labeled

        return contract_labeled(self, other)

    def __rmul__(self, other) -> MVLabeledTensor:
        """Right‑multiplication: scalar * tensor."""
        if isinstance(other, (int, float)):
            return self.mul_scalar(float(other))
        return NotImplemented

    # ------------------------------------------------------------------
    # Phase 5 – __truediv__ / __rtruediv__
    # ------------------------------------------------------------------

    def __truediv__(self, other) -> MVLabeledTensor:
        """Division contraction: ``A[\"ij\"] / B[\"jk\"]``.

        Computes element‑wise reciprocal of *other* then multiplies.
        Scalar division delegates to :meth:`div_scalar` /
        :meth:`rdiv_scalar`.
        """
        if isinstance(other, (int, float)):
            return self.div_scalar(float(other))
        if not isinstance(other, MVLabeledTensor):
            return NotImplemented

        # Element‑wise reciprocal
        inv_data = 1.0 / other.tensor.data
        from ._data import MVTensor as _MVTensor

        inv_tensor = _MVTensor(data=inv_data, masks=other.tensor.masks)
        inv_labeled = MVLabeledTensor(inv_tensor, other.labels)
        return self.__mul__(inv_labeled)

    def __rtruediv__(self, other) -> MVLabeledTensor:
        """Right‑division: scalar / tensor."""
        if isinstance(other, (int, float)):
            return self.rdiv_scalar(float(other))
        return NotImplemented

    # ------------------------------------------------------------------
    # Phase 6 – __add__ / __sub__
    # ------------------------------------------------------------------

    def __add__(self, other) -> MVLabeledTensor:
        """Broadcast‑add two labeled tensors, aligning on shared labels.

        ``A[\"ij\"] + B[\"jk\"]`` → output ``\"ijk\"``.
        """
        if not isinstance(other, MVLabeledTensor):
            return NotImplemented
        return _add_or_sub(self, other, np.add)

    def __radd__(self, other) -> MVLabeledTensor:
        if isinstance(other, (int, float)) and other == 0:
            return self
        return NotImplemented

    def __sub__(self, other) -> MVLabeledTensor:
        """Broadcast‑subtract two labeled tensors."""
        if not isinstance(other, MVLabeledTensor):
            return NotImplemented
        return _add_or_sub(self, other, np.subtract)

    def __rsub__(self, other) -> MVLabeledTensor:
        if isinstance(other, (int, float)) and other == 0:
            return self.mul_scalar(-1.0)
        return NotImplemented


# ---------------------------------------------------------------------------
# Phase 6 helper – _add_or_sub
# ---------------------------------------------------------------------------


def _add_or_sub(
    a: MVLabeledTensor,
    b: MVLabeledTensor,
    op,
) -> MVLabeledTensor:
    """Broadcast addition/subtraction of two labeled tensors.

    Parameters
    ----------
    a, b : MVLabeledTensor
    op : callable
        ``np.add`` or ``np.subtract``.
    """
    raw_a = _raw_names(a.labels)
    raw_b = _raw_names(b.labels)

    # Check shared axes for compatibility
    shared = set(raw_a) & set(raw_b)
    for name in shared:
        ax_a = raw_a.index(name)
        ax_b = raw_b.index(name)
        mask_a = a.tensor.masks[ax_a]
        mask_b = b.tensor.masks[ax_b]
        if mask_a is not None and mask_b is not None:
            if mask_a.algebra is not mask_b.algebra:
                raise ValueError(f"label '{name}': algebra mismatch in +/−")
            if mask_a.ids != mask_b.ids:
                raise ValueError(f"label '{name}': mask ids differ in +/−")
        elif (mask_a is None) != (mask_b is None):
            raise ValueError(f"label '{name}': mask mismatch in +/−")
        if a.shape[ax_a] != b.shape[ax_b]:
            raise ValueError(
                f"label '{name}': shape mismatch "
                f"({a.shape[ax_a]} vs {b.shape[ax_b]}) in +/−"
            )

    # Build output raw names: a's raw names, then b's unique names
    output_raw = list(raw_a)
    for ch in raw_b:
        if ch not in output_raw:
            output_raw.append(ch)

    # Determine modes for output
    output_modes: dict[str, str] = {}
    for idx, ch in enumerate(raw_a):
        output_modes[ch] = _mode_at(a.labels, idx)
    for idx, ch in enumerate(raw_b):
        if ch not in output_modes:
            output_modes[ch] = _mode_at(b.labels, idx)
        else:
            # Shared name: _ wins if either is element‑wise
            mode_a = _mode_at(a.labels, raw_a.index(ch))
            mode_b = _mode_at(b.labels, raw_b.index(ch))
            output_modes[ch] = "_" if (mode_a == "_" or mode_b == "_") else "*"

    # Expand dims to broadcast
    n_out = len(output_raw)
    # Build a map from axis name → position in a/b
    a_pos = {raw_a[i]: i for i in range(len(raw_a))}
    b_pos = {raw_b[i]: i for i in range(len(raw_b))}

    # Expand a
    a_data = a.tensor.data
    a_masks = list(a.tensor.masks)
    for i, name in enumerate(output_raw):
        if name not in a_pos:
            a_data = np.expand_dims(a_data, i)
            a_masks.insert(i, None)
    # Reorder a axes to match output_raw order
    a_map = [a_pos.get(name, -1) for name in output_raw]
    # We just expand; the existing axes are already in raw_a order which
    # matches the front of output_raw, so no permutation is needed as
    # long as we inserted new axes at the right positions.

    # Expand b
    b_data = b.tensor.data
    b_masks_list = list(b.tensor.masks)
    for i, name in enumerate(output_raw):
        if name not in b_pos:
            b_data = np.expand_dims(b_data, i)
            b_masks_list.insert(i, None)

    # Apply operation
    result_data = op(a_data, b_data)

    # Build result masks
    result_masks: list[BladeMask | None] = []
    for name in output_raw:
        if name in a_pos:
            result_masks.append(a.tensor.masks[a_pos[name]])
        else:
            result_masks.append(b.tensor.masks[b_pos[name]])

    from ._data import MVTensor as _MVTensor

    return MVLabeledTensor(
        _MVTensor(data=result_data, masks=tuple(result_masks)),
        _extended_from_raw("".join(output_raw), output_modes),
    )


# ---------------------------------------------------------------------------
# 2.3 – Transpose helper
# ---------------------------------------------------------------------------

def _transpose(tensor: MVLabeledTensor, key: str) -> MVLabeledTensor:
    """Transpose/reorder axes according to ``\"src->dst\"`` key.

    Examples
    --------
    ``t[\"kij->jki\"]`` — explicit source and target labels.
    ``t[\"->jki\"]`` — infer source labels from *tensor*'s existing labels.
    ``t[\"ij->\"]`` — reverse: reorder tensor to match *dst* labels.
    """
    if "->" not in key:
        raise ValueError(f"transpose key must contain '->', got '{key}'")
    src_str, dst_str = key.split("->", 1)
    self_raw = _raw_names(tensor.labels)

    if src_str == "":
        # Infer source from tensor's existing labels
        src_raw = self_raw
    else:
        src_raw = _raw_names(_canonicalise(src_str))

    if dst_str == "":
        # Infer destination from tensor's existing labels
        dst_raw = self_raw
    else:
        dst_raw = _raw_names(_canonicalise(dst_str))

    if len(src_raw) != tensor.ndim:
        raise ValueError(
            f"source labels '{src_raw}' have {len(src_raw)} axes "
            f"but tensor has ndim={tensor.ndim}"
        )
    if set(src_raw) != set(self_raw):
        raise ValueError(
            f"source labels '{src_raw}' do not match tensor labels "
            f"'{self_raw}'"
        )
    if set(dst_raw) != set(src_raw):
        raise ValueError(
            f"target labels '{dst_raw}' must be a permutation of "
            f"source labels '{src_raw}'"
        )

    # Build the permutation: for each target name, find its source axis
    src_name_to_axis = {name: i for i, name in enumerate(src_raw)}
    axes = [src_name_to_axis[name] for name in dst_raw]

    new_data = np.transpose(tensor.tensor.data, axes)
    new_masks = tuple(tensor.tensor.masks[ax] for ax in axes)

    # Build new extended labels by permuting the modes
    src_modes = {self_raw[i]: _mode_at(tensor.labels, i) for i in range(tensor.ndim)}
    new_labels = _extended_from_raw(dst_raw, src_modes)

    from ._data import MVTensor as _MVTensor

    return MVLabeledTensor(
        _MVTensor(data=new_data, masks=new_masks), new_labels
    )


# ---------------------------------------------------------------------------
# 2.7 – iter_labels generator
# ---------------------------------------------------------------------------


def iter_labels(name: str, *tensors: MVLabeledTensor):
    """Iterate synchronously over *name* across all tensors.

    Yields ``MVLabeledTensor`` instances with the named axis removed.
    """
    axes: list[int] = []
    for t in tensors:
        raw = _raw_names(t.labels)
        if name not in raw:
            raise ValueError(
                f"label '{name}' not found in tensor with labels "
                f"'{t.labels}'"
            )
        axes.append(raw.index(name))

    length = tensors[0].tensor.shape[axes[0]]
    for t, ax in zip(tensors, axes):
        if t.tensor.shape[ax] != length:
            raise ValueError(
                f"label '{name}' has mismatched axis lengths across tensors"
            )

    from ._data import MVTensor as _MVTensor

    for i in range(length):
        slices: list[MVLabeledTensor] = []
        for t, ax in zip(tensors, axes):
            sliced_data = t.tensor.data.take(i, axis=ax)
            # Drop the iterated axis from masks
            sliced_masks = t.tensor.masks[:ax] + t.tensor.masks[ax + 1 :]
            # Drop the iterated label from the label string (2 chars per axis)
            sliced_labels = (
                t.labels[: 2 * ax] + t.labels[2 * ax + 2 :]
            )
            slices.append(
                MVLabeledTensor(
                    _MVTensor(data=sliced_data, masks=sliced_masks),
                    sliced_labels,
                )
            )
        yield tuple(slices) if len(slices) > 1 else slices[0]