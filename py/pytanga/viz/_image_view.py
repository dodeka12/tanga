# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Image view and canvas for displaying raster images in the Tanga viewer.

This module is the backend mirror of the frontend ``renderers/image.js``.  The
low-level :class:`ImageView` owns the images, shader, and uniform state;
:class:`ImageCanvas` (added in a later phase) is the user-facing helper.
"""

from __future__ import annotations

from itertools import count
from typing import TYPE_CHECKING, Any, cast

from .camera import (
    CameraAction,
    PlanarMapper,
    StretchMode,
    View2DConfig,
    _validate_stretch,
)
from .image import (
    DEFAULT_IMAGE_LAYER_STYLE,
    ImageChannelMode,
    ImageColormap,
    ImageData,
    ImageLayerStyle,
    LayerBlendMode,
    default_mode,
    default_value_range,
)
from ._interaction import MouseButton
from ._surface import InteractionSurface

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from ._active import ClickBinding, DragBinding
    from ._interaction import ClickEvent, DragEvent
    from ._surface import (
        SurfaceClickHandler,
        SurfaceDragHandler,
        SurfaceEventHandler,
    )

__all__ = ["ImageView", "ImageCanvas"]

#: Default number of image layers (the wire contract).  WebGL 1 guarantees at
#: least 8 fragment-shader texture units, so 8 is the safe portable floor.
DEFAULT_MAX_IMAGE_LAYERS = 8

#: Backward-compatible alias for the default layer count.
MAX_IMAGE_LAYERS = DEFAULT_MAX_IMAGE_LAYERS

#: Standard-shader uniform defaults (brightness / contrast / contrast mid-point).
_STANDARD_UNIFORM_DEFAULTS: dict[str, float] = {
    "u_brightness": 0.0,
    "u_contrast": 1.0,
    "u_midpoint": 0.5,
}


def _blend_code(blend: LayerBlendMode | str | int) -> int:
    """Coerce a blend mode (enum / string / raw code) to its wire int code."""
    if isinstance(blend, LayerBlendMode):
        return blend.code
    if isinstance(blend, str):
        return LayerBlendMode(blend).code
    return int(blend)


def _channel_code(channel: ImageChannelMode | str | int) -> int:
    """Coerce a channel mode (enum / string / raw code) to its wire int code."""
    if isinstance(channel, ImageChannelMode):
        return int(channel)
    if isinstance(channel, str):
        return int(ImageChannelMode.from_str(channel))
    return int(channel)


class ImageView:
    """Low-level image plane: images + shader + uniform state.

    Holds up to :data:`MAX_IMAGE_LAYERS` images (each available to the shader as
    a texture), the custom fragment shader, and the uniform values.  This class
    is pure data + validation; it serializes to the ``image`` entity dict.
    """

    def __init__(
        self, image_id: str, *, max_layers: int = DEFAULT_MAX_IMAGE_LAYERS
    ) -> None:
        if not isinstance(max_layers, int) or isinstance(max_layers, bool) or max_layers < 1:
            raise ValueError(f"max_layers must be a positive integer, got {max_layers!r}")
        self.id = image_id
        self._max_layers = max_layers
        self._images: list[ImageData | None] = []
        self._uniforms: dict[str, float | int] = {}
        self._fragment: str | None = None
        self._vertex: str | None = None
        self._frame: tuple[int, int] | None = None
        self._uniforms.update(_STANDARD_UNIFORM_DEFAULTS)
        self._transport: Any = None
        self._view_id: str | None = None
        self._record_frame: Any = None

    # -- image layers -------------------------------------------------

    @property
    def images(self) -> list[ImageData]:
        """A copy of the current (non-cleared) image layers."""
        return [img for img in self._images if img is not None]

    @property
    def primary_image(self) -> ImageData | None:
        """The primary (layer 0, frame-defining) image, or ``None`` if empty."""
        for img in self._images:
            if img is not None:
                return img
        return None

    @property
    def frame(self) -> tuple[int, int]:
        """The pixel frame extent ``(width, height)``, or ``(0, 0)`` if empty."""
        return self._frame if self._frame is not None else (0, 0)

    @property
    def max_layers(self) -> int:
        """The configured maximum number of image layers."""
        return self._max_layers

    def set_image(
        self, image: ImageData, style: ImageLayerStyle = DEFAULT_IMAGE_LAYER_STYLE
    ) -> None:
        """Replace layer 0 (the primary, frame-defining image) with *image* + *style*."""
        old = self._images[0] if self._images else None
        if self._images:
            self._images[0] = image
        else:
            self._images.append(image)
        assert image.width is not None and image.height is not None
        self._frame = (image.width, image.height)
        self._apply_layer_style(0, image, style)
        prune = [old.id] if old is not None and old.id != image.id else []
        self._push_background_pixels([image.id], prune)

    def add_layer(
        self, image: ImageData, style: ImageLayerStyle = DEFAULT_IMAGE_LAYER_STYLE
    ) -> int:
        """Append *image* as a new layer (max ``max_layers``) and return its index."""
        if len(self._images) >= self._max_layers:
            raise ValueError(f"ImageView supports at most {self._max_layers} images")
        self._images.append(image)
        index = len(self._images) - 1
        if self._frame is None:
            assert image.width is not None and image.height is not None
            self._frame = (image.width, image.height)
        self._apply_layer_style(index, image, style)
        self._push_background_pixels([image.id], [])
        return index

    def set_layer(
        self,
        index: int,
        image: ImageData | None,
        style: ImageLayerStyle = DEFAULT_IMAGE_LAYER_STYLE,
    ) -> None:
        """Overwrite layer *index* with *image* + *style*.

        ``image=None`` clears the layer in place (see :meth:`remove_layer`).
        """
        if image is None:
            self.remove_layer(index)
            return
        self._check_layer_index(index)
        old = self._images[index]
        self._images[index] = image
        if index == 0:
            assert image.width is not None and image.height is not None
            self._frame = (image.width, image.height)
        self._apply_layer_style(index, image, style)
        prune = [old.id] if old is not None and old.id != image.id else []
        self._push_background_pixels([image.id], prune)

    def remove_layer(self, index: int) -> None:
        """Clear layer *index* in place (stable index — no re-numbering).

        The slot becomes ``None`` and ``u_layer{index}_enabled`` is set to 0.
        Layer 0 is the frame-defining primary and cannot be removed; replace it
        with :meth:`set_image`.
        """
        if index == 0:
            raise ValueError(
                "cannot remove layer 0 (the frame-defining primary); "
                "use set_image to replace it"
            )
        self._check_layer_index(index)
        old = self._images[index]
        self._images[index] = None
        self._uniforms[f"u_layer{index}_enabled"] = 0
        prune = [old.id] if old is not None else []
        self._push_background_pixels([], prune)

    # -- background binding / push ---------------------------------

    def _bind_background(self, transport: Any, view_id: str, record_frame: Any) -> None:
        """Bind this view to a pane background so mutators push their own updates.

        *record_frame* is a callback ``(image_id, frame_or_none)`` the layout
        host supplies to keep its reconnect frame cache in sync (``None`` prunes).
        """
        self._transport = transport
        self._view_id = view_id
        self._record_frame = record_frame

    def _unbind_background(self) -> None:
        """Detach from the pane background (mutators become local-only again)."""
        self._transport = None
        self._view_id = None
        self._record_frame = None

    def _push_background_uniforms(self, patch: dict[str, float | int]) -> None:
        """Send a granular ``view_background_uniforms`` patch (no pixel bytes)."""
        if patch and self._transport is not None and self._view_id is not None:
            self._transport.send(
                {
                    "type": "view_background_uniforms",
                    "view_id": self._view_id,
                    "uniforms": dict(patch),
                }
            )

    def _push_background_pixels(
        self, changed_ids: list[str], prune_ids: list[str]
    ) -> None:
        """Send changed-layer frames + one ``view_background_image`` message."""
        if self._transport is None or self._view_id is None:
            return
        from ._image_wire import encode_image_frame

        for image in self._images:
            if image is None or image.data is None or image.id not in changed_ids:
                continue
            frame = encode_image_frame(
                image.id,
                image.data,
                codec=image.codec,
                jpeg_quality=image.jpeg_quality or 85,
            )
            self._transport.send_bytes(frame)
            if self._record_frame is not None:
                self._record_frame(image.id, frame)
        for image_id in prune_ids:
            if self._record_frame is not None:
                self._record_frame(image_id, None)
        self._transport.send(
            {
                "type": "view_background_image",
                "view_id": self._view_id,
                "image": self.background_meta(),
            }
        )

    def set_layer_style(self, index: int, style: ImageLayerStyle) -> None:
        """Merge *style* into layer *index* (``None`` fields keep current values)."""
        self._check_layer_index(index)
        before = dict(self._uniforms)
        self._merge_layer_style(index, style)
        after = self._uniforms
        patch = {
            name: value for name, value in after.items() if before.get(name) != value
        }
        self._push_background_uniforms(patch)

    def _apply_layer_style(
        self, index: int, image: ImageData, style: ImageLayerStyle
    ) -> None:
        """Apply *style* to layer *index*, resolving ``None`` to per-image defaults."""
        assert image.channels is not None and image.dtype is not None
        enabled = True if style.enabled is None else style.enabled
        opacity = 1.0 if style.opacity is None else style.opacity
        blend_code = (
            LayerBlendMode.NORMAL.code if style.blend is None else _blend_code(style.blend)
        )
        channel_code = (
            default_mode(image.channels)
            if style.channel is None
            else _channel_code(style.channel)
        )
        lo, hi = default_value_range(image.dtype)
        value_min = lo if style.value_min is None else float(style.value_min)
        value_max = hi if style.value_max is None else float(style.value_max)
        colormap_code = (
            int(ImageColormap.GRAY) if style.colormap is None else int(style.colormap)
        )
        self._uniforms.update(
            {
                f"u_layer{index}_enabled": int(enabled),
                f"u_layer{index}_opacity": float(opacity),
                f"u_layer{index}_blend": blend_code,
                f"u_layer{index}_mode": channel_code,
                f"u_layer{index}_colormap": colormap_code,
                f"u_layer{index}_value_min": value_min,
                f"u_layer{index}_value_max": value_max,
            }
        )
        if index == 0:
            # Keep the legacy global color uniforms in sync with the primary layer.
            self._uniforms["u_mode"] = channel_code
            self._uniforms["u_value_min"] = value_min
            self._uniforms["u_value_max"] = value_max

    def _merge_layer_style(self, index: int, style: ImageLayerStyle) -> None:
        """Merge *style* into layer *index* (``None`` fields keep current values)."""
        if style.enabled is not None:
            self._uniforms[f"u_layer{index}_enabled"] = int(style.enabled)
        if style.opacity is not None:
            self._uniforms[f"u_layer{index}_opacity"] = float(style.opacity)
        if style.blend is not None:
            self._uniforms[f"u_layer{index}_blend"] = _blend_code(style.blend)
        if style.channel is not None:
            self._uniforms[f"u_layer{index}_mode"] = _channel_code(style.channel)
        if style.colormap is not None:
            self._uniforms[f"u_layer{index}_colormap"] = int(style.colormap)
        if style.value_min is not None:
            self._uniforms[f"u_layer{index}_value_min"] = float(style.value_min)
        if style.value_max is not None:
            self._uniforms[f"u_layer{index}_value_max"] = float(style.value_max)

    # -- uniforms -----------------------------------------------------

    @property
    def uniforms(self) -> dict[str, float | int]:
        """A copy of the current uniform values."""
        return dict(self._uniforms)

    def set_uniform(self, name: str, value: float | int) -> None:
        """Set a uniform value (emitted as a JSON ``image_update`` later)."""
        self._uniforms[name] = value
        self._push_background_uniforms({name: value})

    def register_uniform(self, name: str, default: float | int) -> None:
        """Register a uniform with a default, keeping an existing value."""
        self._uniforms.setdefault(name, default)

    def _check_layer_index(self, index: int) -> None:
        """Raise :class:`IndexError` when *index* does not address an image layer."""
        if not 0 <= index < len(self._images):
            raise IndexError(
                f"layer index {index} out of range [0, {len(self._images) - 1}]"
            )

    def set_layer_enabled(self, index: int, enabled: bool) -> None:
        """Enable (or disable) the image layer at *index*."""
        self._check_layer_index(index)
        self.set_uniform(f"u_layer{index}_enabled", int(enabled))

    def set_layer_opacity(self, index: int, opacity: float) -> None:
        """Set the image layer opacity at *index* (0..1)."""
        self._check_layer_index(index)
        self.set_uniform(f"u_layer{index}_opacity", float(opacity))

    def set_layer_blend(self, index: int, blend: LayerBlendMode | int) -> None:
        """Set the blend mode of the image layer at *index*."""
        self._check_layer_index(index)
        self.set_uniform(f"u_layer{index}_blend", _blend_code(blend))

    def set_layer_value_range(self, index: int, value_min: float, value_max: float) -> None:
        """Set the normalization value range of the image layer at *index*."""
        self._check_layer_index(index)
        self.set_uniform(f"u_layer{index}_value_min", float(value_min))
        self.set_uniform(f"u_layer{index}_value_max", float(value_max))

    def set_layer_channel(self, index: int, mode: ImageChannelMode | int) -> None:
        """Set the channel mapping mode of the image layer at *index*."""
        self._check_layer_index(index)
        self.set_uniform(f"u_layer{index}_mode", int(mode))

    # -- shader -------------------------------------------------------

    def register_shader(self, fragment: str, vertex: str | None = None) -> None:
        """Register a custom fragment (and optional vertex) shader source."""
        self._fragment = fragment
        self._vertex = vertex

    @property
    def shader(self) -> dict[str, str | None]:
        """The custom shader sources (``fragment``/``vertex``); both ``None`` → default."""
        return {"fragment": self._fragment, "vertex": self._vertex}

    # -- serialization ------------------------------------------------

    def serialized_images(self) -> list[dict[str, Any] | None]:
        """Serialize every image layer slot to the canonical per-image metadata.

        Cleared slots serialize as ``None`` so the frontend keeps ``images[i]``
        aligned with ``uImage{i}`` (stable-index removal).
        """
        return [self._serialize_image(img, i) for i, img in enumerate(self._images)]

    def _serialize_state(self) -> dict[str, Any]:
        """Serialize the shared image + shader + uniform state (no scene envelope)."""
        return {
            "images": self.serialized_images(),
            "shader": {"fragment": self._fragment, "vertex": self._vertex},
            "uniforms": dict(self._uniforms),
            "max_layers": self._max_layers,
        }

    def background_meta(self) -> dict[str, Any]:
        """Serialize this view as ``CameraView.background_image`` metadata.

        Keeps the flat primary-image fields (for framing/``uImageAspect``) and
        adds the full ``images`` layer list plus the shared ``shader`` /
        ``uniforms`` / ``max_layers`` state.  Mirrors ``_image_view_meta`` but
        lives on ``ImageView`` so a bound background can emit
        ``view_background_image`` without importing ``views._helpers``.
        """
        primary = self.primary_image
        meta: dict[str, Any] = {} if primary is None else primary.layer_meta()
        meta["images"] = self.serialized_images()
        meta["shader"] = dict(self.shader)
        meta["uniforms"] = dict(self.uniforms)
        meta["max_layers"] = self.max_layers
        return meta

    def _serialize(self) -> dict[str, Any]:
        """Serialize to the canonical ``image`` entity dict (README contract)."""
        result = self._serialize_state()
        result.update(
            {
                "id": self.id,
                "layer": "scene",
                "kind": "image",
                "frame": {"width": self.frame[0], "height": self.frame[1]},
            }
        )
        return result

    def _serialize_image(
        self, image: ImageData | None, index: int
    ) -> dict[str, Any] | None:
        """Serialize one image layer (metadata only — pixels travel as bytes)."""
        if image is None:
            return None
        meta = image.layer_meta()
        prefix = f"u_layer{index}_"
        for key in (
            "enabled",
            "opacity",
            "blend",
            "mode",
            "colormap",
            "value_min",
            "value_max",
        ):
            meta[key] = self._uniforms[f"{prefix}{key}"]
        return meta


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
    (plane + textures + shader/uniform state), an :class:`InteractionSurface`
    (a per-pane ``z = 0`` interaction plane) for drag/click, and an overlay
    group for drawing in pixel coordinates.
    """

    def __init__(
        self,
        target: Any,
        *,
        image_id: str | None = None,
        stretch: StretchMode = "fit",
        border_px: float = 0.0,
        min_zoom: float = 0.25,
        on_drag: Callable[[DragEvent, ImageCanvas], Awaitable[bool]] | None = None,
        on_drag_start: Callable[[DragEvent, ImageCanvas], Awaitable[None]]
        | None = None,
        on_drag_end: Callable[[DragEvent, ImageCanvas], Awaitable[None]] | None = None,
        on_click: Callable[[ClickEvent, ImageCanvas], Awaitable[None]] | None = None,
        drag_handlers: list[DragBinding[ImageCanvas]] | None = None,
        click_handlers: list[ClickBinding[ImageCanvas]] | None = None,
        controls: dict[MouseButton, CameraAction | None] | None = None,
        cursor: str | None = None,
    ) -> None:
        viz = _coerce_visualizer(target)
        self._image_id = (
            image_id if image_id is not None else f"img{next(_image_id_counter)}"
        )
        self._image_view = ImageView(self._image_id)
        self._stretch = _validate_stretch(stretch)
        self._border_px = float(border_px)
        self._min_zoom = float(min_zoom)
        if self._min_zoom <= 0.0:
            raise ValueError(f"min_zoom must be positive, got {min_zoom!r}")

        self._scene_name = f"imgc{next(_image_canvas_counter)}"
        self._handle = viz.scene(
            self._scene_name, space_dim=2, add_axes=False, add_grid=False
        )
        if controls is not None:
            self._handle.scene.config.controls = controls
        self._transport = getattr(viz, "_transport", None)
        self._overlay = self._handle.add_group(f"{self._scene_name}_overlay")
        self._overlay_refs: list[Any] = []

        # Wrap handlers in-place so the user's own binding objects are shared
        # with the surface — mutating ``binding.enabled`` later toggles its trigger.
        for binding in drag_handlers or []:
            binding.handler = cast(Any, self._bind_drag(binding.handler))
        for binding in click_handlers or []:
            binding.handler = cast(Any, self._bind_click(binding.handler))

        self._surface = InteractionSurface(
            PlanarMapper(),
            on_drag=self._bind_drag(on_drag) if on_drag is not None else None,
            on_drag_start=(
                self._bind_event(on_drag_start) if on_drag_start is not None else None
            ),
            on_drag_end=(
                self._bind_event(on_drag_end) if on_drag_end is not None else None
            ),
            on_click=self._bind_click(on_click) if on_click is not None else None,
            drag_bindings=cast(
                "list[DragBinding[InteractionSurface]]", list(drag_handlers or [])
            ),
            click_bindings=cast(
                "list[ClickBinding[InteractionSurface]]", list(click_handlers or [])
            ),
            cursor=cursor,
        )

    # -- handler wrapping -----------------------------------------
    # Handlers are registered with the InteractionSurface, which passes its own
    # instance as the second argument.  We wrap the user's handlers so that
    # second argument is this ImageCanvas instead.

    def _bind_drag(
        self, handler: Callable[[DragEvent, ImageCanvas], Awaitable[bool]]
    ) -> SurfaceDragHandler:
        async def wrapped(event: DragEvent, _surface: InteractionSurface) -> bool:
            return await handler(event, self)

        return wrapped

    def _bind_click(
        self, handler: Callable[[ClickEvent, ImageCanvas], Awaitable[None]]
    ) -> SurfaceClickHandler:
        async def wrapped(event: ClickEvent, _surface: InteractionSurface) -> None:
            await handler(event, self)

        return wrapped

    def _bind_event(
        self, handler: Callable[[DragEvent, ImageCanvas], Awaitable[None]]
    ) -> SurfaceEventHandler:
        async def wrapped(event: DragEvent, _surface: InteractionSurface) -> None:
            await handler(event, self)

        return wrapped

    # -- image / shader / uniform ---------------------------------

    @property
    def image_view(self) -> ImageView:
        """The underlying :class:`ImageView` (images + shader + uniforms)."""
        return self._image_view

    def set_image(
        self, image: ImageData, style: ImageLayerStyle = DEFAULT_IMAGE_LAYER_STYLE
    ) -> None:
        """Replace the primary image (with *style*), re-frame the camera, and sync it."""
        self._image_view.set_image(image, style)
        self.fit_to_image()
        self._sync_image()

    def add_layer(
        self, image: ImageData, style: ImageLayerStyle = DEFAULT_IMAGE_LAYER_STYLE
    ) -> int:
        """Append a new layer (max 4) with *style* and return its index."""
        index = self._image_view.add_layer(image, style)
        self._sync_image()
        return index

    def set_layer(
        self,
        index: int,
        image: ImageData,
        style: ImageLayerStyle = DEFAULT_IMAGE_LAYER_STYLE,
    ) -> None:
        """Overwrite layer *index* with *image* + *style* and sync it."""
        self._image_view.set_layer(index, image, style)
        self._sync_image()

    def set_layer_style(self, index: int, style: ImageLayerStyle) -> None:
        """Merge *style* into layer *index* and push a granular uniform patch."""
        before = self._image_view.uniforms
        self._image_view.set_layer_style(index, style)
        after = self._image_view.uniforms
        patch = {name: value for name, value in after.items() if before.get(name) != value}
        self._push_uniforms(patch)

    def set_uniform(self, name: str, value: float | int) -> None:
        """Set a shader uniform value (JSON ``image_update``, no image bytes)."""
        self._image_view.set_uniform(name, value)
        self._push_uniforms({name: value})

    def _push_uniforms(self, patch: dict[str, float | int]) -> None:
        """Send a granular ``image_update`` patch and re-snapshot the node payload."""
        if patch and self._transport is not None:
            self._transport.send(
                {
                    "type": "image_update",
                    "scene": self._scene_name,
                    "id": self._image_view.id,
                    "uniforms": dict(patch),
                }
            )
        self._resync_node()

    def _resync_node(self) -> None:
        """Re-serialize the image node so a full-state push reflects the latest state.

        The granular ``image_update`` patch is the live path; re-snapshotting the
        node here keeps the authoritative payload (used by the full-state push on
        connect and by reconnects) in sync with the live uniform dict, so changes
        made before the server boots are not lost.
        """
        if not self._image_view.images:
            return
        self._handle.scene.upsert_image(
            self._image_view.id,
            self._image_view._serialize(),
            images=self._image_view.images,
        )

    def register_uniform(self, name: str, default: float | int) -> None:
        """Register a shader uniform with a default (keeps an existing value)."""
        self._image_view.register_uniform(name, default)
        self._resync_node()

    def register_shader(self, fragment: str, vertex: str | None = None) -> None:
        """Register a custom fragment (and optional vertex) shader."""
        self._image_view.register_shader(fragment, vertex)
        self._resync_node()

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
    def surface(self) -> InteractionSurface:
        """The :class:`~pytanga.viz.InteractionSurface` for the image plane."""
        return self._surface

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
        """A :class:`~pytanga.viz.SceneView` pane for the dedicated scene.

        The pane carries this canvas's :class:`~pytanga.viz.InteractionSurface`,
        so pointer events on the pane are resolved against the image plane.
        """
        from .views import SceneView

        return SceneView(self._scene_name, surface=self._surface)

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
                min_zoom=self._min_zoom,
            )
        )

    def _sync_image(self) -> None:
        """Register the image entity and send its pixel bytes + uniforms."""
        from ._image_wire import encode_image_frame

        # Auto-register any tiled pyramids so the /image/... tile route is live
        # before the frontend tries to fetch its tiles.
        for img in self._image_view.images:
            if img.source == "tiled" and img.tiled is not None:
                self._handle._viz._register_pyramid(img.tiled)

        payload = self._image_view._serialize()
        self._handle.scene.upsert_image(
            self._image_view.id, payload, images=self._image_view.images
        )

        if self._transport is None:
            return
        for img in self._image_view.images:
            if img.data is not None:
                self._transport.send_bytes(
                    encode_image_frame(
                        img.id,
                        img.data,
                        codec=img.codec,
                        jpeg_quality=img.jpeg_quality or 85,
                    )
                )
        self._transport.send(
            {
                "type": "image_update",
                "scene": self._scene_name,
                "id": self._image_view.id,
                "uniforms": dict(self._image_view.uniforms),
            }
        )
        self._handle.flush()

    # -- interaction toggles / cursor -------------------------

    def set_cursor(self, cursor: str | None) -> None:
        """Set the mouse cursor shown over this canvas's scene (``None`` clears it)."""
        self._handle.set_cursor(cursor)

    def set_handler_enabled(self, enabled: bool) -> None:
        """Enable or disable the image plane's general drag handler."""
        self._surface.set_handler_enabled(enabled)

    def set_click_enabled(self, enabled: bool) -> None:
        """Enable or disable the image plane's general click handler."""
        self._surface.set_click_enabled(enabled)

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable all interaction on the image plane."""
        self._surface.set_enabled(enabled)

    def refresh_interaction(self) -> None:
        """Re-push the image plane's interaction config.

        Call after mutating a :class:`DragBinding` / :class:`ClickBinding`
        ``enabled`` flag so the new trigger set reaches the frontend.
        """
        self._surface.refresh_interaction()

    def on_key(self, key: str, handler: Any, *, modifiers: Any = None) -> None:
        """Register an async handler for a key press in this canvas's scene."""
        self._handle.on_key(key, handler, modifiers=modifiers)
