# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the fundamental :class:`Vec3` vector type."""

import pytest

from pytanga.entity import Direction, Point, Vec3


def test_add():
    assert Vec3(1, 2, 3) + Vec3(4, 5, 6) == Vec3(5, 7, 9)


def test_sub():
    assert Vec3(1, 2, 3) - Vec3(4, 5, 6) == Vec3(-3, -3, -3)


def test_neg():
    assert -Vec3(1, 2, 3) == Vec3(-1, -2, -3)


def test_scalar_mul():
    assert Vec3(1, 2, 3) * 2 == Vec3(2, 4, 6)
    assert 2 * Vec3(1, 2, 3) == Vec3(2, 4, 6)


def test_element_wise_mul():
    assert Vec3(1, 2, 3) * Vec3(4, 5, 6) == Vec3(4, 10, 18)
    assert Vec3(1, 2, 3).elem_mul(Vec3(4, 5, 6)) == Vec3(4, 10, 18)


def test_truediv():
    assert Vec3(2, 4, 6) / 2 == Vec3(1, 2, 3)


def test_dot():
    assert Vec3(1, 2, 3).dot(Vec3(4, 5, 6)) == 32


def test_cross():
    assert Vec3(1, 2, 3).cross(Vec3(4, 5, 6)) == Vec3(-3, 6, -3)


def test_mag():
    assert Vec3(3, 4, 0).mag() == 5.0


def test_normalized():
    assert Vec3(3, 0, 0).normalized() == Vec3(1, 0, 0)


def test_normalized_zero_raises():
    with pytest.raises(ValueError):
        Vec3(0, 0, 0).normalized()


def test_to_point():
    assert Vec3(1, 2, 3).to_point() == Point(1, 2, 3)


def test_to_direction():
    assert Vec3(1, 2, 3).to_direction() == Direction(1, 2, 3)


def test_from_point():
    assert Vec3.from_point(Point(1, 2, 3)) == Vec3(1, 2, 3)


def test_from_direction():
    assert Vec3.from_direction(Direction(1, 2, 3)) == Vec3(1, 2, 3)


def test_equality():
    assert Vec3(1, 2, 3) == Vec3(1, 2, 3)
    assert Vec3(1, 2, 3) != Vec3(1, 2, 4)
