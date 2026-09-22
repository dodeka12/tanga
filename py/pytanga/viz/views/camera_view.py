# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""The :class:`CameraView` presentation descriptor for one pane's camera."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

from ._helpers import _image_meta, _normalize_lock, _normalize_navigation
from ..camera import (
    CameraAction,
    CameraConfig,
    Navigation,
    View2DConfig,
    View3dConfig,
    ViewportConfig,
    _normalize_camera_config,
)

if TYPE_CHECKING:
    from .._interaction import MouseButton


@dataclass
class CameraView:
    """Presentation descriptor for one pane's camera.

    Bundles the camera (a :class:`~pytanga.viz.camera.CameraConfig`, including
    :class:`~pytanga.viz.camera.PinholeCamera`), an optional ``lock`` set, a
    ``navigation`` mode, an optional per-pane ``controls`` button mapping, an
    optional ``viewport``, and an optional ``background_image``.  Pass to
    ``SceneView(camera_view=…)``.
    """

    camera: CameraConfig | View2DConfig | View3dConfig | None = None
    navigation: str | Navigation = "orbit"
    controls: dict[MouseButton, CameraAction | None] | None = None
    lock: set[str] | None = None
    viewport: ViewportConfig | None = None
    background_image: Any | None = None

    def __post_init__(self) -> None:
        self.camera = _normalize_camera_config(self.camera)
        self.navigation = _normalize_navigation(self.navigation)
        self.lock = _normalize_lock(self.lock)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if self.camera is not None:
            result["camera"] = cast("CameraConfig", self.camera).to_dict()
        if self.navigation != "orbit":
            result["navigation"] = self.navigation
        if self.controls is not None:
            result["controls"] = {
                button.value: (action.value if action is not None else None)
                for button, action in self.controls.items()
            }
        if self.lock:
            result["lock"] = sorted(self.lock)
        if self.viewport is not None:
            result["viewport"] = self.viewport.to_dict()
        if self.background_image is not None:
            result["background_image"] = _image_meta(self.background_image)
        return result
