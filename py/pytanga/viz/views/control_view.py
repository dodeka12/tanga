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
    single source of truth for the control's fields.  Shared reads are
    forwarded explicitly through typed :class:`property` accessors on this
    base; each concrete view adds typed forwarders for its kind-specific
    fields.

    Parameterised by the concrete control kind, so a subclass declares
    ``class SliderView(ControlView[Slider])`` and ``self.control`` is a
    :class:`Slider`.  ``control`` is assigned by each concrete view's
    ``__init__``; the base leaves it unset, so reading it before then raises
    :class:`AttributeError`.
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
        self._push_state = None  # state callback slot injected at mount

    @property
    def enabled(self) -> bool:
        """Whether the control is interactive (greyed out when ``False``)."""
        return self.control.enabled

    @property
    def visible(self) -> bool:
        """Whether the control is rendered at all."""
        return self.control.visible

    @property
    def selected(self) -> bool:
        """Whether the control renders in its active/selected state."""
        return self.control.selected

    def get_value(self) -> Any:
        """Return this control's current value (see :meth:`set_value`)."""
        return self.control.get_value()

    def set_value(self, value: Any) -> None:
        """Set this control's value and push ``control_update`` to the browser.

        Mutates ``self.control`` and, when mounted, pushes the new value through
        the injected ``_push`` callback (so backend-initiated changes reach the
        rendered DOM).
        """
        self.control.set_value(value)
        if self._push is not None:
            self._push(self.id, self.control.get_value())

    def set_enabled(self, enabled: bool) -> None:
        """Set this control's enabled state and push ``control_state``."""
        self.control.enabled = bool(enabled)
        if self._push_state is not None:
            self._push_state(self.id, {"enabled": self.control.enabled})

    def set_visible(self, visible: bool) -> None:
        """Set this control's visibility and push ``control_state``."""
        self.control.visible = bool(visible)
        if self._push_state is not None:
            self._push_state(self.id, {"visible": self.control.visible})

    def set_selected(self, selected: bool) -> None:
        """Set this control's active/selected state and push ``control_state``."""
        self.control.selected = bool(selected)
        if self._push_state is not None:
            self._push_state(self.id, {"selected": self.control.selected})

    def enable(self) -> None:
        """Enable this control."""
        self.set_enabled(True)

    def disable(self) -> None:
        """Disable (grey out) this control."""
        self.set_enabled(False)

    def show(self) -> None:
        """Show this control."""
        self.set_visible(True)

    def hide(self) -> None:
        """Hide this control."""
        self.set_visible(False)

    def _serialize(self) -> dict[str, Any]:
        result = super()._serialize()
        result["id"] = self.id  # control id doubles as the event key
        result["label"] = self.label
        result["tooltip"] = self.tooltip
        for key, val in self.control.serialize().items():
            if key not in ("id", "kind", "label", "tooltip"):
                result[key] = val
        return result
