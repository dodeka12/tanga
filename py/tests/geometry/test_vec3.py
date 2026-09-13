# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the fundamental :class:`Vec3` vector type."""

import pytest

from pytanga.entity import Direction, Point, Vec3


def test_add():  # noqa: ANN201
    assert Vec3(1, 2, 3) + Vec3(4, 5, 6) == Vec3(5, 7, 9)


def test_sub():  # noqa: ANN201
    assert Vec3(1, 2, 3) - Vec3(4, 5, 6) == Vec3(-3, -3, -3)


def test_neg():  # noqa: ANN201
    assert -Vec3(1, 2, 3) == Vec3(-1, -2, -3)


def test_scalar_mul():  # noqa: ANN201
    assert Vec3(1, 2, 3) * 2 == Vec3(2, 4, 6)
    assert 2 * Vec3(1, 2, 3) == Vec3(2, 4, 6)


def test_element_wise_mul():  # noqa: ANN201
    assert Vec3(1, 2, 3) * Vec3(4, 5, 6) == Vec3(4, 10, 18)
    assert Vec3(1, 2, 3).elem_mul(Vec3(4, 5, 6)) == Vec3(4, 10, 18)


def test_truediv():  # noqa: ANN201
    assert Vec3(2, 4, 6) / 2 == Vec3(1, 2, 3)


def test_dot():  # noqa: ANN201
    assert Vec3(1, 2, 3).dot(Vec3(4, 5, 6)) == 32


def test_cross():  # noqa: ANN201
    assert Vec3(1, 2, 3).cross(Vec3(4, 5, 6)) == Vec3(-3, 6, -3)


def test_mag():  # noqa: ANN201
    assert Vec3(3, 4, 0).mag() == 5.0


def test_normalized():  # noqa: ANN201
    assert Vec3(3, 0, 0).normalized() == Vec3(1, 0, 0)


def test_normalized_zero_raises():  # noqa: ANN201
    with pytest.raises(ValueError):
        Vec3(0, 0, 0).normalized()


def test_to_point():  # noqa: ANN201
    assert Vec3(1, 2, 3).to_point() == Point(1, 2, 3)


def test_to_direction():  # noqa: ANN201
    assert Vec3(1, 2, 3).to_direction() == Direction(1, 2, 3)


def test_from_point():  # noqa: ANN201
    assert Vec3.from_point(Point(1, 2, 3)) == Vec3(1, 2, 3)


def test_from_direction():  # noqa: ANN201
    assert Vec3.from_direction(Direction(1, 2, 3)) == Vec3(1, 2, 3)


def test_equality():  # noqa: ANN201
    assert Vec3(1, 2, 3) == Vec3(1, 2, 3)
    assert Vec3(1, 2, 3) != Vec3(1, 2, 4)
