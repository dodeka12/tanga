# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Frustum visualization-only entity data class."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from ._coerce import to_direction, to_float, to_point
from .direction import Direction
from .point import Point


def _pt(values: Any) -> Point:
    """Build a ``Point`` from a 3-sequence (coercing to plain floats)."""
    return Point(float(values[0]), float(values[1]), float(values[2]))


def _dir(values: Any) -> Direction:
    """Build a ``Direction`` from a 3-sequence (coercing to plain floats)."""
    return Direction(float(values[0]), float(values[1]), float(values[2]))


@dataclass(frozen=True)
class Frustum:
    """A truncated pyramid (or pyramid) drawn purely for visualization.

    Unlike the MV-backed entities in this package, a :class:`Frustum` has **no**
    multivector representation — it cannot be passed to
    :func:`~pytanga.geometry.create` or produced by
    :func:`~pytanga.geometry.analyze`.  It exists only as a rendering hint for
    the visualizer (e.g. a camera's view frustum).

    The frustum is parameterized intrinsically: ``origin`` is the apex (the
    camera position), ``axis`` the central axis toward the far plane,
    ``horizontal`` the far plane's horizontal axis (the vertical axis is
    ``horizontal × axis``), and ``near``/``far`` the distances from ``origin``
    to the first/second plane.  A non-positive ``near`` means the first plane
    collapses to the apex at ``origin``.  The near-plane half-extents follow by
    similar triangles (``near / far * far_half_*``).
    """

    origin: Point
    axis: Direction
    horizontal: Direction
    near: float
    far: float
    far_half_width: float
    far_half_height: float

    def __init__(
        self,
        origin: Any,
        axis: Any,
        horizontal: Any,
        near: Any,
        far: Any,
        far_half_width: Any,
        far_half_height: Any,
    ) -> None:
        object.__setattr__(self, "origin", to_point(origin))
        object.__setattr__(self, "axis", to_direction(axis))
        object.__setattr__(self, "horizontal", to_direction(horizontal))
        object.__setattr__(self, "near", to_float(near))
        object.__setattr__(self, "far", to_float(far))
        object.__setattr__(self, "far_half_width", to_float(far_half_width))
        object.__setattr__(self, "far_half_height", to_float(far_half_height))

    @property
    def apex(self) -> bool:
        """Whether the first end collapses to a single point (``near <= 0``)."""
        return self.near <= 0.0

    def __repr__(self) -> str:
        return (
            f"Frustum(apex={self.apex}, origin={self.origin}, axis={self.axis}, "
            f"near={self.near:.2f}, far={self.far:.2f}, "
            f"hw={self.far_half_width:.2f}, hh={self.far_half_height:.2f})"
        )

    @classmethod
    def from_camera(
        cls,
        camera: Any,
        *,
        near: float | None = None,
        far: float | None = None,
        aspect: float = 1.0,
    ) -> "Frustum":
        """Build the view frustum for a camera config.

        A ``PinholeCamera`` (``type == "pinhole"``) uses its intrinsics
        (``fx``/``fy``/``width``/``height``); a symmetric ``CameraConfig3d``
        uses ``fov`` + *aspect*.  ``near``/``far`` default to the camera's
        near/far planes; a non-positive ``near`` yields the apex form (the first
        plane collapses to the camera position).
        """
        import numpy as np

        position = np.asarray(camera.position, dtype=float)
        target = np.asarray(camera.target, dtype=float) if camera.target is not None else position + np.array([0.0, 0.0, 1.0])
        up = np.asarray(camera.up, dtype=float) if camera.up is not None else np.array([0.0, 1.0, 0.0])

        axis = target - position
        axis_norm = float(np.linalg.norm(axis))
        axis = axis / axis_norm if axis_norm > 1e-9 else np.array([0.0, 0.0, 1.0])

        near_d = float(near if near is not None else (getattr(camera, "near", None) or 0.1))
        far_d = float(far if far is not None else (getattr(camera, "far", None) or 10.0))
        if far_d <= 0.0:
            far_d = 10.0

        if getattr(camera, "type", None) == "pinhole":
            def half_extents(d: float) -> tuple[float, float]:
                return (
                    d * float(camera.width) / (2.0 * float(camera.fx)),
                    d * float(camera.height) / (2.0 * float(camera.fy)),
                )
        else:
            fov = float(getattr(camera, "fov", 50.0))

            def half_extents(d: float) -> tuple[float, float]:
                hh = d * math.tan(math.radians(fov) / 2.0)
                return (hh * aspect, hh)

        right = np.cross(axis, up)
        right_norm = float(np.linalg.norm(right))
        right = right / right_norm if right_norm > 1e-9 else np.array([1.0, 0.0, 0.0])

        far_hw, far_hh = half_extents(far_d)

        return cls(
            _pt(position),
            _dir(axis),
            _dir(right),
            near_d,
            far_d,
            far_hw,
            far_hh,
        )
