# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""The generic :class:`ControlView` base for HTML control views."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from ._base import View
from .._controls import Control
from .._size import Size, SizeSpec

C = TypeVar("C", bound=Control)


class ControlView(View, Generic[C]):
    """Base for a single HTML control rendered as a plain ``View`` (no scene).

    The control ``id`` is the WebSocket event key (``control_id``) and must be
    unique across the app.  Each subclass wraps a
    :class:`~pytanga.viz._controls.Control` (``self.control``) which is the
    single source of truth for the control's fields; reads of those fields
    delegate to it via :meth:`__getattr__`.

    Parameterised by the concrete control kind, so a subclass declares
    ``class SliderView(ControlView[Slider])`` and ``self.control`` is a
    :class:`Slider`.  ``control`` is assigned by each concrete view's
    ``__init__``; the base leaves it unset, so reading it before then falls
    through to :meth:`__getattr__`'s ``AttributeError``.
    """

    control: C

    _node_type = "control"

    def __init__(
        self,
        cid: str,
        *,
        label: str = "",
        tooltip: str = "",
        size: SizeSpec = None,
        preferred_width: SizeSpec = None,
        preferred_height: SizeSpec = None,
        min_width: SizeSpec = Size.px(120),
        min_height: SizeSpec = Size.px(32),
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
        self.id = cid
        self.label = label
        self.tooltip = tooltip
        self._push = None  # callback slot injected at mount (LogView pattern)

    def __getattr__(self, name: str) -> Any:
        ctrl = self.__dict__.get("control")
        if ctrl is not None and hasattr(ctrl, name):
            return getattr(ctrl, name)
        raise AttributeError(f"{type(self).__name__} object has no attribute {name!r}")

    def set_value(self, value: Any) -> None:
        """Set this control's value and push ``control_update`` to the browser.

        Mutates ``self.control`` and, when mounted, pushes the new value through
        the injected ``_push`` callback (so backend-initiated changes reach the
        rendered DOM).
        """
        self.control.set_value(value)
        if self._push is not None:
            self._push(self.id, self.control.get_value())

    def _serialize(self) -> dict[str, Any]:
        result = super()._serialize()
        result["id"] = self.id  # control id doubles as the event key
        result["label"] = self.label
        result["tooltip"] = self.tooltip
        for key, val in self.control.serialize().items():
            if key not in ("id", "kind", "label", "tooltip"):
                result[key] = val
        return result
