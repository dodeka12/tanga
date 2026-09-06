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
from typing import Any, Literal


StretchMode = Literal["fit", "fill", "fill_x", "fill_y"]

#: Canonical 2D camera stretch modes.
_STRETCH_MODES: tuple[str, ...] = ("fit", "fill", "fill_x", "fill_y")


def _validate_stretch(stretch: str) -> str:
    """Validate a 2D camera stretch mode and return it unchanged."""
    if stretch not in _STRETCH_MODES:
        raise ValueError(
            f"stretch must be one of {_STRETCH_MODES}, got {stretch!r}"
        )
    return stretch


def _to_json(value: Any) -> Any:
    """Convert a dataclass field value to a JSON-compatible value."""
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, list):
        return value
    return value


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

    def to_dict(self) -> dict:
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


def get_camera(
    view_config: View2DConfig | View3dConfig,
) -> CameraConfig:
    """Dispatch on view config type to build the matching camera config."""
    if isinstance(view_config, View2DConfig):
        return get_camera_view2d(view_config)
    if isinstance(view_config, View3dConfig):
        return get_camera_view3d(view_config)
    raise TypeError(
        f"Unsupported view config type: {type(view_config).__name__!r}"
    )


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
