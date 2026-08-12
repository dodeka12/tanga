# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Coordinate axes and grid scene objects.

Provides :class:`Axis` and :class:`Grid` scene objects plus the
convenience classes :class:`Axes3D` and :class:`Axes2D`, which expand
into individual :class:`Axis` objects.

Axes and grids are ordinary scene-layer objects.  Unlike the old
hard-coded frontend helpers, they are serialized like any other entity
and flow through the standard ``createEntityMesh`` pipeline, so they
work identically in the live viewer and in HTML export.
"""

from __future__ import annotations

from dataclasses import dataclass

_Vec3 = tuple[float, float, float]


@dataclass
class Axis:
    """A single coordinate axis with ticks and optional value labels.

    Renders as a line from ``start`` to ``end``.  At each major
    interval, a small perpendicular tick is drawn and (optionally) a
    value label.  At each minor interval, a smaller tick is drawn.

    Parameters
    ----------
    start:
        Start point of the axis in world coordinates.
    end:
        End point of the axis in world coordinates.
    major_interval:
        Spacing between major ticks (and value labels).
    minor_interval:
        Spacing between minor ticks.  ``None`` disables minor ticks.
    label_at_major:
        When ``True``, draw a value label at each major tick.
    label_format:
        Python format specifier used to render value labels
        (e.g. ``".2f"``).
    label_size:
        Font size in pixels for the CSS2D value labels.  ``None`` uses
        the frontend default.
    show_ticks:
        When ``False``, draw only the axis line without ticks.
    label:
        Optional axis name label (e.g. ``"X"``) drawn near the end of
        the axis.  ``None`` draws no name label.

    Examples
    --------
    >>> x = Axis((0, 0, 0), (10, 0, 0), major_interval=2.0, label="X")
    >>> y = Axis((0, 0, 0), (0, 5, 0), major_interval=1.0, label="Y")
    """

    start: _Vec3
    end: _Vec3
    major_interval: float = 1.0
    minor_interval: float | None = None
    label_at_major: bool = True
    label_format: str = ".1f"
    label_size: float | None = None
    show_ticks: bool = True
    label: str | None = None


@dataclass
class Grid:
    """A coordinate grid in a plane.

    Draws a mesh of lines in the plane spanned by ``dir_u`` and
    ``dir_v``.  Lines parallel to ``dir_u`` are drawn at each
    ``interval_v`` step; lines parallel to ``dir_v`` at each
    ``interval_u`` step.  The grid is centred on ``origin`` and covers
    ``range_u`` × ``range_v``.

    Parameters
    ----------
    origin:
        Grid centre point in world coordinates.
    dir_u:
        First in-plane direction (must be orthogonal to ``dir_v``).
    dir_v:
        Second in-plane direction.
    range_u:
        Total extent along ``dir_u`` (from ``-range_u/2`` to
        ``+range_u/2``).
    range_v:
        Total extent along ``dir_v``.
    interval_u:
        Spacing between lines parallel to ``dir_v``.
    interval_v:
        Spacing between lines parallel to ``dir_u``.

    Examples
    --------
    >>> grid = Grid(range_u=10.0, range_v=10.0, interval_u=1.0, interval_v=1.0)
    """

    origin: _Vec3 = (0.0, 0.0, 0.0)
    dir_u: _Vec3 = (1.0, 0.0, 0.0)
    dir_v: _Vec3 = (0.0, 1.0, 0.0)
    range_u: float = 5.0
    range_v: float = 5.0
    interval_u: float = 1.0
    interval_v: float = 1.0


@dataclass
class Axes3D:
    """Convenience wrapper that expands to three :class:`Axis` objects.

    The three axes run from ``origin`` along ``dir_u``, ``dir_v``, and
    ``dir_w``.  ``labels`` optionally names each axis, drawn near its
    end.

    Parameters
    ----------
    origin:
        Common start point of all three axes.
    dir_u, dir_v, dir_w:
        Axis directions (need not be orthonormal, but should be
        linearly independent).
    range_u, range_v, range_w:
        Total extent along each axis.
    major_interval:
        Major tick spacing passed to each expanded :class:`Axis`.
    labels:
        Optional ``(u, v, w)`` axis name labels.

    Examples
    --------
    >>> axes = Axes3D(range_u=5, range_v=5, range_w=5, labels=("X", "Y", "Z"))
    >>> for a in axes.expand():
    ...     print(a.start, a.end, a.label)
    """

    origin: _Vec3 = (0.0, 0.0, 0.0)
    dir_u: _Vec3 = (1.0, 0.0, 0.0)
    dir_v: _Vec3 = (0.0, 1.0, 0.0)
    dir_w: _Vec3 = (0.0, 0.0, 1.0)
    range_u: float = 5.0
    range_v: float = 5.0
    range_w: float = 5.0
    major_interval: float = 1.0
    labels: tuple[str, str, str] | None = None

    def expand(self) -> list[Axis]:
        """Expand into a list of three :class:`Axis` objects."""
        u_label = self.labels[0] if self.labels is not None else None
        v_label = self.labels[1] if self.labels is not None else None
        w_label = self.labels[2] if self.labels is not None else None
        return [
            Axis(
                start=self.origin,
                end=_scale_dir(self.origin, self.dir_u, self.range_u),
                major_interval=self.major_interval,
                label=u_label,
            ),
            Axis(
                start=self.origin,
                end=_scale_dir(self.origin, self.dir_v, self.range_v),
                major_interval=self.major_interval,
                label=v_label,
            ),
            Axis(
                start=self.origin,
                end=_scale_dir(self.origin, self.dir_w, self.range_w),
                major_interval=self.major_interval,
                label=w_label,
            ),
        ]


@dataclass
class Axes2D:
    """Convenience wrapper that expands to two :class:`Axis` objects.

    The two axes run from ``origin`` along ``dir_u`` and ``dir_v``.
    ``labels`` optionally names each axis.

    Parameters
    ----------
    origin:
        Common start point of both axes.
    dir_u, dir_v:
        Axis directions.
    range_u, range_v:
        Total extent along each axis.
    major_interval:
        Major tick spacing passed to each expanded :class:`Axis`.
    labels:
        Optional ``(u, v)`` axis name labels.

    Examples
    --------
    >>> axes = Axes2D(range_u=5, range_v=5, labels=("X", "Y"))
    >>> len(axes.expand())
    2
    """

    origin: _Vec3 = (0.0, 0.0, 0.0)
    dir_u: _Vec3 = (1.0, 0.0, 0.0)
    dir_v: _Vec3 = (0.0, 1.0, 0.0)
    range_u: float = 5.0
    range_v: float = 5.0
    major_interval: float = 1.0
    labels: tuple[str, str] | None = None

    def expand(self) -> list[Axis]:
        """Expand into a list of two :class:`Axis` objects."""
        u_label = self.labels[0] if self.labels is not None else None
        v_label = self.labels[1] if self.labels is not None else None
        return [
            Axis(
                start=self.origin,
                end=_scale_dir(self.origin, self.dir_u, self.range_u),
                major_interval=self.major_interval,
                label=u_label,
            ),
            Axis(
                start=self.origin,
                end=_scale_dir(self.origin, self.dir_v, self.range_v),
                major_interval=self.major_interval,
                label=v_label,
            ),
        ]


def _scale_dir(origin: _Vec3, direction: _Vec3, extent: float) -> _Vec3:
    """Return ``origin + normalize(direction) * extent``."""
    import math

    norm = math.sqrt(sum(c * c for c in direction))
    if norm == 0.0:
        raise ValueError("Axis direction must be non-zero")
    return tuple(origin[i] + direction[i] / norm * extent for i in range(3))  # type: ignore[return-value]