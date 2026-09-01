# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""PointPath — ordered list of 3D points rendered as connected line segments.

Provides :class:`PointPath` for visualizing graphs, object trails, and
polylines in the Tanga 3D viewer.  Supports FIFO capping, per-point colors,
and color gradient utilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass
class PointPath:
    """Ordered list of 3D points rendered as connected line segments.

    Parameters
    ----------
    max_points:
        Maximum number of points.  ``None`` = unlimited.  When the limit is
        reached, adding a new point removes the oldest.
    pop_colors:
        When ``True`` (default), popping the oldest point also removes its
        associated color.  When ``False``, colors remain anchored to their
        position slots — useful for trails that change shape but keep a
        fixed color gradient.
    default_colors:
        Template list mapping position index → fallback color (CSS hex
        string).  Used when ``add()`` is called without an explicit color
        and no color exists at that index in the current color list.

    Examples
    --------
    >>> path = PointPath(max_points=100)
    >>> path.add((0, 0, 0), color="#ff0000")
    >>> path.add((1, 2, 0))
    >>> path.add((3, 1, 0), color="#0000ff")
    >>> list(path.points)
    [(0.0, 0.0, 0.0), (1.0, 2.0, 0.0), (3.0, 1.0, 0.0)]
    >>> list(path.colors)
    ['#ff0000', '#ff0000', '#0000ff']
    """

    max_points: int | None = None
    pop_colors: bool = True
    default_colors: list[str | None] | None = None

    def __post_init__(self) -> None:
        if self.max_points is not None and self.max_points < 1:
            raise ValueError(f"max_points must be >= 1 or None, got {self.max_points}")
        self._points: list[tuple[float, float, float]] = []
        self._colors: list[str | None] = []

    # ── Public API ──────────────────────────────────────────

    def add(self, point: _PointInput, *, color: str | None = None) -> None:
        """Append a point to the path.

        Parameters
        ----------
        point:
            One of: :class:`~pytanga.geometry.entities.Point`,
            ``(x, y, z)`` tuple, or an MV (resolved via
            :func:`~pytanga.geometry.analysis.analyze` → Point / HPoint
            / Sphere → center).
        color:
            CSS hex color string (e.g. ``"#ff0000"``).  When ``None``,
            the color is resolved from the current color list, then
            ``default_colors``, then inherited from the previous point.
        """
        xyz = _resolve_point(point)
        at_capacity = (
            self.max_points is not None and len(self._points) >= self.max_points
        )

        if at_capacity:
            self._points.pop(0)
            if self.pop_colors and self._colors:
                self._colors.pop(0)
            elif not self.pop_colors:
                # Colors stay anchored; trim colors to not exceed max_points
                if len(self._colors) > self.max_points:
                    self._colors[:] = self._colors[: self.max_points]

        # Determine the new point's index *after* potential pop
        new_index = len(self._points)
        self._points.append(xyz)

        if color is not None:
            # Pad colors to match points length if needed
            while len(self._colors) < new_index:
                self._colors.append(None)
            self._colors.append(color)
        elif at_capacity and not self.pop_colors:
            # Colors are anchored; don't append, just let the existing color cover this slot
            pass
        else:
            self._colors.append(self._resolve_color(new_index))

    def remove(self, index: int = -1) -> None:
        """Remove a point and its color by index."""
        if not self._points:
            raise IndexError("remove from empty PointPath")
        self._points.pop(index)
        if self._colors:
            idx = index if index >= 0 else len(self._colors) + index
            if 0 <= idx < len(self._colors):
                self._colors.pop(idx)

    def clear(self) -> None:
        """Remove all points and colors."""
        self._points.clear()
        self._colors.clear()

    def set_colors(self, colors: Sequence[str | None]) -> None:
        """Replace the entire color list."""
        self._colors = list(colors)

    def set_default_colors(self, colors: Sequence[str | None]) -> None:
        """Replace the default color template."""
        self.default_colors = list(colors)

    # ── Properties ──────────────────────────────────────────

    @property
    def points(self) -> list[tuple[float, float, float]]:
        """A copy of the current point list."""
        return list(self._points)

    @property
    def colors(self) -> list[str | None]:
        """A copy of the current color list (parallel to ``points``)."""
        return list(self._colors)

    @property
    def dim(self) -> int:
        """Always 3 (point path is 3D)."""
        return 3

    @property
    def is_full(self) -> bool:
        """True when the path has reached ``max_points``."""
        if self.max_points is None:
            return False
        return len(self._points) >= self.max_points

    def __len__(self) -> int:
        return len(self._points)

    def __repr__(self) -> str:
        return (
            f"PointPath(points={len(self._points)}, "
            f"max={self.max_points}, pop_colors={self.pop_colors})"
        )

    # ── Internal helpers ────────────────────────────────────

    def _resolve_color(self, index: int) -> str | None:
        """Resolve the color for a point at the given index.

        Priority:
        1. Existing color in ``_colors`` at that index
        2. ``default_colors`` value at that index
        3. Previous point's color (index-1)
        4. ``None`` (falls back to style default on frontend)
        """
        if index < len(self._colors) and self._colors[index] is not None:
            return self._colors[index]

        if self.default_colors is not None:
            wrapped_idx = index % len(self.default_colors)
            dc = self.default_colors[wrapped_idx]
            if dc is not None:
                return dc

        if index > 0 and self._colors:
            return self._colors[index - 1]

        return None


# ── Point resolution ───────────────────────────────────────

_PointInput = (
    "GeoPoint | tuple[float, float, float] | tuple[float, float] | MV"
)


def _resolve_point(point: _PointInput) -> tuple[float, float, float]:
    """Convert various point representations to ``(x, y, z)``."""
    # MV (has _alg attribute)
    if hasattr(point, "_alg"):
        from pytanga.geometry import analyze
        from pytanga.geometry.entities import HPoint, Point as GeoPoint, Sphere

        # Typed conversion first: a point MV resolves directly to a GeoPoint
        # (Phase 3's ``Point(mv)`` constructor reads ``mv.algebra.opns``).
        try:
            result = GeoPoint(point)
        except (ValueError, TypeError):
            # Fallback: HPoint / Sphere center via generic analysis.
            result = analyze(point)
        if isinstance(result, GeoPoint):
            return (result.x, result.y, result.z)
        if isinstance(result, HPoint):
            return (result.point.x, result.point.y, result.point.z)
        if isinstance(result, Sphere):
            return (result.center.x, result.center.y, result.center.z)
        raise ValueError(
            f"Cannot extract point from MV that resolves to "
            f"{type(result).__name__ if result else 'None'}"
        )

    # Geo Point entity
    from pytanga.geometry.entities import Point as GeoPoint

    if isinstance(point, GeoPoint):
        return (point.x, point.y, point.z)

    # Tuple / sequence
    if isinstance(point, (tuple, list)):
        coords = tuple(float(v) for v in point)
        if len(coords) == 3:
            return (coords[0], coords[1], coords[2])
        if len(coords) == 2:
            return (coords[0], coords[1], 0.0)
        raise ValueError(
            f"Point tuple must have 2 or 3 elements, got {len(coords)}"
        )

    raise TypeError(f"Cannot interpret {type(point).__name__} as a point")


# ── Color utilities ────────────────────────────────────────


def gradient_colors(start: str, end: str, steps: int) -> list[str]:
    """Return a linear RGB gradient as a list of CSS hex color strings.

    Parameters
    ----------
    start:
        Starting color (e.g. ``"#440000"``).
    end:
        Ending color (e.g. ``"#ffaa00"``).
    steps:
        Number of colors in the output list.  Must be >= 1.

    Returns
    -------
    list[str]
        ``steps`` hex strings interpolated between *start* and *end*.

    Examples
    --------
    >>> gradient_colors("#ff0000", "#0000ff", 3)
    ['#ff0000', '#800080', '#0000ff']
    """
    return multi_gradient_colors([(0.0, start), (1.0, end)], steps)


def multi_gradient_colors(
    stops: list[tuple[float, str]], steps: int
) -> list[str]:
    """Return a multi-stop RGB gradient as a list of CSS hex color strings.

    Parameters
    ----------
    stops:
        List of ``(position, color)`` pairs.  Positions are floats between
        0.0 and 1.0 and must be in ascending order.  At least two stops
        are required.
    steps:
        Number of output colors.  Must be >= 1.

    Returns
    -------
    list[str]
        ``steps`` hex strings interpolated across the stops.

    Examples
    --------
    >>> multi_gradient_colors(
    ...     [(0.0, "#ff0000"), (0.5, "#00ff00"), (1.0, "#0000ff")], 5
    ... )
    ['#ff0000', '#80ff00', '#00ff00', '#0080ff', '#0000ff']
    """
    if steps < 1:
        raise ValueError(f"steps must be >= 1, got {steps}")
    if len(stops) < 2:
        raise ValueError(f"need at least 2 color stops, got {len(stops)}")

    # Validate stops are sorted
    for i in range(1, len(stops)):
        if stops[i][0] <= stops[i - 1][0]:
            raise ValueError(
                f"Color stops must be in ascending order; "
                f"stop {i} ({stops[i][0]}) <= stop {i-1} ({stops[i-1][0]})"
            )

    if steps == 1:
        return [stops[0][1]]

    colors: list[str] = []
    for i in range(steps):
        t = i / (steps - 1) if steps > 1 else 0.0
        colors.append(_interpolate_stops(stops, t))

    return colors


def _interpolate_stops(
    stops: list[tuple[float, str]], t: float
) -> str:
    """Interpolate between the two nearest stops at position *t*."""
    # Clamp
    if t <= stops[0][0]:
        return stops[0][1]
    if t >= stops[-1][0]:
        return stops[-1][1]

    # Find bracketing stops
    for i in range(len(stops) - 1):
        t0, c0 = stops[i]
        t1, c1 = stops[i + 1]
        if t0 <= t <= t1:
            local = (t - t0) / (t1 - t0) if t1 != t0 else 0.0
            return _lerp_color(c0, c1, local)

    return stops[-1][1]


def _lerp_color(c0: str, c1: str, t: float) -> str:
    """Linearly interpolate between two CSS hex colors."""
    r0, g0, b0 = _hex_to_rgb(c0)
    r1, g1, b1 = _hex_to_rgb(c1)
    r = int(r0 + (r1 - r0) * t)
    g = int(g0 + (g1 - g0) * t)
    b = int(b0 + (b1 - b0) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Parse a CSS hex color string to ``(r, g, b)`` integers (0–255)."""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        raise ValueError(f"Invalid hex color: {hex_color!r}")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)