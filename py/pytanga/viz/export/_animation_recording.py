# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""AnimationRecording — captures per-frame entity state for animated export.

Each frame is a full, id-keyed snapshot of every object in the scene
(scene-layer entities and overlay labels), captured via
``Scene.full_state()``.  The JS playback engine reconciles consecutive
snapshots by entity id, so no separate ``initial_state`` is needed.
"""

from __future__ import annotations

import base64
import gzip
import json
from typing import TYPE_CHECKING, Any

from .._style_dict import StylesMap

if TYPE_CHECKING:
    from pytanga.viz.scene import Scene


class AnimationRecording:
    """A sequence of entity state snapshots for animated HTML export.

    Created by ``SceneExporter.start_animation_recording()``.  The user
    calls ``capture_frame()`` inside their animation loop to snapshot
    the current entity state.  After the loop, the recording is passed
    to ``export_animated_figure()`` or ``export_animated_html()``.

    Usage::

        recording = exporter.start_animation_recording()
        for frame in range(150):
            viz.update_entity(...)
            viz.flush()
            recording.capture_frame()
        exporter.export_animated_figure("anim.html", recording, fps=30)
    """

    def __init__(
        self,
        scene: Scene,
        styles_map: StylesMap | None = None,
    ) -> None:
        self._scene = scene
        self._styles_map = styles_map or {}
        self._frames: list[list[dict[str, Any]]] = []
        self._cameras: list[dict[str, Any] | None] = []
        self._assets: dict[str, dict[str, Any]] = {}
        self._frame_assets: list[list[dict[str, str]]] = []
        self._assets_captured = False

    def capture_frame(self, include_images: bool = False) -> None:
        """Snapshot the current entity state.

        Uses ``Scene.full_state()`` to capture the complete state of every
        object regardless of dirty flags.  This is safe even when
        ``viz.flush()`` is called before or after — the recording is
        independent of the live viewer's dirty-tracked flush cycle.

        Each captured frame is a full, id-keyed snapshot of every object.
        Image pixel data is captured **once** (into ``assets``); pass
        ``include_images=True`` to re-capture it (e.g. when the image changes
        per frame).
        """
        entities = self._scene.full_state(styles_map=self._styles_map)
        self._frames.append(list(entities))
        camera = self._scene.config.camera
        self._cameras.append(camera.to_dict() if camera is not None else None)
        if include_images or not self._assets_captured:
            self.capture_assets()
            self._assets_captured = True
        self._frame_assets.append(image_hydration_frames(self._assets))

    def capture_assets(self) -> None:
        """Collect image pixel data once (data → base64, url → url)."""
        self._assets = capture_image_assets(self._scene)

    @staticmethod
    def _image_asset(img: Any) -> dict[str, Any]:
        """Serialize one image layer into the asset store.

        Eligible images (``uint8``, 1 or 3 channels) are embedded as a JPEG
        data URL; everything else keeps a raw base64 buffer.
        """
        asset: dict[str, Any] = {
            "kind": "image",
            "source": img.source,
            "width": img.width,
            "height": img.height,
            "channels": img.channels,
            "dtype": img.dtype.value if img.dtype is not None else 0,
        }
        if img.url is not None:
            asset["url"] = img.url
        elif img.supports_jpeg:
            asset["source"] = "url"
            asset["url"] = img.to_jpeg_data_url()
        else:
            asset["data"] = img.to_base64()
        return asset

    @property
    def assets(self) -> dict[str, dict[str, Any]]:
        """The id-keyed asset store (images, and future textures)."""
        return dict(self._assets)

    @property
    def frame_assets(self) -> list[list[dict[str, str]]]:
        """The per-frame image-hydration lists (index-aligned with ``frames``)."""
        return list(self._frame_assets)

    @property
    def frames(self) -> list[list[dict[str, Any]]]:
        """The raw list of per-frame entity snapshots."""
        return self._frames

    @property
    def frame_count(self) -> int:
        """Number of recorded frames."""
        return len(self._frames)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the recording to a compact JSON-serializable dict.

        Returns a dict with ``frames`` (full, id-keyed per-frame snapshots)
        and ``frame_count``.  Frames are the single source of truth for
        playback; there is no separate ``initial_state``.
        """
        return {
            "frames": self._frames,
            "frame_count": len(self._frames),
            "cameras": self._cameras,
            "assets": self._assets,
            "frame_assets": self._frame_assets,
        }

    def to_json(self, *, compress: bool = False) -> str:
        """Serialize the recording to a JSON string.

        When *compress* is ``True``, the output is a base64-encoded gzip
        blob intended for embedding in an HTML ``<script>`` tag with
        client-side ``DecompressionStream`` decoding.

        Args:
            compress: If ``True``, gzip-compress the JSON before base64
                encoding.

        Returns:
            A JSON string (uncompressed) or a base64-encoded gzip blob.
        """
        data = self.to_dict()
        raw_json = json.dumps(data, separators=(",", ":")).encode("utf-8")

        if compress:
            compressed = gzip.compress(raw_json)
            return base64.b64encode(compressed).decode("ascii")

        return raw_json.decode("utf-8")


def capture_image_assets(scene: Any) -> dict[str, dict[str, Any]]:
    """Capture image pixel assets from a scene's ``VizImage`` nodes."""
    from .._nodes import VizImage

    assets: dict[str, dict[str, Any]] = {}
    for node in scene._dfs_preorder():
        if isinstance(node, VizImage):
            for img in node.images:
                assets[img.id] = AnimationRecording._image_asset(img)
    return assets


def image_hydration_frames(assets: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    """Convert asset-store entries to frame-hydration records ``{id, codec, data_b64}``.

    JPEG data URLs become ``codec="jpeg"``; raw base64 buffers become
    ``codec="raw"``; external URLs are skipped (the frontend ``url`` path loads
    them directly).
    """
    frames: list[dict[str, str]] = []
    for asset_id, asset in assets.items():
        if asset.get("source") == "url":
            url = asset.get("url", "")
            if isinstance(url, str) and url.startswith("data:image/"):
                _, b64 = url.split(",", 1)
                frames.append({"id": asset_id, "codec": "jpeg", "data_b64": b64})
        elif "data" in asset:
            frames.append({"id": asset_id, "codec": "raw", "data_b64": asset["data"]})
    return frames
