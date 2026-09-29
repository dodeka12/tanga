# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Drag-to-create preview helper and the ``ShapeFromPoints`` protocol.

A :class:`DragPreview` drives the transient-entity lifecycle for any factory
implementing :class:`ShapeFromPoints` — the composites' ``create_from_points``
classmethods.  During a drag it renders the factory's body entity as a preview;
on finalize it returns the finished composite for the caller to add.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

from pytanga.geometry import Point

if TYPE_CHECKING:
    from ._active import ActSceneObject
    from ._scene_handle import VizSceneHandle


class ShapeFromPoints(Protocol):
    """Anything that can build an ``Act`` composite from two anchor points.

    The two points are interpreted per shape: opposite corners for
    ``ActRectangle2D``/``ActEllipse``, center + rim for ``ActCircle``, and
    segment endpoints for ``ActLine``/``ActPolygon``.
    """

    @classmethod
    def create_from_points(
        cls, a: Point, b: Point, **kwargs: Any
    ) -> "ActSceneObject": ...


class DragPreview:
    """Drives a drag-to-create preview for a :class:`ShapeFromPoints` factory.

    The transient preview entity is the factory's ``entity``, so the preview
    and the finalized shape always agree on clamps/defaults.

    Args:
        handle: The scene handle the preview entity is added to.
        factory: A class implementing ``create_from_points(a, b, **kwargs)``.
        style: Body style applied to the transient preview entity.
    """

    def __init__(
        self,
        handle: "VizSceneHandle",
        *,
        factory: type[ShapeFromPoints],
        style: Any = None,
        factory_kwargs: dict[str, Any] | None = None,
    ) -> None:
        self._handle = handle
        self._factory = factory
        self._style = style
        self._factory_kwargs = factory_kwargs or {}
        self._anchor: Point | None = None
        self._preview_id: str | None = None

    @property
    def anchor(self) -> Point | None:
        """The drag anchor point, or ``None`` before :meth:`begin`."""
        return self._anchor

    def begin(self, anchor: Point) -> None:
        """Record the drag anchor."""
        self._anchor = anchor

    def update(self, pos: Point) -> None:
        """Add/update the transient preview entity for ``(anchor, pos)``."""
        if self._anchor is None:
            return
        entity = self._factory.create_from_points(
            self._anchor, pos, **self._factory_kwargs
        ).entity
        if self._preview_id is None:
            self._preview_id = self._handle.add(entity, style=self._style)
        else:
            self._handle.update_entity(self._preview_id, entity)
        self._handle.flush()

    def finalize(self, pos: Point) -> "ActSceneObject":
        """Discard the preview and return the finished composite."""
        anchor = self._anchor
        self.discard()
        assert anchor is not None
        return self._factory.create_from_points(anchor, pos, **self._factory_kwargs)

    def discard(self) -> None:
        """Remove the transient preview entity and clear the anchor."""
        if self._preview_id is not None:
            self._handle.remove(self._preview_id)
            self._preview_id = None
        self._anchor = None
