# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Dialog data model and wire serialization (sibling of :mod:`._banner`).

A :class:`Dialog` is a transient overlay shown over the viewer (globally or per
scene) with a title bar and an arbitrary view-content container (built from the
declarative layout model in :mod:`.views`).  The serializers here produce the
``dialog_define`` / ``dialog_remove`` / ``dialog_clear`` messages defined in the
wire contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ._controls import Handler
from .views import View, _make_id_gen


@dataclass
class Dialog:
    """A transient dialog overlay with arbitrary view content.

    Attributes:
        id: Unique dialog identifier (also the ``dialog_remove`` key).
        content: The view subtree rendered inside the dialog body (any
            :class:`~pytanga.viz.views.View`, e.g. a ``StackView`` of control
            views).
        title: Optional title shown in the dialog's title bar.
        align_x / align_y: Anchor point in ``[0, 1]``: ``(0, 0)`` pins the
            dialog's top-left to the container's top-left; ``(1, 1)`` pins its
            bottom-right to the container's bottom-right; ``(0.5, 0.5)``
            centers it.  The container is the viewport (global) or the scene
            pane (per-scene).
        dismissable: When ``False``, the dialog is modal — a dimmed backdrop
            blocks interaction and there is no ✕.
        on_close: Optional handler invoked when the user dismisses a
            ``dismissable`` dialog via the ✕ (runs on the server loop).
    """

    id: str
    content: View
    title: str = ""
    align_x: float = 0.5
    align_y: float = 0.5
    dismissable: bool = True
    on_close: Handler | None = None

    def __post_init__(self) -> None:
        for name in ("align_x", "align_y"):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1], got {value}")


def serialize_dialog(dialog: Dialog, scene: str | None = None) -> dict[str, Any]:
    """Build the ``dialog_define`` message for *dialog*.

    *scene* is ``None`` for a global dialog (serialized as JSON ``null``) or a
    scene name (``""`` = main scene) for a per-scene dialog.
    """
    return {
        "type": "dialog_define",
        "scene": scene,
        "id": dialog.id,
        "title": dialog.title,
        "align_x": dialog.align_x,
        "align_y": dialog.align_y,
        "dismissable": dialog.dismissable,
        "content": dialog.content._serialize(_make_id_gen()),
    }


def serialize_dialog_remove(
    dialog_id: str, scene: str | None = None
) -> dict[str, Any]:
    """Build the ``dialog_remove`` message."""
    return {"type": "dialog_remove", "scene": scene, "id": dialog_id}


def serialize_dialog_clear(scene: str | None = None) -> dict[str, Any]:
    """Build the ``dialog_clear`` message."""
    return {"type": "dialog_clear", "scene": scene}
