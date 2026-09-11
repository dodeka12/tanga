# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the expression label allocator (integer pool)."""

from pytanga.expression._labels import (
    MAX_DEGREE,
    _reset_allocator,
    allocate_block,
    allocate_label,
    block_for_label,
    max_variables,
)


class TestLabelAllocator:
    def test_blocks_unique_and_stable(self):
        _reset_allocator()
        first = allocate_block()
        second = allocate_block()
        assert first != second
        assert len(first) == MAX_DEGREE == len(second)
        assert all(isinstance(x, int) for x in first + second)

    def test_blocks_are_contiguous(self):
        _reset_allocator()
        block = allocate_block()
        assert block == tuple(range(block[0], block[0] + MAX_DEGREE))

    def test_single_label_shim(self):
        _reset_allocator()
        assert allocate_label() == 0

    def test_labels_are_unique(self):
        _reset_allocator()
        labels = [ch for _ in range(100) for ch in allocate_block()]
        assert len(set(labels)) == len(labels)

    def test_block_for_label(self):
        _reset_allocator()
        first = allocate_block()
        second = allocate_block()
        assert block_for_label(first[0]) == first
        assert block_for_label(second[0]) == second

    def test_no_exhaustion(self):
        _reset_allocator()
        for _ in range(1000):
            allocate_block()
        assert max_variables() > 1000
