# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""The :class:`StackView` flow container."""

from __future__ import annotations

from typing import Any

from ._base import View
from ._enums import EStackAlign, EStackDirection, EStackJustify
from .._size import SizeSpec


class StackView(View):
    """A flow container that stacks children vertically, horizontally, or wraps.

    Unlike :class:`SplitView`, children flow in normal document order (no
    splitters) and the container sizes to its content along the stack axis.
    """

    _node_type = "stack"

    def __init__(
        self,
        direction: EStackDirection | str,
        children: list[View] | None = None,
        *,
        scrollable: bool = False,
        gap: int | None = None,
        align: EStackAlign | str = EStackAlign.STRETCH,
        justify: EStackJustify | str = EStackJustify.START,
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
        if direction not in EStackDirection:
            raise ValueError(
                f"direction must be 'vertical', 'horizontal' or 'wrap', got {direction!r}"
            )
        if align not in EStackAlign:
            raise ValueError(
                f"align must be 'start', 'center', 'end' or 'stretch', got {align!r}"
            )
        if justify not in EStackJustify:
            raise ValueError(
                f"justify must be one of 'start', 'center', 'end', 'space-between', "
                f"'space-around', 'space-evenly', got {justify!r}"
            )
        if gap is not None and (
            isinstance(gap, bool) or not isinstance(gap, int) or gap < 0
        ):
            raise ValueError(f"gap must be a non-negative int or None, got {gap!r}")
        self.direction = direction
        self.children = list(children or [])
        self.scrollable = scrollable
        self.gap = gap
        self.align = align
        self.justify = justify

    def _serialize(self) -> dict[str, Any]:
        result = super()._serialize()
        result["direction"] = self.direction
        result["scrollable"] = self.scrollable
        result["gap"] = self.gap
        result["align"] = self.align
        result["justify"] = self.justify
        result["children"] = [child._serialize() for child in self.children]
        return result
