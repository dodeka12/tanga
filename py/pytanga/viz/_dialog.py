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
from ._size import Size, SizeSpec
from .views import FileChooserView, View, _make_id_gen


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
    width: SizeSpec | None = None
    height: SizeSpec | None = None
    variant: str = "default"
    control_id: str | None = None
    on_accept: Handler | None = None

    def __post_init__(self) -> None:
        for name in ("align_x", "align_y"):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1], got {value}")


class FileChooserDialog:
    """A file-open dialog spec: a file chooser listing + path line + OK/Cancel.

    Pass an instance to :meth:`Visualizer.show_dialog`.  It is converted to a
    :class:`Dialog` whose content is a
    :class:`~pytanga.viz.views.FileChooserView` listing.  Selecting a file fills
    the dialog's path line (no close); ``OK`` fires ``on_accept(path)`` and
    closes, while ``Cancel``/✕ fire ``on_close`` (dismiss).
    """

    def __init__(
        self,
        control_id: str,
        *,
        title: str = "Select a file",
        value: str = "",
        root: str | None = None,
        accept: str = "",
        on_accept: Handler | None = None,
        on_close: Handler | None = None,
        align_x: float = 0.5,
        align_y: float = 0.5,
        dismissable: bool = True,
        width: SizeSpec | None = None,
        height: SizeSpec | None = None,
    ) -> None:
        self.control_id = control_id
        self.title = title
        self.value = value
        self.root = root
        self.accept = accept
        self.on_accept = on_accept
        self.on_close = on_close
        self.align_x = align_x
        self.align_y = align_y
        self.dismissable = dismissable
        self.width = Size.px(520) if width is None else width
        self.height = Size.px(420) if height is None else height

    def build_dialog(self, dialog_id: str) -> Dialog:
        """Build the underlying :class:`Dialog` (used by ``Visualizer``)."""
        return Dialog(
            id=dialog_id,
            content=FileChooserView(
                self.control_id,
                value=self.value,
                root=self.root,
                accept=self.accept,
            ),
            title=self.title,
            align_x=self.align_x,
            align_y=self.align_y,
            dismissable=self.dismissable,
            on_close=self.on_close,
            width=self.width,
            height=self.height,
            variant="file_chooser",
            control_id=self.control_id,
            on_accept=self.on_accept,
        )


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
        "variant": dialog.variant,
        "control_id": dialog.control_id,
        "align_x": dialog.align_x,
        "align_y": dialog.align_y,
        "dismissable": dialog.dismissable,
        "width": None if dialog.width is None else dialog.width.to_dict(),
        "height": None if dialog.height is None else dialog.height.to_dict(),
        "content": dialog.content._serialize(_make_id_gen()),
    }


def serialize_dialog_remove(dialog_id: str, scene: str | None = None) -> dict[str, Any]:
    """Build the ``dialog_remove`` message."""
    return {"type": "dialog_remove", "scene": scene, "id": dialog_id}


def serialize_dialog_clear(scene: str | None = None) -> dict[str, Any]:
    """Build the ``dialog_clear`` message."""
    return {"type": "dialog_clear", "scene": scene}
