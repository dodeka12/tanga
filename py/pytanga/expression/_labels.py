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

import sys

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

# Maps every allocated variable label (an integer) to its full block, so a
# label can be resolved back to (block, occurrence) when a variable repeats.
_label_to_block: dict[int, tuple[int, ...]] = {}


def max_variables() -> int:
    """Return the maximum number of live variables the integer pool supports.

    The pool is monotonic and effectively unbounded; this reports the largest
    practical count (``sys.maxsize // MAX_DEGREE``).
    """
    return sys.maxsize // MAX_DEGREE


def allocate_block(size: int = MAX_DEGREE) -> tuple[int, ...]:
    """Return the next unused block of *size* contiguous integer labels.

    A block is assigned once per ``Variable``; ``labels[k]`` labels that
    variable's ``k``-th occurrence in a product.  Blocks are never reused.
    """
    global _counter
    if size < 1:
        raise ValueError(f"block size must be positive, got {size}")
    block = tuple(range(_counter, _counter + size))
    _counter += size
    for lab in block:
        _label_to_block[lab] = block
    return block


def allocate_label() -> int:
    """Return a single variable label (backward-compatible shim).

    Kept for the single-label inverse path; prefer :func:`allocate_block`.
    """
    return allocate_block(1)[0]


def block_for_label(label: int) -> tuple[int, ...]:
    """Return the full label block containing *label*."""
    return _label_to_block[label]


def _reset_allocator() -> None:
    """Reset the label allocator (used by tests)."""
    global _counter
    _counter = 0
    _label_to_block.clear()
