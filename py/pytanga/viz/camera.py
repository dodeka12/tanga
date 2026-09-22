# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Camera configuration types and view builders for the Tanga 3D viewer.

This module defines the raw camera configuration classes that are sent to the
frontend, plus the convenience builders that translate high-level view
specifications (:class:`View2DConfig`, :class:`View3dConfig`) into fully
populated camera configs.

The camera config classes carry only the values the frontend needs to
construct an orthographic or perspective camera.  The final frustum is derived
by the frontend from the live browser viewport so the requested view is always
shown correctly regardless of the requested extents and the browser window
aspect/size.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, fields
from enum import StrEnum
from typing import Any, Literal, cast

import numpy as np

from pytanga.geometry.frame import CoordinateFrame, OpenCVFrame
from pytanga.geometry.matrix import Matrix


StretchMode = Literal["fit", "fill", "fill_x", "fill_y"]


class CameraAction(StrEnum):
    """Camera navigation action a mouse button can be bound to.

    Mirrors Three.js ``OrbitControls`` mouse actions (``ROTATE``/``DOLLY``/
    ``PAN``).  Used by :attr:`SceneConfig.controls` to rebind which mouse
    button drives which camera movement.
    """

    ROTATE = "rotate"
    DOLLY = "dolly"
    PAN = "pan"


class CameraLock(StrEnum):
    """Parts of a pane's camera that can be fixed via ``SceneView.lock``.

    Used by :attr:`SceneView.lock` (a ``set`` of these string values) to disable
    the matching OrbitControls action for a single pane.
    """

    ROTATE = "rotate"
    PAN = "pan"
    ZOOM = "zoom"


class Navigation(StrEnum):
    """Per-pane camera navigation mode.

    ``ORBIT`` is the default free-orbit camera (rotate + pan + zoom).  ``VIEW2D``
    switches a pane to 2D-style viewport navigation: cursor-anchored dolly zoom
    plus screen-space pan, with no orbit.
    """

    ORBIT = "orbit"
    VIEW2D = "2d"


#: Canonical 2D camera stretch modes.
_STRETCH_MODES: tuple[str, ...] = ("fit", "fill", "fill_x", "fill_y")


def _validate_stretch(stretch: str) -> StretchMode:
    """Validate a 2D camera stretch mode and return it unchanged."""
    if stretch not in _STRETCH_MODES:
        raise ValueError(f"stretch must be one of {_STRETCH_MODES}, got {stretch!r}")
    return cast("StretchMode", stretch)


def _to_json(value: Any) -> Any:
    """Convert a dataclass field value to a JSON-compatible value."""
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, list):
        return value
    return value


def _as_pair(value: Any, name: str) -> tuple[float, float]:
    """Validate a 2-sequence of numbers and return it as a float pair."""
    if not (isinstance(value, (tuple, list)) and len(value) == 2):
        raise ValueError(f"{name} must be a (x, y) pair, got {value!r}")
    a, b = value
    if not (isinstance(a, (int, float)) and isinstance(b, (int, float))):
        raise ValueError(f"{name} must be two numbers, got {value!r}")
    return (float(a), float(b))


def _as_limits(value: Any, name: str) -> tuple[float, float] | None:
    """Validate an optional (min, max) pair, or pass through ``None``."""
    if value is None:
        return None
    lo, hi = _as_pair(value, name)
    if lo > hi:
        raise ValueError(f"{name} must be ordered (min <= max), got {value!r}")
    return (lo, hi)


@dataclass
class ViewportConfig:
    """A pane's 2D viewport transform (zoom + pan) and its limits.

    ``zoom`` is a scale factor (``1.0`` = full/fit framing, ``>1`` zooms in);
    ``pan`` is the view-centre offset in normalized (NDC) units, ``(0, 0)`` =
    centred.  ``min_zoom``/``max_zoom``/``pan_xlim``/``pan_ylim`` bound the
    interactive navigation (mirroring the 2D view's limits).
    """

    zoom: float = 1.0
    pan: tuple[float, float] = (0.0, 0.0)
    min_zoom: float | None = None
    max_zoom: float | None = None
    pan_xlim: tuple[float, float] | None = None
    pan_ylim: tuple[float, float] | None = None

    def __post_init__(self) -> None:
        if not (isinstance(self.zoom, (int, float)) and self.zoom > 0):
            raise ValueError(f"zoom must be a positive number, got {self.zoom!r}")
        self.zoom = float(self.zoom)
        self.pan = _as_pair(self.pan, "pan")
        self.pan_xlim = _as_limits(self.pan_xlim, "pan_xlim")
        self.pan_ylim = _as_limits(self.pan_ylim, "pan_ylim")
        if (
            self.min_zoom is not None
            and self.max_zoom is not None
            and self.min_zoom > self.max_zoom
        ):
            raise ValueError(
                f"min_zoom must be <= max_zoom, "
                f"got {self.min_zoom!r} > {self.max_zoom!r}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict, omitting ``None`` limits."""
        result: dict[str, Any] = {"zoom": self.zoom, "pan": _to_json(self.pan)}
        for name in ("min_zoom", "max_zoom", "pan_xlim", "pan_ylim"):
            value = getattr(self, name)
            if value is not None:
                result[name] = _to_json(value)
        return result


@dataclass(kw_only=True)
class CameraConfig:
    """Base camera config: a ``type`` discriminator + fields shared by 2D/3D.

    Subclasses select the concrete camera type and add their specific raw
    parameters.  ``position`` / ``target`` / ``up`` / ``near`` / ``far`` are
    shared because both camera families use them.
    """

    type: str  # "2d" | "3d" — discriminator; set by the subclass

    # Shared transform / clipping
    position: tuple[float, float, float] | None = None  # camera world position
    target: tuple[float, float, float] | None = None  # look-at point
    up: tuple[float, float, float] | None = None  # camera up vector
    near: float | None = None  # near clipping plane
    far: float | None = None  # far clipping plane

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict, omitting ``None`` values.

        Implemented generically over the dataclass fields so subclasses do not
        need their own serializer.  The ``type`` discriminator is always
        included.
        """
        result: dict[str, Any] = {"type": self.type}
        for f in fields(self):
            if f.name == "type":
                continue
            value = getattr(self, f.name)
            if value is not None:
                result[f.name] = _to_json(value)
        return result


@dataclass(kw_only=True)
class CameraConfig2d(CameraConfig):
    """Orthographic top-down camera configuration.

    Carries the final visible world rectangle plus the 2D aspect/scaling
    policy.  The rectangle already includes ``border_world`` (applied by the
    builder); ``border_px`` is applied by the frontend because it needs the
    live viewport size to convert pixels to world units.
    """

    type: Literal["2d"] = "2d"

    # Final visible world rectangle
    xmin: float
    xmax: float
    ymin: float
    ymax: float

    # How the rectangle is framed into the viewport:
    #   "fit"    — letterbox, preserve aspect (uniform world scale)
    #   "fill"   — stretch the rect to exactly fill the viewport (non-uniform)
    #   "fill_x" — x fills the viewport, y keeps aspect (uniform, may clip)
    #   "fill_y" — y fills the viewport, x keeps aspect (uniform, may clip)
    stretch: StretchMode = "fit"

    # Additional fixed border in pixels, applied by the frontend
    border_px: float = 0.0

    # Interactive pan/zoom limits (world coordinates, centred like xmin/xmax).
    # ``pan_*`` default to the data rectangle (xmin/xmax/ymin/ymax) when None.
    pan_xmin: float | None = None
    pan_xmax: float | None = None
    pan_ymin: float | None = None
    pan_ymax: float | None = None
    min_zoom: float | None = None  # max zoom-out (None = contain the full data)
    max_zoom: float | None = None  # max zoom-in (None = no limit)

    def __post_init__(self) -> None:
        _validate_stretch(self.stretch)


@dataclass(kw_only=True)
class CameraConfig3d(CameraConfig):
    """Perspective camera configuration.

    Carries the full explicit placement of a projective 3D camera:
    ``position`` / ``target`` / ``up`` (shared with :class:`CameraConfig`),
    plus the vertical ``fov`` and ``near`` / ``far`` clipping distances.
    Any field left ``None`` is auto-computed by the frontend.
    """

    type: Literal["3d"] = "3d"

    fov: float = 50.0  # vertical field of view in degrees
    up: tuple[float, float, float] | None = None  # camera up / orbit axis


#: Valid ``PinholeCamera.fit`` values.
_FIT_MODES: tuple[str, ...] = ("fit", "fill")


@dataclass(kw_only=True)
class PinholeCamera(CameraConfig):
    """Calibrated pinhole camera (off-center perspective projection).

    Carries distortion-free intrinsics (``fx`` / ``fy`` / ``cx`` / ``cy`` plus
    the image ``width`` / ``height``), the pose (``position`` / ``target`` /
    ``up``), clipping (``near`` / ``far``), and a ``fit`` aspect policy.  The
    frontend renders with an off-center projection so the principal point
    ``(cx, cy)`` is honored.

    ``fit`` controls how the image is framed into the pane: ``"fit"`` (default)
    letterboxes to preserve the image aspect, ``"fill"`` stretches to the pane.
    """

    type: Literal["pinhole"] = "pinhole"

    fx: float
    fy: float
    cx: float
    cy: float
    width: int
    height: int

    fit: Literal["fit", "fill"] = "fit"

    def __post_init__(self) -> None:
        if self.fit not in _FIT_MODES:
            raise ValueError(f"fit must be one of {_FIT_MODES}, got {self.fit!r}")


# ── Input specs ────────────────────────────────────────────


@dataclass
class View2DConfig:
    """2D orthographic view defined by visible data bounds.

    Args:
        xmin: Minimum visible world X (data coord).
        xmax: Maximum visible world X (data coord).
        ymin: Minimum visible world Y (data coord).
        ymax: Maximum visible world Y (data coord).
        border_world: World-unit margin added on all four sides (applied in
            Python by :func:`get_camera_view2d`).
        border_px: Pixel margin added on all four sides (applied by the
            frontend).
        stretch: How the rectangle is framed into the viewport — ``"fit"``
            (letterbox, default), ``"fill"`` (stretch both axes),
            ``"fill_x"`` (x fills, y keeps aspect), or ``"fill_y"`` (y fills,
            x keeps aspect).
    """

    xmin: float
    xmax: float
    ymin: float
    ymax: float
    border_world: float = 0.0
    border_px: float = 0.0
    stretch: StretchMode = "fit"
    pan_xmin: float | None = None
    pan_xmax: float | None = None
    pan_ymin: float | None = None
    pan_ymax: float | None = None
    min_zoom: float | None = None
    max_zoom: float | None = None

    def __post_init__(self) -> None:
        _validate_stretch(self.stretch)


@dataclass
class View3dConfig:
    """3D camera defined via a virtual plane.

    The camera optical axis is the plane normal.  The camera is placed
    at ``center + n̂ * distance`` where ``distance`` is computed from
    ``fov`` and the plane extents.

    Args:
        point: A point on the virtual plane.
        normal: Camera optical axis direction (the plane normal).
        extent_u: Full horizontal extent of the virtual plane.
        extent_v: Full vertical extent of the virtual plane.
        center: Point that maps to the viewport center (defaults to
            ``point``).
        up: Camera up vector, used as the orbit rotation axis by the
            interactive viewer.  Defaults to ``(0, 1, 0)`` so orbit
            behaviour matches the no-camera case.
        fov: Vertical field of view in degrees.
    """

    point: tuple[float, float, float]
    normal: tuple[float, float, float]
    extent_u: float
    extent_v: float
    center: tuple[float, float, float] | None = None
    up: tuple[float, float, float] = (0.0, 1.0, 0.0)
    fov: float = 50.0


# ── Builder helpers ────────────────────────────────────────


def _normalize(v: tuple[float, float, float]) -> tuple[float, float, float]:
    x, y, z = v
    length = math.sqrt(x * x + y * y + z * z)
    if length < 1e-9:
        return (0.0, 0.0, 1.0)
    return (x / length, y / length, z / length)


# ── Builders ───────────────────────────────────────────────


def get_camera_view2d(config: View2DConfig) -> CameraConfig2d:
    """Build an orthographic 2D camera from a :class:`View2DConfig`.

    Applies ``border_world`` to produce the stored visible rectangle and
    computes a top-down ``position`` / ``target`` at ``z``.
    """
    xmin = config.xmin - config.border_world
    xmax = config.xmax + config.border_world
    ymin = config.ymin - config.border_world
    ymax = config.ymax + config.border_world

    cx = (xmin + xmax) / 2.0
    cy = (ymin + ymax) / 2.0

    return CameraConfig2d(
        xmin=xmin,
        xmax=xmax,
        ymin=ymin,
        ymax=ymax,
        stretch=config.stretch,
        border_px=config.border_px,
        pan_xmin=config.pan_xmin,
        pan_xmax=config.pan_xmax,
        pan_ymin=config.pan_ymin,
        pan_ymax=config.pan_ymax,
        min_zoom=config.min_zoom,
        max_zoom=config.max_zoom,
        position=(cx, cy, 20.0),
        target=(cx, cy, 0.0),
        near=0.1,
        far=1000.0,
    )


def get_camera_view3d(config: View3dConfig) -> CameraConfig3d:
    """Build a projective 3D camera from a :class:`View3dConfig`.

    The virtual plane defined by ``point`` / ``normal`` / ``extent_u`` /
    ``extent_v`` determines the initial framing: the camera optical axis is the
    plane normal ``n̂`` and the camera is placed at ``center + n̂ * distance``
    where ``distance`` is computed from ``fov`` and the plane extents.  The
    camera up vector defaults to ``(0, 1, 0)`` so the interactive viewer's
    orbit rotation axis matches the no-camera case.

    The resulting :class:`CameraConfig3d` is a plain projective camera that the
    frontend renders with free orbit controls (rotation + pan + zoom).
    """
    n = _normalize(config.normal)
    center = config.center if config.center is not None else config.point
    ext_u = abs(config.extent_u)
    ext_v = abs(config.extent_v)
    fov = config.fov

    distance = (max(ext_u, ext_v) / 2.0) / math.tan(math.radians(fov) / 2.0)

    position = (
        center[0] + n[0] * distance,
        center[1] + n[1] * distance,
        center[2] + n[2] * distance,
    )

    return CameraConfig3d(
        fov=fov,
        position=position,
        target=center,
        up=config.up,
        near=max(0.01, distance * 0.001),
        far=distance * 10.0,
    )


def _to_vec3(values: Any) -> tuple[float, float, float]:
    """Convert a 3-sequence to a plain Python ``float`` tuple."""
    return (float(values[0]), float(values[1]), float(values[2]))


def pinhole_camera(
    K: Any,
    R: Any,
    t: Any,
    *,
    image_size: tuple[int, int] | list[int],
    near: float | None = None,
    far: float | None = None,
    fit: Literal["fit", "fill"] = "fit",
) -> PinholeCamera:
    """Build a :class:`PinholeCamera` from a pinhole calibration (OpenCV).

    ``K`` is the 3×3 intrinsic matrix, ``R`` the world→camera rotation, ``t``
    the world→camera translation, so a world point ``X`` projects to pixel
    ``u = fx·(Xc/Zc)+cx``, ``v = fy·(Yc/Zc)+cy`` for ``[Xc,Yc,Zc]ᵀ = R·X + t``.

    ``image_size`` is ``(width, height)`` in pixels.  The returned camera
    carries the intrinsics, the pose (``position``/``target``/``up``), clipping
    (``near``/``far``), and a ``fit`` aspect policy.
    """
    import numpy as np

    K = np.asarray(K, dtype=float)
    R = np.asarray(R, dtype=float)
    t = np.asarray(t, dtype=float)
    if K.shape != (3, 3):
        raise ValueError(f"K must be a 3x3 matrix, got shape {K.shape}")
    if R.shape != (3, 3):
        raise ValueError(f"R must be a 3x3 matrix, got shape {R.shape}")
    if t.shape != (3,):
        raise ValueError(f"t must be a length-3 vector, got shape {t.shape}")
    if not isinstance(image_size, (tuple, list)) or len(image_size) != 2:
        raise ValueError("image_size must be a (width, height) pair")

    width, height = int(image_size[0]), int(image_size[1])
    if width <= 0 or height <= 0:
        raise ValueError("image_size must be positive")

    fx, fy = float(K[0, 0]), float(K[1, 1])
    cx, cy = float(K[0, 2]), float(K[1, 2])

    R_t = R.T
    position = _to_vec3(-R_t @ t)
    forward = R_t @ np.array([0.0, 0.0, 1.0])
    up = _to_vec3(R_t @ np.array([0.0, -1.0, 0.0]))
    target = _to_vec3(np.asarray(position) + forward)

    return PinholeCamera(
        fx=fx,
        fy=fy,
        cx=cx,
        cy=cy,
        width=width,
        height=height,
        position=position,
        target=target,
        up=up,
        near=near,
        far=far,
        fit=fit,
    )


def get_camera(
    view_config: View2DConfig | View3dConfig,
) -> CameraConfig:
    """Dispatch on view config type to build the matching camera config."""
    if isinstance(view_config, View2DConfig):
        return get_camera_view2d(view_config)
    if isinstance(view_config, View3dConfig):
        return get_camera_view3d(view_config)
    raise TypeError(f"Unsupported view config type: {type(view_config).__name__!r}")


def _normalize_camera_config(
    camera: CameraConfig | View2DConfig | View3dConfig | None,
) -> CameraConfig | None:
    """Convert a view config to a :class:`CameraConfig`, or pass through.

    Accepts either a concrete :class:`CameraConfig` (returned unchanged) or a
    view input spec (:class:`View2DConfig` / :class:`View3dConfig`), which is
    converted via :func:`get_camera`.  ``None`` is returned unchanged.
    """
    if camera is None or isinstance(camera, CameraConfig):
        return camera
    return get_camera(camera)


def _deduce_space_dim(
    camera: CameraConfig | View2DConfig | View3dConfig | None,
) -> int | None:
    """Deduce the viewer ``space_dim`` from a camera config, or ``None``.

    A 2D camera/config implies ``space_dim=2``; a 3D camera/config implies
    ``space_dim=3``.  Returns ``None`` when no camera is given, so callers can
    fall back to their own default.
    """
    if isinstance(camera, (CameraConfig2d, View2DConfig)):
        return 2
    if isinstance(camera, (CameraConfig3d, View3dConfig)):
        return 3
    return None


@dataclass
class CameraCalibration:
    """A pinhole camera's intrinsics + extrinsics, with a frame and units.

    ``K`` is the 3×3 intrinsic matrix (pixels); ``R``/``t`` are the world→camera
    rotation/translation expressed in ``frame``; ``image_size`` is the
    ``(width, height)`` in pixels; and ``units`` is a scale applied to ``t`` (so
    millimetre data can pass ``units=0.001`` to obtain metres).
    """

    K: Matrix
    R: Matrix
    t: Any
    image_size: tuple[int, int]
    frame: CoordinateFrame = OpenCVFrame()
    units: float = 1.0

    def __post_init__(self) -> None:
        if self.K.shape != (3, 3):
            raise ValueError(f"K must be 3×3, got shape {self.K.shape}")
        if self.R.shape != (3, 3):
            raise ValueError(f"R must be 3×3, got shape {self.R.shape}")
        if len(self.image_size) != 2:
            raise ValueError(
                f"image_size must be a (width, height) pair, got {self.image_size!r}"
            )
        self.t = _to_vec3(self.t)
        self.image_size = (int(self.image_size[0]), int(self.image_size[1]))
        self.units = float(self.units)

    def _standard_rotation(self) -> np.ndarray:
        """The world→camera rotation in the standard (right-handed) frame."""
        m = np.asarray(self.frame.to_matrix(), dtype=float)
        return self.R.data @ m[:3, :3].T  # R @ Mᵀ

    def _standard_translation(self) -> np.ndarray:
        """The world→camera translation in the standard frame, scaled by ``units``."""
        return np.asarray(self.t, dtype=float) * self.units

    def world_to_camera(self) -> Matrix:
        """Return the 4×4 world→camera matrix (standard frame, metres)."""
        m = np.eye(4)
        m[:3, :3] = self._standard_rotation()
        m[:3, 3] = self._standard_translation()
        return Matrix(m)

    def camera_to_world(self) -> Matrix:
        """Return the 4×4 camera→world matrix (standard frame, metres)."""
        return self.world_to_camera().inverse()

    def camera_center(self) -> tuple[float, float, float]:
        """Return the camera's world position (standard frame)."""
        c = self.camera_to_world().data[:3, 3]
        return (float(c[0]), float(c[1]), float(c[2]))

    def to_pinhole_camera(
        self,
        *,
        near: float | None = None,
        far: float | None = None,
        fit: Literal["fit", "fill"] = "fit",
    ) -> PinholeCamera:
        """Build a :class:`PinholeCamera` placed in the standard (right-handed) frame."""
        return pinhole_camera(
            self.K.data,
            self._standard_rotation(),
            self._standard_translation(),
            image_size=self.image_size,
            near=near,
            far=far,
            fit=fit,
        )
