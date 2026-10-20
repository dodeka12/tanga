# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Depth image (2.5D surface) data model.

Pure data + validation for the ``depth_image`` scene entity.  ``DepthImageData``
bundles the source numpy arrays (color image, depth, segmentation); ``DepthImage``
turns them into the wire content payload plus the binary-frame ``ImageData``
objects.  No server/rendering imports, so the module is unit-testable in
isolation (mirrors ``image.py``).

The three source arrays may have different pixel resolutions (only the extent
must match).  Downscaling happens here, Python-side, before encoding, so only
the mesh/texture resolution actually needed is transmitted.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any

import numpy as np

from pytanga.geometry.transform import Transform

from .image import EImageCodec, ImageData

__all__ = [
    "DepthImageMode",
    "DepthColormap",
    "DepthImageData",
    "DepthImage",
    "compute_pinhole_positions",
    "MAX_SELECTED_SEGMENTS",
    "DEFAULT_MISSING_DEPTH",
]

#: Maximum number of segment ids carried by the ``u_selected_segments`` uniform.
MAX_SELECTED_SEGMENTS = 16

#: Sentinel written into the depth array for non-finite (NaN/±inf) values.
DEFAULT_MISSING_DEPTH = -3.402823466e38

_SUPPORTED_RASTER_DTYPES = (
    np.dtype("uint8"),
    np.dtype("uint16"),
    np.dtype("float32"),
)


class DepthImageMode(IntEnum):
    """How the surface fragment shader colors the mesh."""

    DEPTH = 0
    IMAGE = 1
    PLAIN = 2

    @classmethod
    def from_str(cls, value: str) -> "DepthImageMode":
        """Resolve a ``"depth"``/``"image"``/``"plain"`` string to its code."""
        mapping = {"depth": cls.DEPTH, "image": cls.IMAGE, "plain": cls.PLAIN}
        try:
            return mapping[value]
        except KeyError as exc:
            raise ValueError(f"Unknown depth render mode {value!r}") from exc


class DepthColormap(IntEnum):
    """Built-in depth color maps (selectable via ``u_colormap``)."""

    VIRIDIS = 0
    TURBO = 1
    GRAY = 2

    @classmethod
    def from_str(cls, value: str) -> "DepthColormap":
        """Resolve a ``"viridis"``/``"turbo"``/``"gray"`` string to its code."""
        mapping = {
            "viridis": cls.VIRIDIS,
            "turbo": cls.TURBO,
            "gray": cls.GRAY,
            "grayscale": cls.GRAY,
        }
        try:
            return mapping[value]
        except KeyError as exc:
            raise ValueError(f"Unknown depth colormap {value!r}") from exc


def _hex_to_rgb(color: str) -> list[float]:
    """Convert a ``#rrggbb`` (or ``#rgb``) hex color to ``[r, g, b]`` floats."""
    raw = color.strip().lstrip("#")
    if len(raw) == 3:
        raw = "".join(c * 2 for c in raw)
    if len(raw) != 6:
        raise ValueError(f"Expected a #rrggbb color, got {color!r}")
    try:
        return [int(raw[i : i + 2], 16) / 255.0 for i in (0, 2, 4)]
    except ValueError as exc:
        raise ValueError(f"Expected a #rrggbb color, got {color!r}") from exc


def _validate_raster(arr: np.ndarray, name: str) -> np.ndarray:
    """Validate a color raster (2-D or 3-D with 1/3/4 channels)."""
    if arr.ndim == 2:
        pass
    elif arr.ndim == 3 and arr.shape[2] in (1, 3, 4):
        pass
    else:
        raise ValueError(
            f"{name} must be 2-D (H×W) or 3-D (H×W×C, C∈{{1,3,4}}), got ndim={arr.ndim}"
        )
    if arr.dtype not in _SUPPORTED_RASTER_DTYPES:
        raise ValueError(
            f"{name} dtype must be uint8, uint16, or float32, got {arr.dtype!r}"
        )
    return np.ascontiguousarray(arr)


def _normalize_depth(arr: np.ndarray, missing_depth: float) -> np.ndarray:
    """Cast depth to float32 and replace non-finite values with the sentinel."""
    depth = np.ascontiguousarray(arr, dtype=np.float32)
    if depth.ndim != 2:
        raise ValueError(f"depth must be 2-D (H×W), got ndim={depth.ndim}")
    out = depth.copy()
    out[~np.isfinite(out)] = missing_depth
    return out


def _validate_segmentation(arr: np.ndarray) -> np.ndarray:
    """Validate a segmentation mask (2-D integer labels, dtype preserved)."""
    seg = np.ascontiguousarray(arr)
    if seg.ndim != 2:
        raise ValueError(
            f"segmentation must be 2-D (H×W) integer labels, got ndim={seg.ndim}"
        )
    if seg.dtype not in _SUPPORTED_RASTER_DTYPES:
        raise ValueError(
            f"segmentation dtype must be uint8, uint16, or float32, got {seg.dtype!r}"
        )
    return seg


def _nearest_downscale(arr: np.ndarray, width: int, height: int) -> np.ndarray:
    """Nearest-neighbour downscale (preserves the sentinel and integer labels)."""
    h, w = arr.shape[0], arr.shape[1]
    if (w, h) == (width, height):
        return arr
    xs = np.clip(((np.arange(width) + 0.5) * w / width).astype(np.int64), 0, w - 1)
    ys = np.clip(((np.arange(height) + 0.5) * h / height).astype(np.int64), 0, h - 1)
    return arr[np.ix_(ys, xs)]


def _bilinear_downscale(arr: np.ndarray, width: int, height: int) -> np.ndarray:
    """Bilinear downscale via Pillow for the color image.

    Resizes with Pillow's bilinear filter.  Multi-channel rasters are resized
    channel-by-channel (each channel keeps its dtype), which covers every
    supported raster dtype (``uint8``/``uint16``/``float32``) and channel count
    (1/3/4).  Raises :class:`ImportError` when Pillow is unavailable.
    """
    h, w = arr.shape[:2]
    if (w, h) == (width, height):
        return arr
    try:
        from PIL import Image
    except ImportError as exc:
        raise ImportError(
            "Bilinear image downscale requires Pillow; install it "
            "(e.g. `pip install pillow`)"
        ) from exc

    resample = Image.Resampling.BILINEAR
    if arr.ndim == 2:
        image = Image.fromarray(arr)
        return np.asarray(image.resize((width, height), resample), dtype=arr.dtype)
    return np.stack(
        [
            np.asarray(
                Image.fromarray(arr[:, :, c]).resize((width, height), resample),
                dtype=arr.dtype,
            )
            for c in range(arr.shape[2])
        ],
        axis=-1,
    )


def _scaled_side(side: int, scale: float | None) -> int:
    """Resolve a downscaled side length from a fraction (``None`` → full)."""
    if scale is None or float(scale) >= 1.0:
        return side
    return max(1, int(round(side * float(scale))))


def _frame_codec(
    codec: Any, arr: np.ndarray, *, allow_jpeg: bool
) -> EImageCodec | None:
    """Resolve a per-frame codec honoring the JPEG constraints.

    ``None`` keeps the wire auto-selection.  Explicit JPEG is only honored for
    ``allow_jpeg`` frames whose array qualifies (uint8, 1/3 channels); otherwise
    it falls back to lossless ZLIB.
    """
    if codec is None:
        return None
    resolved = codec if isinstance(codec, EImageCodec) else EImageCodec(int(codec))
    jpeg_ok = arr.dtype == np.dtype("uint8") and (
        arr.ndim == 2 or arr.shape[2] in (1, 3)
    )
    if resolved is EImageCodec.JPEG and (not allow_jpeg or not jpeg_ok):
        return EImageCodec.ZLIB
    return resolved


def _lossless_codec(codec: Any) -> EImageCodec:
    """Resolve a lossless frame codec for depth/segmentation (never JPEG).

    ``None`` and an explicit JPEG both fall back to ZLIB; RAW/ZLIB pass through.
    Depth (float32) and segmentation (integer labels) must never be lossy.
    """
    if codec is None:
        return EImageCodec.ZLIB
    resolved = codec if isinstance(codec, EImageCodec) else EImageCodec(int(codec))
    if resolved is EImageCodec.JPEG:
        return EImageCodec.ZLIB
    return resolved


def _image_meta(img: ImageData) -> dict[str, Any]:
    """Serialize one frame's metadata (pixels travel as binary frames)."""
    assert img.width is not None and img.height is not None
    assert img.channels is not None and img.dtype is not None
    return {
        "id": img.id,
        "width": img.width,
        "height": img.height,
        "channels": img.channels,
        "dtype": int(img.dtype),
        "source": img.source,
    }


def _resolve_camera(camera: Any) -> tuple[float, float, float, float]:
    """Resolve ``(fx, fy, cx, cy)`` from a camera value.

    Accepts a ``CameraCalibration`` (``K``) or a ``PinholeCamera``
    (``fx``/``fy``/``cx``/``cy`` fields).
    """
    if hasattr(camera, "K"):
        k = camera.K.data
        return (float(k[0, 0]), float(k[1, 1]), float(k[0, 2]), float(k[1, 2]))
    return (
        float(camera.fx),
        float(camera.fy),
        float(camera.cx),
        float(camera.cy),
    )


def camera_transform(camera: Any, apply_pose: bool = True) -> Transform | None:
    """Return the camera→world :class:`Transform` for a ``CameraCalibration``.

    Returns ``None`` when *camera* is ``None``, *apply_pose* is ``False``, or the
    camera carries no pose (e.g. a bare ``PinholeCamera``).  The matrix→TRS
    decomposition reuses :class:`pytanga.geometry.Transform`.
    """
    if camera is None or not apply_pose or not hasattr(camera, "camera_to_world"):
        return None
    return Transform.from_matrix(camera.camera_to_world())


#: Depth-kind aliases → canonical name.  The canonical names are "axial"
#: (depth along the optical axis), "radial" (distance along the projection ray),
#: and "inverse" (inverse depth 1/Z).
_DEPTH_KIND_ALIASES = {
    "axial": "axial",
    "z": "axial",
    "orthogonal": "axial",
    "radial": "radial",
    "range": "radial",
    "inverse": "inverse",
    "disparity": "inverse",
}


def normalize_depth_kind(value: str) -> str:
    """Resolve a depth-kind string (or alias) to its canonical name.

    Canonical kinds: ``"axial"`` (depth along the optical axis, i.e. ``Z_c``),
    ``"radial"`` (Euclidean distance along the projection ray), and
    ``"inverse"`` (inverse depth ``1/Z``).  Accepted aliases: ``"z"`` /
    ``"orthogonal"`` → axial, ``"range"`` → radial, ``"disparity"`` → inverse.
    """
    key = value.lower()
    try:
        return _DEPTH_KIND_ALIASES[key]
    except KeyError as exc:
        raise ValueError(
            f"depth_kind must be one of {sorted(_DEPTH_KIND_ALIASES)}, got {value!r}"
        ) from exc


def grazing_angle_to_stretch(angle_deg: float | None) -> float:
    """Convert a max grazing angle (degrees) to the ``u_max_stretch`` uniform.

    The stretch filter discards surface fragments that are more edge-on to the
    viewing ray than ``angle_deg``.  ``None`` or ``<= 0`` disables the filter
    (returns ``0.0``, the "off" sentinel); otherwise the value is the tangent of
    the angle, i.e. the apparent depth slope (``tan(grazing angle)``) the vertex
    shader compares against ``vStretch``.
    """
    if angle_deg is None:
        return 0.0
    angle_deg = float(angle_deg)
    if angle_deg <= 0.0:
        return 0.0
    if angle_deg >= 90.0:
        raise ValueError("max_grazing_angle must be < 90 degrees")
    return math.tan(math.radians(angle_deg))


def compute_pinhole_positions(
    depth: np.ndarray,
    fx: float,
    fy: float,
    cx: float,
    cy: float,
    *,
    depth_kind: str = "axial",
    depth_scale: float = 1.0,
    depth_offset: float = 0.0,
    mesh_scale: float = 1.0,
    max_mesh_size: int | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute camera-frame vertex positions for the pinhole depth mode.

    ``depth`` is the depth array (its resolution is treated as the reference
    frame here).  Pixel ``(u, v)`` are reference-frame pixel centers.  Returns
    ``(positions, u, v)`` where ``positions`` is ``(N, 3)`` in camera frame
    (x right, y down, z forward).  This is the canonical reference for the
    frontend vertex math.

    ``depth_kind`` selects the raw-depth interpretation — ``"axial"`` (depth
    along the optical axis), ``"radial"`` (Euclidean distance along the
    projection ray), or ``"inverse"`` (inverse depth ``1/Z``); aliases ``"z"``,
    ``"range"``, ``"disparity"`` are accepted.  ``depth_scale``/``depth_offset``
    convert the raw depth value to world units first (``depth_scale`` is "world
    units per depth unit").  The returned positions are **unclamped** (pure
    unprojection); the frontend additionally clamps the axial depth ``Z`` to
    ``[depth_min, depth_max]``, which are always expressed in axial metres.
    """
    kind = normalize_depth_kind(depth_kind)

    depth_h, depth_w = depth.shape
    scale = max(0.0, min(1.0, float(mesh_scale)))
    vert_w = max(2, int(round(depth_w * scale)))
    vert_h = max(2, int(round(depth_h * scale)))
    if max_mesh_size is not None:
        longest = max(vert_w, vert_h)
        if longest > int(max_mesh_size):
            factor = int(max_mesh_size) / longest
            vert_w = max(2, int(round(vert_w * factor)))
            vert_h = max(2, int(round(vert_h * factor)))

    us = (np.arange(vert_w) + 0.5) * (depth_w / vert_w)
    vs = (np.arange(vert_h) + 0.5) * (depth_h / vert_h)

    d = _nearest_downscale(depth, vert_w, vert_h)
    metric = (d.astype(np.float64) - depth_offset) * depth_scale
    xnorm = (us[None, :] - cx) / fx
    ynorm = (vs[:, None] - cy) / fy
    if kind == "radial":
        z = metric / np.sqrt(xnorm**2 + ynorm**2 + 1.0)
    elif kind == "inverse":
        with np.errstate(divide="ignore", invalid="ignore"):
            z = np.where(np.abs(metric) > 1e-9, 1.0 / metric, 0.0)
    else:  # axial
        z = metric

    x = xnorm * z
    y = ynorm * z

    positions = np.stack([x.ravel(), y.ravel(), z.ravel()], axis=1)
    uu, vv = np.meshgrid(us, vs)
    return positions, uu.ravel(), vv.ravel()


@dataclass
class DepthImageData:
    """Bundle of source arrays for a depth image.

    ``image`` and ``segmentation`` are optional; ``depth`` is required.  The
    three arrays may have different pixel resolutions (only the extent must
    match).  Non-finite depth values are replaced with ``missing_depth``.
    """

    depth: np.ndarray
    image: np.ndarray | None = None
    segmentation: np.ndarray | None = None
    missing_depth: float = DEFAULT_MISSING_DEPTH

    def __post_init__(self) -> None:
        if self.depth is None:  # type: ignore[comparison-overlap]  # defensive
            raise ValueError("depth is required")
        self.depth = _normalize_depth(self.depth, self.missing_depth)
        if self.image is not None:
            self.image = _validate_raster(self.image, "image")
        if self.segmentation is not None:
            self.segmentation = _validate_segmentation(self.segmentation)

    @property
    def frame(self) -> tuple[int, int]:
        """Reference pixel extent ``(width, height)`` (image if present, else depth)."""
        arr = self.image if self.image is not None else self.depth
        return (int(arr.shape[1]), int(arr.shape[0]))

    @property
    def has_image(self) -> bool:
        """``True`` when a color image is present."""
        return self.image is not None

    @property
    def has_segmentation(self) -> bool:
        """``True`` when a segmentation mask is present."""
        return self.segmentation is not None

    def segmentation_ids(self) -> list[int]:
        """Return the sorted unique integer labels of the segmentation mask."""
        if self.segmentation is None:
            return []
        return [int(v) for v in np.unique(self.segmentation).tolist()]


@dataclass
class DepthImage:
    """A viz-only scene entity that renders a depth map as a 2.5D surface.

    Wraps a :class:`DepthImageData` plus the presentation fields (custom shader
    + uniforms + initial segment selection).  Pass it to ``viz.add(...)`` /
    ``viz.new(...)`` with a :class:`~pytanga.viz.DepthImageStyle`.
    """

    data: DepthImageData
    fragment: str | None = None
    vertex: str | None = None
    uniforms: dict[str, float | int] = field(default_factory=dict)
    selected_segments: list[int] | None = None

    def _serialize_uniforms(self, style: dict[str, Any]) -> dict[str, Any]:
        """Serialize the uniform block (README contract) from the resolved style."""
        render_mode = DepthImageMode.from_str(str(style["render_mode"]))
        colormap = DepthColormap.from_str(str(style["colormap"]))
        uniforms: dict[str, Any] = {
            "u_render_mode": int(render_mode),
            "u_colormap": int(colormap),
            "u_depth_scale": float(style["depth_scale"]),
            "u_depth_offset": float(style["depth_offset"]),
            "u_depth_min": float(style["depth_min"]),
            "u_depth_max": float(style["depth_max"]),
            "u_missing_depth": float(self.data.missing_depth),
            "u_discard_missing": 1 if style["discard_missing"] else 0,
            "u_max_stretch": grazing_angle_to_stretch(style.get("max_grazing_angle")),
            "u_seg_enabled": 0,
            "u_num_selected": 0,
            "u_selected_segments": [0] * MAX_SELECTED_SEGMENTS,
            "u_color": _hex_to_rgb(str(style["color"])),
            "u_opacity": float(style["opacity"]),
            "u_shininess": float(style["shininess"]),
            "u_specular": _hex_to_rgb(str(style["specular"])),
        }
        selected = [int(v) for v in (self.selected_segments or [])]
        selected = selected[:MAX_SELECTED_SEGMENTS]
        if selected:
            uniforms["u_seg_enabled"] = 1
            uniforms["u_num_selected"] = len(selected)
            uniforms["u_selected_segments"] = selected + [0] * (
                MAX_SELECTED_SEGMENTS - len(selected)
            )
        for name, value in self.uniforms.items():
            uniforms[name] = value
        return uniforms

    def _serialize_mesh(
        self, style: dict[str, Any], depth_w: int, depth_h: int
    ) -> dict[str, Any]:
        """Resolve the mesh grid from the *depth* resolution.

        The mesh has one vertex per depth sample (pixel center), so
        ``segments_u/v`` are ``samples - 1``; ``mesh_scale``/``max_mesh_size``
        decimate the depth samples before the grid is built.
        """
        scale = float(style["mesh_scale"])
        scale = max(0.0, min(1.0, scale))
        vert_w = max(2, int(round(depth_w * scale)))
        vert_h = max(2, int(round(depth_h * scale)))
        max_size = style.get("max_mesh_size")
        if max_size is not None:
            longest = max(vert_w, vert_h)
            if longest > int(max_size):
                factor = int(max_size) / longest
                vert_w = max(2, int(round(vert_w * factor)))
                vert_h = max(2, int(round(vert_h * factor)))
        mesh: dict[str, Any] = {
            "segments_u": vert_w - 1,
            "segments_v": vert_h - 1,
            "world_scale": float(style["world_scale"]),
        }
        camera = style.get("camera")
        if camera is not None:
            fx, fy, cx, cy = _resolve_camera(camera)
            mesh["camera"] = {
                "fx": fx,
                "fy": fy,
                "cx": cx,
                "cy": cy,
                "depth_kind": normalize_depth_kind(style.get("depth_kind") or "axial"),
            }
        return mesh

    def _build(
        self, style: dict[str, Any], entity_id: str
    ) -> tuple[dict[str, Any], list[ImageData]]:
        """Downscale + encode the arrays and return ``(content, frames)``.

        ``content`` is the ``depth_image`` content payload (frame / depth /
        image / segmentation / shader / mesh / uniforms); ``frames`` are the
        ``ImageData`` objects whose bytes travel as binary frames.
        """
        frame_w, frame_h = self.data.frame
        depth_h, depth_w = self.data.depth.shape
        mesh = self._serialize_mesh(style, depth_w, depth_h)
        seg_u = int(mesh["segments_u"])
        seg_v = int(mesh["segments_v"])
        codec = style.get("codec")
        jpeg_quality = style.get("jpeg_quality")

        frames: list[ImageData] = []

        depth = _nearest_downscale(self.data.depth, seg_u + 1, seg_v + 1)
        depth_img = ImageData(
            f"{entity_id}.depth",
            data=depth,
            codec=_lossless_codec(codec),
            jpeg_quality=jpeg_quality,
            tile_max_dim=None,
            tile_max_bytes=None,
        )
        frames.append(depth_img)

        image_meta: dict[str, Any] | None = None
        if self.data.image is not None:
            h, w = self.data.image.shape[0], self.data.image.shape[1]
            image = _bilinear_downscale(
                self.data.image,
                _scaled_side(w, style.get("image_scale")),
                _scaled_side(h, style.get("image_scale")),
            )
            image_img = ImageData(
                f"{entity_id}.image",
                data=image,
                codec=_frame_codec(codec, image, allow_jpeg=True),
                jpeg_quality=jpeg_quality,
                tile_max_dim=None,
                tile_max_bytes=None,
            )
            frames.append(image_img)
            image_meta = _image_meta(image_img)

        segmentation_meta: dict[str, Any] | None = None
        if self.data.segmentation is not None:
            h, w = self.data.segmentation.shape[0], self.data.segmentation.shape[1]
            seg_scale = style.get("segmentation_scale")
            if seg_scale is None:
                seg_scale = style.get("image_scale")
            segmentation = _nearest_downscale(
                self.data.segmentation,
                _scaled_side(w, seg_scale),
                _scaled_side(h, seg_scale),
            )
            seg_img = ImageData(
                f"{entity_id}.seg",
                data=segmentation,
                codec=_lossless_codec(codec),
                jpeg_quality=jpeg_quality,
                tile_max_dim=None,
                tile_max_bytes=None,
            )
            frames.append(seg_img)
            segmentation_meta = _image_meta(seg_img)

        content: dict[str, Any] = {
            "frame": {"width": frame_w, "height": frame_h},
            "depth": _image_meta(depth_img),
            "image": image_meta,
            "segmentation": segmentation_meta,
            "shader": {"fragment": self.fragment, "vertex": self.vertex},
            "mesh": mesh,
            "uniforms": self._serialize_uniforms(style),
        }
        return content, frames
