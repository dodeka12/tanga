# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""The :class:`SeparatorView` thin divider line."""

from __future__ import annotations

from typing import Any, Literal

from ._base import View
from ._helpers import _DEFAULT_SEPARATOR_SPACING
from .._size import Size, SizeSpec


class SeparatorView(View):
    """A thin 1px divider line with spacing, for toolbars/menus/stacks.

    ``orientation`` describes the *line* (perpendicular to the container it
    lives in): ``"vertical"`` for a horizontal container (``ToolbarView`` /
    menu ``bar``) and ``"horizontal"`` for a vertical container
    (``StackView`` / ``MenuView`` dropdown).  ``"auto"`` (the default) lets the
    frontend container pick the perpendicular orientation; pin it explicitly
    where there is no enclosing ``StackView``-derived container to resolve it
    (e.g. a ``SplitView`` pane), in which case ``"auto"`` stays unresolved and
    renders nothing useful — so pass an explicit orientation there.

    ``spacing`` is the gap on each side of the line (default ``6`` px).
    """

    _node_type = "separator"

    def __init__(
        self,
        orientation: Literal["auto", "horizontal", "vertical"] = "auto",
        *,
        spacing: int | None = None,
        size: SizeSpec = None,
        preferred_width: SizeSpec = None,
        preferred_height: SizeSpec = None,
        min_width: SizeSpec = None,
        min_height: SizeSpec = None,
        max_width: SizeSpec = None,
        max_height: SizeSpec = None,
    ) -> None:
        if orientation not in ("auto", "horizontal", "vertical"):
            raise ValueError(
                f"orientation must be 'auto', 'horizontal' or 'vertical', "
                f"got {orientation!r}"
            )
        if spacing is not None and (
            isinstance(spacing, bool) or not isinstance(spacing, int) or spacing < 0
        ):
            raise ValueError(
                f"spacing must be a non-negative int or None, got {spacing!r}"
            )
        spacing = _DEFAULT_SEPARATOR_SPACING if spacing is None else spacing
        line = Size.px(1)
        if orientation == "vertical" and preferred_width is None:
            preferred_width = line
        elif orientation == "horizontal" and preferred_height is None:
            preferred_height = line
        super().__init__(
            size=size,
            preferred_width=preferred_width,
            preferred_height=preferred_height,
            min_width=min_width,
            min_height=min_height,
            max_width=max_width,
            max_height=max_height,
        )
        self.orientation = orientation
        self.spacing = spacing

    def _serialize(self) -> dict[str, Any]:
        result = super()._serialize()
        result["orientation"] = self.orientation
        result["spacing"] = self.spacing
        return result
