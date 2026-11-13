# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for `PointPath` per-segment color overrides."""

from __future__ import annotations

import pytest

from pytanga.viz._point_path import PointPath
from pytanga.viz.scene import Scene


def test_segment_colors_default_empty() -> None:
    path = PointPath()
    assert path.segment_colors == []
    path.add((0.0, 0.0, 0.0))
    assert path.segment_colors == []
    path.add((1.0, 0.0, 0.0))
    assert path.segment_colors == [None]


def test_set_segment_colors_round_trip() -> None:
    path = PointPath()
    for p in ((0, 0, 0), (1, 0, 0), (1, 1, 0)):
        path.add(p)
    path.set_segment_colors(["#ff0000", "#0000ff"])
    assert path.segment_colors == ["#ff0000", "#0000ff"]


def test_set_segment_colors_wrong_length_raises() -> None:
    path = PointPath()
    path.add((0.0, 0.0, 0.0))
    path.add((1.0, 0.0, 0.0))
    with pytest.raises(ValueError):
        path.set_segment_colors(["#ff0000", "#00ff00"])


def test_set_segment_color_validates_index() -> None:
    path = PointPath()
    path.add((0.0, 0.0, 0.0))
    path.add((1.0, 0.0, 0.0))
    with pytest.raises(IndexError):
        path.set_segment_color(1, "#ff0000")
    path.set_segment_color(0, "#ff0000")
    assert path.segment_colors == ["#ff0000"]


def test_add_appends_none_segment_color() -> None:
    path = PointPath()
    path.add((0.0, 0.0, 0.0))
    path.add((1.0, 0.0, 0.0))
    path.set_segment_color(0, "#ff0000")
    path.add((2.0, 0.0, 0.0))
    assert path.segment_colors == ["#ff0000", None]


def test_max_points_pop_shifts_segment_colors() -> None:
    path = PointPath(max_points=3)
    for p in ((0, 0, 0), (1, 0, 0), (2, 0, 0)):
        path.add(p)
    path.set_segment_colors(["#ff0000", "#00ff00"])
    # Appending a fourth point pops the oldest; the first segment color shifts out.
    path.add((3.0, 0.0, 0.0))
    assert path.segment_colors == ["#00ff00", None]


def test_serialize_emits_empty_segment_colors_when_uniform() -> None:
    path = PointPath()
    path.add((0.0, 0.0, 0.0))
    path.add((1.0, 0.0, 0.0))
    s = Scene()
    eid = s.add(path)
    assert s.get_node(eid).serialize()["segmentColors"] == []


def test_serialize_clearing_the_last_segment_color_keeps_the_key() -> None:
    # Regression: a path that goes coloured → uniform must still emit
    # `segmentColors` (as `[]`) so the frontend merge can't hold on to the
    # stale, previously-coloured list.
    path = PointPath()
    path.add((0.0, 0.0, 0.0))
    path.add((1.0, 0.0, 0.0))
    path.add((1.0, 1.0, 0.0))
    s = Scene()
    eid = s.add(path)

    path.set_segment_colors(["#ff00ff", None])
    assert s.get_node(eid).serialize()["segmentColors"] == ["#ff00ff", None]

    path.set_segment_colors([None, None])
    assert s.get_node(eid).serialize()["segmentColors"] == []


def test_serialize_emits_segment_colors_when_set() -> None:
    path = PointPath()
    path.add((0.0, 0.0, 0.0))
    path.add((1.0, 0.0, 0.0))
    path.add((1.0, 1.0, 0.0))
    path.set_segment_colors(["#ff00ff", None])
    s = Scene()
    eid = s.add(path)
    assert s.get_node(eid).serialize()["segmentColors"] == ["#ff00ff", None]
