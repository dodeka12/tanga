# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""The :class:`GroupView` titled stack container."""

from __future__ import annotations

from typing import Any

from .._anchor import EAnchor
from ._base import View
from ._enums import EStackAlign, EStackDirection, EStackJustify
from .._icons import Icon
from .._size import SizeSpec
from .stack_view import StackView


class GroupView(StackView):
    """A titled view container (a :class:`StackView` with panel chrome).

    Holds control views (or any views) and can be used as a split pane or as an
    overlay child of a :class:`SceneView`, where ``position`` anchors it over the
    canvas.
    """

    _node_type = "group"

    def __init__(
        self,
        title: str = "",
        children: list[View] | None = None,
        *,
        direction: EStackDirection | str = EStackDirection.VERTICAL,
        position: EAnchor | str | None = None,
        collapsed: bool = False,
        scrollable: bool = False,
        gap: int | None = None,
        align: EStackAlign | str = EStackAlign.STRETCH,
        justify: EStackJustify | str = EStackJustify.START,
        icon: Icon | None = None,
        icon_only: bool = False,
        tooltip: str = "",
        parent_id: str | None = None,
        size: SizeSpec = None,
        preferred_width: SizeSpec = None,
        preferred_height: SizeSpec = None,
        min_width: SizeSpec = None,
        min_height: SizeSpec = None,
        max_width: SizeSpec = None,
        max_height: SizeSpec = None,
    ) -> None:
        super().__init__(
            direction,
            children,
            scrollable=scrollable,
            gap=gap,
            align=align,
            justify=justify,
            size=size,
            preferred_width=preferred_width,
            preferred_height=preferred_height,
            min_width=min_width,
            min_height=min_height,
            max_width=max_width,
            max_height=max_height,
        )
        self.title = title
        self.position = position
        self.collapsed = collapsed
        self.icon = icon
        self.icon_only = icon_only
        self.tooltip = tooltip
        self.parent_id = parent_id

    def _serialize(self) -> dict[str, Any]:
        result = super()._serialize()
        result["title"] = self.title
        result["position"] = self.position
        result["collapsed"] = self.collapsed
        if self.icon is not None:
            result["icon"] = str(self.icon)
        result["icon_only"] = self.icon_only
        if self.tooltip:
            result["tooltip"] = self.tooltip
        if self.parent_id is not None:
            result["parent_id"] = self.parent_id
        return result
