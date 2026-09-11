# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
"""pytanga.tensor.ops — tensor operations including einsum‑like contraction."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from pytanga.blade_mask import BladeMask
from . import MVTensor
from ._labeled import AxisName

if TYPE_CHECKING:
    from ._labeled import MVLabeledTensor


def _parse_subscripts(subscripts: str, n_tensors: int) -> tuple[list[str], str]:
    """Split 'kij,i,j->k' into (['kij','i','j'], 'k')."""
    if "->" not in subscripts:
        raise ValueError("contract subscripts must contain '->'")
    inputs_str, output_str = subscripts.split("->")
    input_labels = [s.strip() for s in inputs_str.split(",")]
    if len(input_labels) != n_tensors:
        raise ValueError(
            f"subscript has {len(input_labels)} input terms but "
            f"{n_tensors} tensors given"
        )
    return input_labels, output_str.strip()


def _check_masks_compatible(mask_a: BladeMask | None, mask_b: BladeMask | None) -> bool:
    """Check that two masks are compatible for the same subscript label."""
    if mask_a is None and mask_b is None:
        return True
    if mask_a is None or mask_b is None:
        return False
    return (mask_a.algebra is mask_b.algebra) and (mask_a.ids == mask_b.ids)


def contract(subscripts: str, *tensors: MVTensor, **kwargs) -> MVTensor:
    """Contract MVTensor instances using an einsum‑like subscript.

    This is a wrapper around :func:`numpy.einsum` that additionally
    validates and propagates blade masks.  For each output axis label,
    the mask is inherited from the input axis that carries that label.
    If a label appears on multiple input axes (a contraction), those
    axes must have compatible masks.

    Parameters
    ----------
    subscripts : str
        Einsum subscript, e.g. ``"kij,i,j->k"``.
    *tensors : MVTensor
        The tensors to contract.
    **kwargs
        Passed through to ``numpy.einsum`` (e.g. ``optimize``).

    Returns
    -------
    MVTensor
        The contracted result with inferred masks.

    Examples
    --------
    GP of two single‑MV tensors via a product tensor::

        C = contract("kij,i,j->k", O, A, B)

    Batch GP of list‑of‑MV tensors::

        C = contract("kij,in,jn->kn", O, A, B)
    """
    input_labels, output_labels = _parse_subscripts(subscripts, len(tensors))

    # --- validate each input label has the right number of axes ----------
    for i, (lbl, ten) in enumerate(zip(input_labels, tensors)):
        if len(lbl) != ten.data.ndim:
            raise ValueError(
                f"tensor {i}: subscript '{lbl}' has {len(lbl)} axes "
                f"but tensor has {ten.data.ndim} dimensions"
            )

    # --- build per‑label mask registry -----------------------------------
    # registry[label] = (tensor_idx, axis_idx_within_tensor, mask)
    registry: dict[str, tuple[int, int, BladeMask | None]] = {}
    for i, (lbl, ten) in enumerate(zip(input_labels, tensors)):
        for a, ch in enumerate(lbl):
            mask = ten.masks[a]
            if ch in registry:
                _, _, existing = registry[ch]
                if not _check_masks_compatible(existing, mask):
                    raise ValueError(
                        f"label '{ch}' appears on incompatible masks: "
                        f"{existing} vs {mask}"
                    )
            else:
                registry[ch] = (i, a, mask)

    # --- build output masks ----------------------------------------------
    out_masks: list[BladeMask | None] = []
    for ch in output_labels:
        if ch not in registry:
            raise ValueError(f"output label '{ch}' does not appear in any input")
        _, _, mask = registry[ch]
        out_masks.append(mask)

    # --- delegate to numpy -----------------------------------------------
    data_arrays = [t.data for t in tensors]
    result_data = np.einsum(subscripts, *data_arrays, **kwargs)

    return MVTensor(data=result_data, masks=tuple(out_masks))


# ---------------------------------------------------------------------------
# Phase 3 – _build_subscript & contract_labeled
# ---------------------------------------------------------------------------


def _build_subscript(
    *labeled_tensors: MVLabeledTensor,
) -> tuple[list[list[int]], list[int], list[AxisName], dict[AxisName, str]]:
    """Build a list-form einsum layout for labeled tensors.

    Given one or more ``MVLabeledTensor`` instances, determines which axes
    are contracted (shared, all ``"*"``), which are element-wise shared, and
    which are unique, and assigns each distinct axis name a small integer
    label.  Returns the per-tensor integer axis lists, the output integer
    axis list, the ordered output names, and a name→mode map for the output.

    Parameters
    ----------
    *labeled_tensors : MVLabeledTensor
        The labeled tensors participating in the contraction.

    Returns
    -------
    input_axes : list[list[int]]
        Integer axis-label list for each input tensor.
    output_axes : list[int]
        Integer axis labels kept in the output.
    output_names : list[AxisName]
        Ordered output axis names.
    output_modes : dict[AxisName, str]
        Maps each output name to ``"*"`` or ``"_"``.
    """
    from ._labeled import _axis_names, _axis_modes

    if not labeled_tensors:
        raise ValueError("need at least one labeled tensor")

    all_names = [_axis_names(t.labels) for t in labeled_tensors]
    all_modes = [_axis_modes(t.labels) for t in labeled_tensors]

    name_to_label: dict[AxisName, int] = {}
    for names in all_names:
        for name in names:
            if name not in name_to_label:
                name_to_label[name] = len(name_to_label)

    occurrences: dict[AxisName, int] = {}
    any_elemwise: dict[AxisName, bool] = {}
    unique_mode: dict[AxisName, str] = {}
    for names, modes in zip(all_names, all_modes):
        for name, mode in zip(names, modes):
            occurrences[name] = occurrences.get(name, 0) + 1
            any_elemwise[name] = any_elemwise.get(name, False) or (mode == "_")
            unique_mode[name] = mode

    contracted = {
        name
        for name, count in occurrences.items()
        if count >= 2 and not any_elemwise[name]
    }
    elemwise_shared = {
        name for name, count in occurrences.items() if count >= 2 and any_elemwise[name]
    }

    output_contractible: list[AxisName] = []
    output_elemwise: list[AxisName] = []
    output_modes: dict[AxisName, str] = {}
    seen: set[AxisName] = set()
    for names in all_names:
        for name in names:
            if name in contracted or name in seen:
                continue
            seen.add(name)
            mode = "_" if name in elemwise_shared else unique_mode[name]
            output_modes[name] = mode
            if mode == "_":
                output_elemwise.append(name)
            else:
                output_contractible.append(name)

    output_names = output_contractible + output_elemwise

    input_axes = [[name_to_label[name] for name in names] for names in all_names]
    output_axes = [name_to_label[name] for name in output_names]

    return input_axes, output_axes, output_names, output_modes


def contract_labeled(*labeled_tensors: MVLabeledTensor, **kwargs) -> MVLabeledTensor:
    """Contract labeled tensors using their labels to build the einsum call.

    Uses ``numpy.einsum``'s list form so axis names may be strings or
    integers (no 52-letter ceiling).

    Parameters
    ----------
    *labeled_tensors : MVLabeledTensor
        The labeled tensors to contract.
    **kwargs
        Passed through to ``numpy.einsum`` (e.g. ``optimize``).

    Returns
    -------
    MVLabeledTensor
        The contracted result with inferred labels.
    """
    from ._labeled import _axis_names, _labels_from_names
    from ._labeled import MVLabeledTensor as _MVLabeledTensor

    input_axes, output_axes, output_names, output_modes = _build_subscript(
        *labeled_tensors
    )

    tensors = [t.tensor for t in labeled_tensors]
    all_names = [_axis_names(t.labels) for t in labeled_tensors]

    # Validate mask compatibility for shared labels and record output masks.
    name_to_mask: dict[AxisName, BladeMask | None] = {}
    for names, t in zip(all_names, labeled_tensors):
        for name, mask in zip(names, t.tensor.masks):
            if name in name_to_mask:
                if not _check_masks_compatible(name_to_mask[name], mask):
                    raise ValueError(
                        f"label {name!r} appears on incompatible masks: "
                        f"{name_to_mask[name]} vs {mask}"
                    )
            else:
                name_to_mask[name] = mask

    result_masks = tuple(name_to_mask[name] for name in output_names)

    einsum_args: list = []
    for data, axes in zip((t.data for t in tensors), input_axes):
        einsum_args.append(data)
        einsum_args.append(axes)
    einsum_args.append(output_axes)

    result_data = np.einsum(*einsum_args, **kwargs)

    from ._data import MVTensor as _MVTensor

    result = _MVTensor(data=result_data, masks=result_masks)
    return _MVLabeledTensor(result, _labels_from_names(output_names, output_modes))
