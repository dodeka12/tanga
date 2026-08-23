# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the SDF viewer's shader-drawn overlays."""

from __future__ import annotations

import pytest

from pytanga.viz.sdf.overlay import Grid, SdfOverlay, serialize_overlay


def test_grid_normalizes_directions() -> None:
    grid = Grid(dir_u=(0.0, 2.0, 0.0), dir_v=(0.0, 0.0, 3.0))
    assert grid.dir_u == (0.0, 1.0, 0.0)
    assert grid.dir_v == (0.0, 0.0, 1.0)


def test_grid_is_an_overlay() -> None:
    assert isinstance(Grid(), SdfOverlay)


def test_grid_intervals_are_positive() -> None:
    grid = Grid(interval_u=-2.0, interval_v=0.0)
    assert grid.interval_u == 2.0
    assert grid.interval_v == pytest.approx(1e-4)


def test_serialize_overlay() -> None:
    grid = Grid(
        origin=(1, 2, 3),
        dir_u=(1, 0, 0),
        dir_v=(0, 0, 1),
        interval_u=0.5,
        interval_v=2.0,
        color="#ff0000",
        opacity=0.8,
    )
    assert serialize_overlay(grid) == {
        "kind": "grid",
        "origin": [1.0, 2.0, 3.0],
        "dir_u": [1.0, 0.0, 0.0],
        "dir_v": [0.0, 0.0, 1.0],
        "interval_u": 0.5,
        "interval_v": 2.0,
        "color": "#ff0000",
        "opacity": 0.8,
    }


def test_serialize_overlay_rejects_unknown() -> None:
    with pytest.raises(TypeError):
        serialize_overlay(object())  # type: ignore[arg-type]
