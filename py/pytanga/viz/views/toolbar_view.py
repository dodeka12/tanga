# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""The :class:`ToolbarView` horizontal control toolbar."""

from __future__ import annotations

from typing import Any

from ._base import View
from .._controls import EControlVariant
from ._enums import EStackAlign, EStackDirection, EStackJustify
from ._helpers import _size_dict
from .._size import Size, SizeSpec
from .menu_view import MenuView
from .stack_view import StackView


def _apply_toolbar_variant(view: View) -> None:
    """Recursively force ``TOOLBAR`` onto eligible control views in a toolbar."""
    for child in getattr(view, "children", None) or ():
        if isinstance(child, MenuView):
            continue  # a nested menu keeps its own MENU styling
        ctrl = getattr(child, "control", None)
        if ctrl is not None and hasattr(ctrl, "variant"):
            ctrl.variant = EControlVariant.TOOLBAR
        _apply_toolbar_variant(child)


class ToolbarView(StackView):
    """A horizontal control toolbar (a bordered :class:`StackView` row).

    ``direction`` is fixed to ``"horizontal"``.  ``margin`` is the inner
    spacing (padding) between the border and the controls; ``border`` toggles
    the thin outline.  ``gap`` spaces the controls, ``align`` sets cross-axis
    (vertical) alignment, and ``justify`` positions the controls along the row
    (``START`` left, ``END`` right, ``CENTER`` block-centered, ``SPACE_EVENLY``
    equally spaced).
    """

    _node_type = "toolbar"

    def __init__(
        self,
        children: list[View] | None = None,
        *,
        margin: SizeSpec = Size.px(6),
        border: bool = True,
        gap: int | None = None,
        align: EStackAlign | str = EStackAlign.CENTER,
        justify: EStackJustify | str = EStackJustify.START,
        size: SizeSpec = None,
        preferred_width: SizeSpec = None,
        preferred_height: SizeSpec = None,
        min_width: SizeSpec = None,
        min_height: SizeSpec = None,
        max_width: SizeSpec = None,
        max_height: SizeSpec = None,
    ) -> None:
        if margin is not None and not isinstance(margin, Size):
            raise ValueError(f"margin must be a Size or None, got {margin!r}")
        if not isinstance(border, bool):
            raise ValueError(f"border must be a bool, got {border!r}")
        super().__init__(
            EStackDirection.HORIZONTAL,
            children,
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
        self.margin = margin
        self.border = border
        _apply_toolbar_variant(self)

    def _serialize(self) -> dict[str, Any]:
        result = super()._serialize()
        result["margin"] = _size_dict(self.margin)
        result["border"] = self.border
        return result
