# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Banner / dialog data model and wire serialization.

A :class:`Banner` is a transient overlay shown over the viewer (globally or per
scene) with markdown/KaTeX text and optional controls (buttons / sliders /
dropdowns).  The serializers here produce the ``banner_define`` /
``banner_remove`` / ``banner_clear`` messages defined in the wire contract.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ._controls import Control, Handler, serialize_control_defs


@dataclass
class Banner:
    """A transient banner/dialog overlay.

    Attributes:
        id: Unique banner identifier (also the ``banner_remove`` key).
        text: Markdown/KaTeX body text.
        title: Optional title shown above the body.
        align_x / align_y: Anchor point in ``[0, 1]``: ``(0, 0)`` pins the
            banner's top-left to the container's top-left; ``(1, 1)`` pins its
            bottom-right to the container's bottom-right; ``(0.5, 0.5)``
            centers it.  The container is the viewport (global) or the scene
            pane (per-scene).
        auto_hide: When ``True`` (default), the frontend removes the banner once
            the user selects an option; otherwise the backend must remove it.
        dismissable: When ``False``, the banner is modal — a dimmed backdrop
            blocks interaction and there is no ✕ / click-away.
        controls: The control objects rendered as the banner's options.
        on_close: Optional handler invoked when the user dismisses a
            ``dismissable`` banner (runs on the server loop).
    """

    id: str
    text: str
    title: str = ""
    align_x: float = 0.5
    align_y: float = 0.5
    auto_hide: bool = True
    dismissable: bool = True
    controls: list[Control] = field(default_factory=list)
    on_close: Handler | None = None

    def __post_init__(self) -> None:
        for name in ("align_x", "align_y"):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1], got {value}")


def serialize_banner(banner: Banner, scene: str | None = None) -> dict[str, Any]:
    """Build the ``banner_define`` message for *banner*.

    *scene* is ``None`` for a global banner (serialized as JSON ``null``) or a
    scene name (``""`` = main scene) for a per-scene banner.
    """
    return {
        "type": "banner_define",
        "scene": scene,
        "id": banner.id,
        "title": banner.title,
        "text": banner.text,
        "align_x": banner.align_x,
        "align_y": banner.align_y,
        "auto_hide": banner.auto_hide,
        "dismissable": banner.dismissable,
        "controls": serialize_control_defs(banner.controls),
    }


def serialize_banner_remove(
    banner_id: str, scene: str | None = None
) -> dict[str, Any]:
    """Build the ``banner_remove`` message."""
    return {"type": "banner_remove", "scene": scene, "id": banner_id}


def serialize_banner_clear(scene: str | None = None) -> dict[str, Any]:
    """Build the ``banner_clear`` message."""
    return {"type": "banner_clear", "scene": scene}
