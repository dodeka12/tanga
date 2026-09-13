# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Image view and canvas for displaying raster images in the Tanga viewer.

This module is the backend mirror of the frontend ``renderers/image.js``.  The
low-level :class:`ImageView` owns the images, shader, and uniform state;
:class:`ImageCanvas` (added in a later phase) is the user-facing helper.
"""

from __future__ import annotations

from typing import Any

from .image import ImageData, default_mode, default_value_range

__all__ = ["ImageView"]

#: Fixed number of image layers (the wire contract).
MAX_IMAGE_LAYERS = 4

#: Standard-shader uniform defaults (brightness / contrast / contrast mid-point).
_STANDARD_UNIFORM_DEFAULTS: dict[str, float] = {
    "u_brightness": 0.0,
    "u_contrast": 1.0,
    "u_midpoint": 0.5,
}


class ImageView:
    """Low-level image plane: images + shader + uniform state.

    Holds up to :data:`MAX_IMAGE_LAYERS` images (each available to the shader as
    a texture), the custom fragment shader, and the uniform values.  This class
    is pure data + validation; it serializes to the ``image`` entity dict.
    """

    def __init__(self, image_id: str) -> None:
        self.id = image_id
        self._images: list[ImageData] = []
        self._uniforms: dict[str, float | int] = {}
        self._fragment: str | None = None
        self._vertex: str | None = None
        self._frame: tuple[int, int] | None = None
        self._uniforms.update(_STANDARD_UNIFORM_DEFAULTS)

    # -- image layers -------------------------------------------------

    @property
    def images(self) -> list[ImageData]:
        """A copy of the current image layers."""
        return list(self._images)

    @property
    def frame(self) -> tuple[int, int]:
        """The pixel frame extent ``(width, height)``, or ``(0, 0)`` if empty."""
        return self._frame if self._frame is not None else (0, 0)

    def set_image(self, image: ImageData) -> None:
        """Replace layer 0 (the primary, frame-defining image) with *image*."""
        if self._images:
            self._images[0] = image
        else:
            self._images.append(image)
        assert image.width is not None and image.height is not None
        self._frame = (image.width, image.height)
        self._seed_image_defaults(image)

    def add_image(self, image: ImageData) -> None:
        """Append *image* as the next layer (max :data:`MAX_IMAGE_LAYERS`)."""
        if len(self._images) >= MAX_IMAGE_LAYERS:
            raise ValueError(f"ImageView supports at most {MAX_IMAGE_LAYERS} images")
        self._images.append(image)
        if self._frame is None:
            assert image.width is not None and image.height is not None
            self._frame = (image.width, image.height)
        self._seed_image_defaults(image)

    def _seed_image_defaults(self, image: ImageData) -> None:
        """Seed ``u_mode``/``u_value_min``/``u_value_max`` from the image."""
        assert image.channels is not None and image.dtype is not None
        self._uniforms.setdefault("u_mode", default_mode(image.channels))
        lo, hi = default_value_range(image.dtype)
        self._uniforms.setdefault("u_value_min", lo)
        self._uniforms.setdefault("u_value_max", hi)

    # -- uniforms -----------------------------------------------------

    @property
    def uniforms(self) -> dict[str, float | int]:
        """A copy of the current uniform values."""
        return dict(self._uniforms)

    def set_uniform(self, name: str, value: float | int) -> None:
        """Set a uniform value (emitted as a JSON ``image_update`` later)."""
        self._uniforms[name] = value

    def register_uniform(self, name: str, default: float | int) -> None:
        """Register a uniform with a default, keeping an existing value."""
        self._uniforms.setdefault(name, default)

    # -- shader -------------------------------------------------------

    def register_shader(self, fragment: str, vertex: str | None = None) -> None:
        """Register a custom fragment (and optional vertex) shader source."""
        self._fragment = fragment
        self._vertex = vertex

    # -- serialization ------------------------------------------------

    def _serialize(self) -> dict[str, Any]:
        """Serialize to the canonical ``image`` entity dict (README contract)."""
        return {
            "id": self.id,
            "layer": "scene",
            "kind": "image",
            "frame": {"width": self.frame[0], "height": self.frame[1]},
            "images": [self._serialize_image(img) for img in self._images],
            "shader": {"fragment": self._fragment, "vertex": self._vertex},
            "uniforms": dict(self._uniforms),
        }

    def _serialize_image(self, image: ImageData) -> dict[str, Any]:
        """Serialize one image layer (metadata only — pixels travel as bytes)."""
        assert image.dtype is not None
        result: dict[str, Any] = {
            "id": image.id,
            "width": image.width,
            "height": image.height,
            "channels": image.channels,
            "dtype": image.dtype.value,
            "source": image.source,
        }
        if image.url is not None:
            result["url"] = image.url
        return result
