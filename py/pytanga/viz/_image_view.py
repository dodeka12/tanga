# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Image view and canvas for displaying raster images in the Tanga viewer.

This module is the backend mirror of the frontend ``renderers/image.js``.  The
low-level :class:`ImageView` owns the images, shader, and uniform state;
:class:`ImageCanvas` (added in a later phase) is the user-facing helper.
"""

from __future__ import annotations

from itertools import count
from typing import Any

from .camera import StretchMode, View2DConfig, _validate_stretch
from .image import ImageData, default_mode, default_value_range
from ._interaction import ModifierKey, MouseButton

__all__ = ["ImageView", "ImageCanvas"]

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


#: Process-wide counter for auto-generated image ids (``img0``…).
_image_id_counter = count()

#: Process-wide counter for auto-generated ``ImageCanvas`` scene names (``imgc0``…).
_image_canvas_counter = count()


def _coerce_visualizer(target: Any) -> Any:
    """Return the :class:`~pytanga.viz.Visualizer` behind a target handle."""
    from .visualizer import Visualizer

    if isinstance(target, Visualizer):
        return target
    viz = getattr(target, "_viz", None)
    if isinstance(viz, Visualizer):
        return viz
    raise TypeError(
        f"ImageCanvas expects a Visualizer or VizSceneHandle, "
        f"got {type(target).__name__!r}"
    )


class ImageCanvas:
    """User-facing helper for displaying images (analogous to ``CoordinateSystem``).

    Owns a dedicated 2D scene with a y-down pixel frame, an :class:`ImageView`
    (plane + textures + shader/uniform state), an :class:`ActImagePlane` for
    interaction, and an overlay group for drawing in pixel coordinates.
    """

    def __init__(
        self,
        target: Any,
        *,
        image_id: str | None = None,
        stretch: StretchMode = "fit",
        border_px: float = 0.0,
        drag_button: MouseButton = MouseButton.LEFT,
        drag_modifiers: frozenset[ModifierKey] = frozenset(),
        on_drag: Any = None,
        on_drag_start: Any = None,
        on_drag_end: Any = None,
        on_click: Any = None,
    ) -> None:
        viz = _coerce_visualizer(target)
        self._image_id = (
            image_id if image_id is not None else f"img{next(_image_id_counter)}"
        )
        self._image_view = ImageView(self._image_id)
        self._stretch = _validate_stretch(stretch)
        self._border_px = float(border_px)

        self._scene_name = f"imgc{next(_image_canvas_counter)}"
        self._handle = viz.scene(
            self._scene_name, space_dim=2, add_axes=False, add_grid=False
        )
        self._transport = getattr(viz, "_transport", None)
        self._overlay = self._handle.add_group(f"{self._scene_name}_overlay")
        self._overlay_refs: list[Any] = []

        from ._active import ActImagePlane

        self._act_plane = ActImagePlane(
            self._image_view,
            drag_button=drag_button,
            drag_modifiers=drag_modifiers,
            handler=on_drag,
            on_drag_start=on_drag_start,
            on_drag_end=on_drag_end,
            on_click=on_click,
        )
        self._interaction_registered = False

    # -- image / shader / uniform ---------------------------------

    @property
    def image_view(self) -> ImageView:
        """The underlying :class:`ImageView` (images + shader + uniforms)."""
        return self._image_view

    def set_image(self, image: ImageData) -> None:
        """Replace the primary image, re-frame the camera, and sync it."""
        self._image_view.set_image(image)
        self.fit_to_image()
        self._sync_image()

    def add_image(self, image: ImageData) -> None:
        """Append another image layer (max 4)."""
        self._image_view.add_image(image)
        self._sync_image()

    def set_uniform(self, name: str, value: float | int) -> None:
        """Set a shader uniform value (JSON ``image_update``, no image bytes)."""
        self._image_view.set_uniform(name, value)
        if self._transport is not None:
            self._transport.send(
                {
                    "type": "image_update",
                    "scene": self._scene_name,
                    "id": self._image_view.id,
                    "uniforms": {name: value},
                }
            )

    def register_uniform(self, name: str, default: float | int) -> None:
        """Register a shader uniform with a default (keeps an existing value)."""
        self._image_view.register_uniform(name, default)

    def register_shader(self, fragment: str, vertex: str | None = None) -> None:
        """Register a custom fragment (and optional vertex) shader."""
        self._image_view.register_shader(fragment, vertex)

    # -- overlay --------------------------------------------------

    def add(self, obj: Any = None, **kwargs: Any) -> Any:
        """Add a drawable entity to the overlay group, returning its ref."""
        ref = self._overlay.new(obj, **kwargs)
        self._overlay_refs.append(ref)
        return ref

    def remove(self, ref: Any) -> None:
        """Remove a previously added overlay entity."""
        ref.remove()
        self._overlay_refs = [r for r in self._overlay_refs if r.id != ref.id]

    def clear(self) -> None:
        """Remove every overlay entity."""
        for ref in list(self._overlay_refs):
            ref.remove()
        self._overlay_refs.clear()

    # -- interaction ----------------------------------------------

    @property
    def act_plane(self) -> Any:
        """The interactive image plane (:class:`~pytanga.viz.ActImagePlane`)."""
        return self._act_plane

    # -- scene ----------------------------------------------------

    @property
    def scene_name(self) -> str:
        """The dedicated scene name (usable in a ``SceneView``)."""
        return self._scene_name

    @property
    def handle(self) -> Any:
        """The :class:`~pytanga.viz.VizSceneHandle` for the dedicated scene."""
        return self._handle

    def scene_view(self) -> Any:
        """A :class:`~pytanga.viz.SceneView` pane for the dedicated scene."""
        from .views import SceneView

        return SceneView(self._scene_name)

    def fit_to_image(self) -> None:
        """Frame the 2D camera on the image's pixel extent."""
        width, height = self._image_view.frame
        if width <= 0 or height <= 0:
            return
        self._handle.set_camera(
            View2DConfig(
                xmin=-0.5,
                xmax=width - 0.5,
                ymin=-0.5,
                ymax=height - 0.5,
                stretch=self._stretch,
                border_px=self._border_px,
            )
        )

    def _sync_image(self) -> None:
        """Register the image entity and send its pixel bytes + uniforms."""
        from ._image_wire import encode_image_frame

        payload = self._image_view._serialize()
        self._handle.scene.upsert_image(
            self._image_view.id, payload, images=self._image_view.images
        )
        self._register_interaction()

        if self._transport is None:
            return
        for img in self._image_view.images:
            if img.data is not None:
                self._transport.send_bytes(encode_image_frame(img.id, img.data))
        self._transport.send(
            {
                "type": "image_update",
                "scene": self._scene_name,
                "id": self._image_view.id,
                "uniforms": dict(self._image_view.uniforms),
            }
        )
        self._handle.flush()

    def _register_interaction(self) -> None:
        """Register the image plane as interactive (idempotent)."""
        if self._interaction_registered:
            return
        image_id = self._image_view.id
        self._act_plane._init(self._handle, image_id)
        self._handle._viz._act_objects[image_id] = self._act_plane
        self._interaction_registered = True
