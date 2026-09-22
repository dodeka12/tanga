# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""The :class:`SceneView` pane that renders a named scene."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ._base import View
from ._helpers import (
    _DEFAULT_SCENE_MIN,
    _coerce_scene_name,
    _normalize_id_set,
    _scene_view_counter,
)
from .._size import SizeSpec
from ..camera import (
    CameraAction,
    CameraConfig,
    Navigation,
    View2DConfig,
    View3dConfig,
    ViewportConfig,
)
from .camera_view import CameraView

if TYPE_CHECKING:
    from ._helpers import SceneRef
    from .._interaction import MouseButton


class SceneView(View):
    """A pane that renders a named scene (referenced by name or handle).

    Scene panes default to a small minimum size on both axes (``min_width`` and
    ``min_height``) so a splitter cannot collapse them to nothing.  Pass
    explicit ``min_width``/``min_height`` (``None`` disables the floor).

    ``camera_view`` (a :class:`CameraView`) bundles this pane's camera, lock,
    and background image.  ``camera`` is a shorthand for a plain free-orbit
    camera (``CameraView(camera=…)``); pass one or the other, not both.  With
    neither, the pane uses the scene's own camera.

    ``id`` is an optional stable identifier for the pane (auto-generated as
    ``"svN"`` when omitted).  It is the key used to address this pane at runtime
    (e.g. ``Visualizer.set_view_camera``).

    ``overlay`` lists views that float over the canvas (e.g. a ``GroupView``),
    anchored by each child's ``position``.

    ``hide`` / ``show`` are optional sets of scene-entity ids that filter which
    entities this pane renders (``hide`` removes, ``show`` is a whitelist).
    """

    _node_type = "scene_view"

    def __init__(
        self,
        scene: SceneRef,
        *,
        id: str | None = None,
        camera: CameraConfig | View2DConfig | View3dConfig | None = None,
        camera_view: CameraView | None = None,
        navigation: str | Navigation = "orbit",
        controls: dict[MouseButton, CameraAction | None] | None = None,
        viewport: ViewportConfig | None = None,
        overlay: list[View] | None = None,
        hide: set[str] | None = None,
        show: set[str] | None = None,
        size: SizeSpec = None,
        preferred_width: SizeSpec = None,
        preferred_height: SizeSpec = None,
        min_width: SizeSpec = _DEFAULT_SCENE_MIN,
        min_height: SizeSpec = _DEFAULT_SCENE_MIN,
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
        self.scene = _coerce_scene_name(scene)
        self.id = id if id is not None else f"sv{next(_scene_view_counter)}"
        if camera is not None and camera_view is not None:
            raise ValueError("pass either `camera` or `camera_view`, not both")
        if camera_view is not None:
            if not isinstance(camera_view, CameraView):
                raise TypeError(
                    f"camera_view must be a CameraView, got {type(camera_view).__name__}"
                )
            self.camera_view = camera_view
        elif (
            camera is not None
            or navigation != "orbit"
            or controls is not None
            or viewport is not None
        ):
            self.camera_view = CameraView(
                camera=camera,
                navigation=navigation,
                controls=controls,
                viewport=viewport,
            )
        else:
            self.camera_view = None
        self.overlay = list(overlay or [])
        self.hide = _normalize_id_set(hide)
        self.show = _normalize_id_set(show)

    def _serialize(self) -> dict[str, Any]:
        result = super()._serialize()
        result["id"] = self.id
        result["scene"] = self.scene
        if self.camera_view is not None:
            result["camera_view"] = self.camera_view.to_dict()
        if self.hide:
            result["hide"] = sorted(self.hide)
        if self.show:
            result["show"] = sorted(self.show)
        if self.overlay:
            result["children"] = [child._serialize() for child in self.overlay]
        return result
