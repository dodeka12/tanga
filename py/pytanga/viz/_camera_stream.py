# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""MJPEG camera stream publisher.

A :class:`CameraStream` encodes frames as JPEG once and fans the latest frame
out to HTTP subscribers.  Slow consumers simply receive the newest frame on
each tick, so a 15–30 Hz feed never accumulates a backlog.
"""

from __future__ import annotations

import threading
from typing import Any

import numpy as np

from ._image_wire import encode_jpeg
from .image import ImageData


class CameraStream:
    """A publish/subscribe MJPEG frame source, addressed at ``/stream/{id}``."""

    def __init__(self, stream_id: str, *, fps: int = 30) -> None:
        if fps <= 0:
            raise ValueError("fps must be positive")
        self.stream_id = stream_id
        self.fps = int(fps)
        self._lock = threading.Lock()
        self._latest: bytes | None = None

    def publish(self, image: Any, *, quality: int = 85) -> None:
        """Publish a frame (a numpy array or :class:`ImageData`)."""
        arr = image.data if isinstance(image, ImageData) else image
        if not isinstance(arr, np.ndarray):
            raise TypeError(
                f"expected a numpy array or ImageData, got {type(image).__name__}"
            )
        encoded = encode_jpeg(arr, quality=quality)
        with self._lock:
            self._latest = encoded

    def latest(self) -> bytes | None:
        """Return the most recently published JPEG frame (or ``None``)."""
        with self._lock:
            return self._latest
