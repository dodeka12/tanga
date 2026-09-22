# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""The :class:`MenuView` dropdown/bar menu container."""

from __future__ import annotations

from typing import Any, Literal

from .._anchor import EAnchor
from ._base import View
from .._controls import EControlVariant
from ._enums import EStackDirection
from .._icons import Icon
from .._size import SizeSpec


def _apply_menu_variant(view: View) -> None:
    """Recursively force ``MENU`` onto eligible control views in a menu subtree."""
    for child in getattr(view, "children", None) or ():
        if isinstance(child, MenuView):
            if child.override_variant:
                _apply_menu_variant(child)
            continue
        ctrl = getattr(child, "control", None)
        if ctrl is not None and hasattr(ctrl, "variant"):
            ctrl.variant = EControlVariant.MENU
        _apply_menu_variant(child)


class MenuView(View):
    """A menu: a hamburger dropdown or a permanent horizontal strip of options.

    ``children`` are the options (usually ``*View`` control wrappers); a child
    may itself be another :class:`MenuView`, forming a nested sub-menu.  When
    used as an overlay (the global overlay or a :class:`SceneView` overlay
    child), ``position`` anchors the menu.

    ``override_variant`` (default ``True``) forces every eligible control in the
    subtree to the ``MENU`` variant, so options render flat/borderless without
    setting ``variant=`` by hand.
    """

    _node_type = "menu"

    def __init__(
        self,
        label: str = "",
        children: list[View] | None = None,
        *,
        trigger_icon: Icon | None = None,
        mode: Literal["dropdown", "bar"] = "dropdown",
        direction: EStackDirection | str | None = None,
        position: EAnchor | str | None = None,
        override_variant: bool = True,
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
        if mode not in ("dropdown", "bar"):
            raise ValueError(f"mode must be 'dropdown' or 'bar', got {mode!r}")
        if direction is None:
            direction = (
                EStackDirection.HORIZONTAL
                if mode == "bar"
                else EStackDirection.VERTICAL
            )
        if direction not in EStackDirection:
            raise ValueError(
                f"direction must be 'vertical', 'horizontal' or 'wrap', got {direction!r}"
            )
        self.label = label
        self.trigger_icon = trigger_icon
        self.mode = mode
        self.direction = direction
        self.position = position
        self.override_variant = override_variant
        self.children = list(children or [])
        if override_variant:
            _apply_menu_variant(self)

    def _serialize(self) -> dict[str, Any]:
        result = super()._serialize()
        result["trigger_icon"] = (
            str(self.trigger_icon) if self.trigger_icon is not None else None
        )
        result["label"] = self.label
        result["mode"] = self.mode
        result["direction"] = self.direction
        result["position"] = self.position
        result["children"] = [child._serialize() for child in self.children]
        return result
