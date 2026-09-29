# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for `ShapeFromPoints` protocol and `DragPreview`."""

from __future__ import annotations

from typing import Any

from pytanga.geometry import Point, Rectangle2D
from pytanga.viz import (
    ActCircle,
    ActEllipse,
    ActLine,
    ActPolygon,
    ActRectangle2D,
    DragPreview,
)


class _FakeHandle:
    """Minimal stand-in for ``VizSceneHandle`` (preview entity bookkeeping)."""

    def __init__(self) -> None:
        self.added: list[tuple[str, object]] = []
        self.updates: list[tuple[str, object]] = []
        self.removed: list[str] = []
        self._counter = 0

    def add(self, entity: Any, *, style: Any = None, **kwargs: Any) -> str:
        eid = f"e{self._counter}"
        self._counter += 1
        self.added.append((eid, entity))
        return eid

    def update_entity(self, object_id: str, entity: object) -> None:
        self.updates.append((object_id, entity))

    def remove(self, object_id: str) -> None:
        self.removed.append(object_id)

    def flush(self) -> None:
        pass


def test_composites_implement_create_from_points() -> None:
    for cls in (ActRectangle2D, ActEllipse, ActCircle, ActLine, ActPolygon):
        assert callable(cls.create_from_points)


def test_drag_preview_lifecycle() -> None:
    handle = _FakeHandle()
    preview = DragPreview(handle, factory=ActRectangle2D)

    preview.begin(Point(0.0, 0.0, 0.0))
    preview.update(Point(4.0, 2.0, 0.0))

    assert len(handle.added) == 1
    eid, entity = handle.added[0]
    assert isinstance(entity, Rectangle2D)
    assert entity.size == (4.0, 2.0)

    act = preview.finalize(Point(4.0, 2.0, 0.0))
    assert isinstance(act, ActRectangle2D)
    assert act.entity.size == (4.0, 2.0)
    assert handle.removed == [eid]
    assert preview.anchor is None


def test_drag_preview_update_reuses_entity() -> None:
    handle = _FakeHandle()
    preview = DragPreview(handle, factory=ActCircle)

    preview.begin(Point(1.0, 1.0, 0.0))
    preview.update(Point(2.0, 1.0, 0.0))
    preview.update(Point(3.0, 1.0, 0.0))

    assert len(handle.added) == 1
    assert len(handle.updates) == 1
    _, first = handle.added[0]
    assert first.radius == 1.0
    _, second = handle.updates[0]
    assert second.radius == 2.0


def test_drag_preview_discard() -> None:
    handle = _FakeHandle()
    preview = DragPreview(handle, factory=ActLine)

    preview.begin(Point(0.0, 0.0, 0.0))
    preview.update(Point(1.0, 0.0, 0.0))
    preview.discard()

    assert len(handle.removed) == 1
    assert preview.anchor is None
