# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Image view and canvas for displaying raster images in the Tanga viewer.

This module is the backend mirror of the frontend ``renderers/image.js``.  The
low-level :class:`ImageView` owns the images, shader, and uniform state;
:class:`ImageCanvas` (added in a later phase) is the user-facing helper.
"""

from __future__ import annotations

from .image import ImageData

__all__ = ["ImageView"]

#: Fixed number of image layers (the wire contract).
MAX_IMAGE_LAYERS = 4


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

    def add_image(self, image: ImageData) -> None:
        """Append *image* as the next layer (max :data:`MAX_IMAGE_LAYERS`)."""
        if len(self._images) >= MAX_IMAGE_LAYERS:
            raise ValueError(f"ImageView supports at most {MAX_IMAGE_LAYERS} images")
        self._images.append(image)
        if self._frame is None:
            assert image.width is not None and image.height is not None
            self._frame = (image.width, image.height)

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
