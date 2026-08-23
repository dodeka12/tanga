# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Shader-drawn overlays for the SDF viewer.

Overlays are **not** raymarched volumes: they are procedural patterns drawn in
the fragment shader and depth-composited against the raymarch result (e.g. an
infinite grid on an arbitrary plane). They serialize with their own ``kind`` so
the frontend can dispatch to a per-kind emitter (``overlays/factory.js``), in
the same spirit as the standard viewer's ``renderers/factory.js``.
"""

from __future__ import annotations

import math
from typing import Any


class SdfOverlay:
    """Base class for shader-drawn overlays (not raymarched volumes)."""


def _normalize(v: tuple[float, float, float]) -> tuple[float, float, float]:
    x, y, z = float(v[0]), float(v[1]), float(v[2])
    length = math.sqrt(x * x + y * y + z * z)
    if length < 1e-12:
        return (0.0, 0.0, 1.0)
    return (x / length, y / length, z / length)


class Grid(SdfOverlay):
    """An infinite grid drawn on the plane spanned by ``dir_u`` and ``dir_v``.

    ``origin`` is a point on the plane. Grid lines run parallel to ``dir_u`` and
    ``dir_v`` (each normalized on construction) with ``interval_u`` /
    ``interval_v`` spacing. ``color`` is a CSS hex string and ``opacity`` the
    line opacity (``0.0`` fully transparent → ``1.0`` opaque).
    """

    def __init__(
        self,
        *,
        origin: tuple[float, float, float] = (0.0, 0.0, 0.0),
        dir_u: tuple[float, float, float] = (1.0, 0.0, 0.0),
        dir_v: tuple[float, float, float] = (0.0, 0.0, 1.0),
        interval_u: float = 1.0,
        interval_v: float = 1.0,
        color: str = "#555555",
        opacity: float = 0.5,
    ) -> None:
        self.origin = (float(origin[0]), float(origin[1]), float(origin[2]))
        self.dir_u = _normalize(dir_u)
        self.dir_v = _normalize(dir_v)
        self.interval_u = max(abs(float(interval_u)), 1e-4)
        self.interval_v = max(abs(float(interval_v)), 1e-4)
        self.color = color
        self.opacity = float(opacity)


def serialize_overlay(overlay: SdfOverlay) -> dict[str, Any]:
    """Serialize an overlay to its wire form (shared with the frontend)."""
    if isinstance(overlay, Grid):
        return {
            "kind": "grid",
            "origin": list(overlay.origin),
            "dir_u": list(overlay.dir_u),
            "dir_v": list(overlay.dir_v),
            "interval_u": overlay.interval_u,
            "interval_v": overlay.interval_v,
            "color": overlay.color,
            "opacity": overlay.opacity,
        }
    raise TypeError(f"SDF viewer does not support overlay {type(overlay).__name__!r}")
