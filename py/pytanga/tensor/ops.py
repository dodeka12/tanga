# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
"""pytanga.tensor.ops — tensor operations including einsum‑like contraction."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from pytanga.blade_mask import BladeMask
from . import MVTensor

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


def _check_masks_compatible(
    mask_a: BladeMask | None, mask_b: BladeMask | None
) -> bool:
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
            raise ValueError(
                f"output label '{ch}' does not appear in any input"
            )
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
) -> tuple[str, list[str], dict[str, str]]:
    """Build an einsum subscript from labeled tensors.

    Given one or more ``MVLabeledTensor`` instances, analyzes their
    labels to determine which axes are contracted (shared, both ``*``),
    which are element‑wise (shared, at least one ``_``), and which are
    unique to a single tensor.  Returns the full subscript string, the
    ordered raw names of the output axes, and a dict mapping each output
    raw name to its mode.

    Parameters
    ----------
    *labeled_tensors : MVLabeledTensor
        The labeled tensors participating in the operation.

    Returns
    -------
    subscripts : str
        The full einsum subscript, e.g. ``"kij,in,jn->kn"``.
    output_raw : list[str]
        Raw names of the output axes, in order.
    output_modes : dict[str, str]
        Maps each output raw name to its mode (``'*'`` or ``'_'``).
    """
    from ._labeled import _raw_names, _is_elemwise

    n_tensors = len(labeled_tensors)
    if n_tensors == 0:
        raise ValueError("need at least one labeled tensor")

    # Gather raw names and mode maps for each tensor
    all_raw: list[str] = []
    all_modes: list[dict[str, str]] = []
    all_ndim = [t.ndim for t in labeled_tensors]
    all_labels = [t.labels for t in labeled_tensors]

    for t in labeled_tensors:
        raw = _raw_names(t.labels)
        modes = {}
        for a in range(t.ndim):
            name = raw[a]
            modes[name] = "_" if _is_elemwise(t.labels, a) else "*"
        all_raw.append(raw)
        all_modes.append(modes)

    # Count occurrences of each raw name
    name_occurrences: dict[str, int] = {}
    for raw in all_raw:
        for ch in raw:
            name_occurrences[ch] = name_occurrences.get(ch, 0) + 1

    # Determine contracted names:
    # A name is contracted if it appears in ≥2 tensors AND all occurrences
    # are contractible (mode '*').  If any occurrence is '_', it becomes
    # an element‑wise axis and stays in the output.
    contracted: set[str] = set()
    elemwise_shared: set[str] = set()
    for name, count in name_occurrences.items():
        if count >= 2:
            # Check if all occurrences are contractible
            all_contractible = True
            for modes in all_modes:
                if name in modes and modes[name] != "*":
                    all_contractible = False
                    break
            if all_contractible:
                contracted.add(name)
            else:
                elemwise_shared.add(name)

    # Build output raw names:
    # 1) Contractible (non‑shared + shared‑but‑element‑wise‑only) — '*'
    # 2) Element‑wise ('_') names
    #
    # Within each group, names keep their order of first appearance
    # across the tensors.
    output_contractible: list[str] = []
    output_elemwise: list[str] = []
    output_modes: dict[str, str] = {}
    seen_in_output: set[str] = set()

    for idx, raw in enumerate(all_raw):
        for ch in raw:
            if ch in contracted:
                continue
            if ch in seen_in_output:
                continue
            seen_in_output.add(ch)
            if ch in elemwise_shared:
                mode = "_"
            else:
                mode = all_modes[idx][ch]
            output_modes[ch] = mode
            if mode == "_":
                output_elemwise.append(ch)
            else:
                output_contractible.append(ch)

    output_raw = output_contractible + output_elemwise

    # Build input label strings (just raw names)
    input_labels = ",".join(raw for raw in all_raw)
    output_str = "".join(output_raw)
    subscripts = f"{input_labels}->{output_str}"

    return subscripts, output_raw, output_modes


def contract_labeled(*labeled_tensors: MVLabeledTensor, **kwargs) -> MVLabeledTensor:
    """Contract labeled tensors using their labels to build the subscript.

    Parameters
    ----------
    *labeled_tensors : MVLabeledTensor
        The labeled tensors to contract.
    **kwargs
        Passed through to :func:`contract`.

    Returns
    -------
    MVLabeledTensor
        The contracted result with inferred labels.
    """
    from ._labeled import _extended_from_raw

    subscripts, output_raw, output_modes = _build_subscript(*labeled_tensors)

    # Extract the underlying MVTensors
    tensors = [t.tensor for t in labeled_tensors]
    result = contract(subscripts, *tensors, **kwargs)

    # Build output label string (may be empty for scalar result)
    out_labels = _extended_from_raw("".join(output_raw), output_modes)
    from ._labeled import MVLabeledTensor as _MVLabeledTensor

    if out_labels == "":
        # Scalar result — wrap in MVLabeledTensor with empty labels
        return _MVLabeledTensor(result, "")
    return _MVLabeledTensor(result, out_labels)
