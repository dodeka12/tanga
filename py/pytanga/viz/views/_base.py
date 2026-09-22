# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""The base :class:`View` node for every layout pane and container."""

from __future__ import annotations

from typing import Any

from ._helpers import _size_dict, _view_counter
from .._size import SizeSpec


class View:
    """Base for every pane/container in a layout. Split-agnostic.

    Exposes per-axis preferred/min/max sizes.  ``fixed_x``/``fixed_y`` are
    computed (``min == max``) and are what a container uses to decide whether a
    splitter next to this view is draggable.
    """

    _node_type = "view"

    def __init__(
        self,
        *,
        id: str | None = None,
        size: SizeSpec = None,
        preferred_width: SizeSpec = None,
        preferred_height: SizeSpec = None,
        min_width: SizeSpec = None,
        min_height: SizeSpec = None,
        max_width: SizeSpec = None,
        max_height: SizeSpec = None,
    ) -> None:
        self.id = id if id is not None else f"v{next(_view_counter)}"
        if size is not None:
            if preferred_width is None:
                preferred_width = size
            if preferred_height is None:
                preferred_height = size
        self.preferred_width = preferred_width
        self.preferred_height = preferred_height
        self.min_width = min_width
        self.min_height = min_height
        self.max_width = max_width
        self.max_height = max_height

    @property
    def fixed_x(self) -> bool:
        """True when the width is pinned (``min_width == max_width``)."""
        return (
            self.min_width is not None
            and self.max_width is not None
            and self.min_width == self.max_width
        )

    @property
    def fixed_y(self) -> bool:
        """True when the height is pinned (``min_height == max_height``)."""
        return (
            self.min_height is not None
            and self.max_height is not None
            and self.min_height == self.max_height
        )

    def _serialize(self) -> dict[str, Any]:
        """Serialize this node (subclasses append their type-specific fields)."""
        return {
            "type": self._node_type,
            "id": self.id,
            "min_width": _size_dict(self.min_width),
            "max_width": _size_dict(self.max_width),
            "min_height": _size_dict(self.min_height),
            "max_height": _size_dict(self.max_height),
            "preferred_width": _size_dict(self.preferred_width),
            "preferred_height": _size_dict(self.preferred_height),
        }
