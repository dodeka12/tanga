# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Single-letter label allocation for the expression system.

``MVLabeledTensor`` axes are named by single letters.  The expression layer
reserves two letters:

- ``OUT_LABEL``  — the output (result multivector) axis of every expression.
- ``BATCH_LABEL`` — the transient counting axis used when a variable is bound
  to a list of multivectors.

Each ``Variable`` receives a contiguous block of ``MAX_DEGREE`` letters from
the remaining 50 letters — one label per possible occurrence of the variable in
a product term (see the repeated-variables plan).
"""

from __future__ import annotations

OUT_LABEL = "k"
BATCH_LABEL = "n"

_VAR_ALPHABET = "".join(
    ch
    for ch in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if ch not in (OUT_LABEL, BATCH_LABEL)
)

# Maximum number of occurrences of a single variable in one product term.
MAX_DEGREE = 4

_counter = 0

# Maps every allocated variable label to its full block, so a label can be
# resolved back to (block, occurrence) when a variable repeats in a product.
_label_to_block: dict[str, tuple[str, ...]] = {}


def max_variables() -> int:
    """Return the maximum number of live variables the alphabet supports."""
    return len(_VAR_ALPHABET) // MAX_DEGREE


def allocate_block(size: int = MAX_DEGREE) -> tuple[str, ...]:
    """Return the next unused block of *size* contiguous variable labels.

    A block is assigned once per ``Variable``; ``labels[k]`` labels that
    variable's ``k``-th occurrence in a product.  Blocks are never reused.
    Raises ``RuntimeError`` once the alphabet cannot supply a full block.
    """
    global _counter
    if size < 1:
        raise ValueError(f"block size must be positive, got {size}")
    if _counter + size > len(_VAR_ALPHABET):
        raise RuntimeError(
            f"label alphabet exhausted: need {size} letters but only "
            f"{len(_VAR_ALPHABET) - _counter} remain"
        )
    block = tuple(_VAR_ALPHABET[_counter : _counter + size])
    _counter += size
    for ch in block:
        _label_to_block[ch] = block
    return block


def allocate_label() -> str:
    """Return a single variable label (backward-compatible shim).

    Kept for the single-label inverse path; prefer :func:`allocate_block`.
    """
    return allocate_block(1)[0]


def block_for_label(label: str) -> tuple[str, ...]:
    """Return the full label block containing *label*."""
    return _label_to_block[label]


def _reset_allocator() -> None:
    """Reset the label allocator (used by tests)."""
    global _counter
    _counter = 0
    _label_to_block.clear()
