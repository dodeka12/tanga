# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""The :class:`SplitView` draggable-splitter container."""

from __future__ import annotations

from typing import Any

from ._base import View
from ._enums import EOrientation
from ._helpers import _size_dict
from .._size import Size, SizeSpec


class SplitView(View):
    """A container that lays its children out along one axis.

    A split has no intrinsic size on the axis perpendicular to its layout axis
    (its children are positioned absolutely), so it defaults
    ``preferred_width``/``preferred_height`` to ``Size.fr(1)``.  This makes a
    split fill the leftover space when it is a child of a flow container
    (``StackView`` / ``GroupView`` / ``ToolbarView``) instead of collapsing to
    zero.  ``fr`` is inert elsewhere — a root layout is forced to fill its
    container and an enclosing ``SplitView`` resolves ``fr`` to a natural size —
    so the default only affects the flow case.  Pass an explicit
    ``preferred_width`` / ``preferred_height`` (or ``size``) to override.
    """

    _node_type = "split"

    def __init__(
        self,
        orientation: EOrientation | str,
        children: list[View] | None = None,
        *,
        movable: bool | None = None,
        sizes: list[SizeSpec] | None = None,
        size: SizeSpec = None,
        preferred_width: SizeSpec = None,
        preferred_height: SizeSpec = None,
        min_width: SizeSpec = None,
        min_height: SizeSpec = None,
        max_width: SizeSpec = None,
        max_height: SizeSpec = None,
    ) -> None:
        super().__init__(
            size=size,
            preferred_width=preferred_width,
            preferred_height=preferred_height,
            min_width=min_width,
            min_height=min_height,
            max_width=max_width,
            max_height=max_height,
        )
        if self.preferred_width is None:
            self.preferred_width = Size.fr(1)
        if self.preferred_height is None:
            self.preferred_height = Size.fr(1)
        self.orientation = EOrientation(orientation)
        self.children = list(children or [])
        self.movable = movable
        self.sizes = sizes
        if len(self.children) < 2:
            raise ValueError("SplitView requires at least 2 children")
        if self.sizes is not None and len(self.sizes) != len(self.children):
            raise ValueError(
                f"sizes must match children ({len(self.sizes)} != {len(self.children)})"
            )

    def _serialize(self) -> dict[str, Any]:
        result = super()._serialize()
        result["orientation"] = self.orientation.value
        result["movable"] = self.movable
        result["sizes"] = (
            [_size_dict(s) for s in self.sizes]
            if self.sizes is not None
            else [None] * len(self.children)
        )
        result["children"] = [child._serialize() for child in self.children]
        return result
