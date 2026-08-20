# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the expression label allocator."""

import pytest

from pytanga.expression._labels import (
    BATCH_LABEL,
    MAX_DEGREE,
    OUT_LABEL,
    _VAR_ALPHABET,
    _reset_allocator,
    allocate_block,
    allocate_label,
    max_variables,
)


class TestLabelAllocator:
    def test_blocks_unique_and_stable(self):
        _reset_allocator()
        first = allocate_block()
        second = allocate_block()
        assert first != second
        assert len(first) == MAX_DEGREE == len(second)

    def test_blocks_are_contiguous(self):
        _reset_allocator()
        block = allocate_block()
        base = _VAR_ALPHABET.index(block[0])
        assert block == tuple(_VAR_ALPHABET[base : base + MAX_DEGREE])

    def test_single_label_shim(self):
        _reset_allocator()
        assert allocate_label() == _VAR_ALPHABET[0]

    def test_reserved_labels_never_assigned(self):
        _reset_allocator()
        labels = [ch for _ in range(max_variables()) for ch in allocate_block()]
        assert OUT_LABEL not in labels
        assert BATCH_LABEL not in labels
        assert len(set(labels)) == len(labels)

    def test_exhaustion(self):
        _reset_allocator()
        for _ in range(max_variables()):
            allocate_block()
        with pytest.raises(RuntimeError):
            allocate_block()
