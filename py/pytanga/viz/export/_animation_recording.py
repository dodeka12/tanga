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
        styles_map: dict[str, Any] | None = None,
    ) -> None:
        self._scene = scene
        self._styles_map = styles_map or {}
        self._frames: list[list[dict[str, Any]]] = []

    def capture_frame(self) -> None:
        """Snapshot the current entity state.

        Uses ``Scene.full_state()`` to capture the complete state of every
        object regardless of dirty flags.  This is safe even when
        ``viz.flush()`` is called before or after — the recording is
        independent of the live viewer's dirty-tracked flush cycle.

        Each captured frame is a full, id-keyed snapshot of every object.
        """
        entities = self._scene.full_state(styles_map=self._styles_map)
        self._frames.append(list(entities))

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