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
_Vec2 = tuple[float, float]

# Default z depths for 2D layering.  Entities default to z = 0 and the
# orthographic 2D camera looks down +z, so:
#   - the grid sits behind all objects (most negative z),
#   - axes sit in front of the grid but behind entities.
_GRID_Z = -1.0
_AXES_Z = -0.5


@dataclass
class Axis:
    """A single coordinate axis with ticks and optional value labels.

    Renders as a line from ``start`` to ``end``.  At each major
    interval, a small perpendicular tick is drawn and (optionally) a
    value label.  At each minor interval, a smaller tick is drawn.

    Value labels measure numeric values along the axis.  By default the
    value at ``start`` is ``0`` and increases by ``1`` per world unit
    along ``start`` → ``end``.  Set ``value_start`` and ``value_step``
    to render a different numeric scale (for example a negative axis
    half, where ``value_step`` is ``-1``).

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
    value_start:
        Numeric value at ``start``.
    value_step:
        Numeric value increment per world unit along ``start`` → ``end``.

    Examples
    --------
    >>> x = Axis((0, 0, 0), (10, 0, 0), major_interval=2.0, label="X")
    >>> y = Axis((0, 0, 0), (0, 5, 0), major_interval=1.0, label="Y")
    >>> neg_x = Axis((0, 0, 0), (-10, 0, 0), value_step=-1.0)
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
    value_start: float = 0.0
    value_step: float = 1.0


@dataclass
class Grid:
    """A coordinate grid in a plane.

    Draws a mesh of lines in the plane spanned by ``dir_u`` and
    ``dir_v``.  Lines parallel to ``dir_u`` are drawn at each
    ``interval_v`` step; lines parallel to ``dir_v`` at each
    ``interval_u`` step.

    The ``range_u`` and ``range_v`` tuples ``(min, max)`` define the
    extents along ``dir_u`` and ``dir_v`` relative to ``origin``, so the
    grid covers ``[min, max]`` in each direction.  A grid needs not be
    centred on ``origin`` — for example ``range_u=(-2.0, 3.0)`` spans
    from ``origin - 2·û`` to ``origin + 3·û``.

    Parameters
    ----------
    origin:
        Grid anchor point in world coordinates.
    dir_u:
        First in-plane direction (must be orthogonal to ``dir_v``).
    dir_v:
        Second in-plane direction.
    range_u:
        ``(min, max)`` extent along ``dir_u``.
    range_v:
        ``(min, max)`` extent along ``dir_v``.
    interval_u:
        Spacing between lines parallel to ``dir_v``.
    interval_v:
        Spacing between lines parallel to ``dir_u``.

    Examples
    --------
    >>> grid = Grid(range_u=(-5.0, 5.0), range_v=(-5.0, 5.0), interval_u=1.0, interval_v=1.0)
    """

    origin: _Vec3 | _Vec2 = (0.0, 0.0)
    dir_u: _Vec3 = (1.0, 0.0, 0.0)
    dir_v: _Vec3 = (0.0, 1.0, 0.0)
    range_u: tuple[float, float] = (0.0, 5.0)
    range_v: tuple[float, float] = (0.0, 5.0)
    interval_u: float = 1.0
    interval_v: float = 1.0

    def __post_init__(self) -> None:
        # A 2-tuple origin (x, y) is placed behind all other objects.
        self.origin = _pad_origin(self.origin, _GRID_Z)


@dataclass
class Axes3D:
    """Convenience wrapper that expands to up to six :class:`Axis` objects.

    For each of the three directions ``dir_u``, ``dir_v``, ``dir_w``,
    the corresponding ``range_*`` tuple ``(min, max)`` defines the
    extents along the negative and positive side of ``origin``.  A
    positive ``max`` produces an axis half running from ``origin`` to
    ``origin + dir̂·max``; a negative ``min`` produces an axis half from
    ``origin`` to ``origin + dir̂·min``.  A zero extent is skipped, so
    the result has between zero and six axes.

    ``labels`` optionally names each axis.  A name label is attached to
    the positive half only.

    Parameters
    ----------
    origin:
        Common start point of all axes.
    dir_u, dir_v, dir_w:
        Axis directions (need not be orthonormal, but should be
        linearly independent).
    range_u, range_v, range_w:
        ``(min, max)`` extent along each axis.
    major_interval:
        Major tick spacing passed to each expanded :class:`Axis`.
    minor_interval:
        Minor tick spacing passed to each expanded :class:`Axis`.
    labels:
        Optional ``(u, v, w)`` axis name labels.

    Examples
    --------
    >>> axes = Axes3D(
    ...     range_u=(-5, 5), range_v=(-5, 5), range_w=(0, 5),
    ...     labels=("X", "Y", "Z"),
    ... )
    >>> for a in axes.expand():
    ...     print(a.start, a.end, a.label)
    """

    origin: _Vec3 = (0.0, 0.0, 0.0)
    dir_u: _Vec3 = (1.0, 0.0, 0.0)
    dir_v: _Vec3 = (0.0, 1.0, 0.0)
    dir_w: _Vec3 = (0.0, 0.0, 1.0)
    range_u: tuple[float, float] = (0.0, 5.0)
    range_v: tuple[float, float] = (0.0, 5.0)
    range_w: tuple[float, float] = (0.0, 5.0)
    major_interval: float = 1.0
    minor_interval: float | None = None
    labels: tuple[str, str, str] | None = None

    def expand(self) -> list[Axis]:
        """Expand into individual :class:`Axis` objects (up to six)."""
        u_label = self.labels[0] if self.labels is not None else None
        v_label = self.labels[1] if self.labels is not None else None
        w_label = self.labels[2] if self.labels is not None else None
        axes: list[Axis] = []
        axes.extend(self._expand_dir(self.dir_u, self.range_u, u_label))
        axes.extend(self._expand_dir(self.dir_v, self.range_v, v_label))
        axes.extend(self._expand_dir(self.dir_w, self.range_w, w_label))
        return axes

    def _expand_dir(
        self, direction: _Vec3, extent: tuple[float, float], label: str | None
    ) -> list[Axis]:
        """Expand one direction into its negative and positive axis halves."""
        lo, hi = extent
        axes: list[Axis] = []

        def make(end: _Vec3, value_step: float, name_label: str | None) -> Axis:
            return Axis(
                start=self.origin,
                end=end,
                major_interval=self.major_interval,
                minor_interval=self.minor_interval,
                label=name_label,
                value_step=value_step,
            )

        if hi != 0.0:
            axes.append(make(_scale_dir(self.origin, direction, hi), 1.0, label))
        if lo != 0.0:
            axes.append(make(_scale_dir(self.origin, direction, lo), -1.0, None))
        return axes


@dataclass
class Axes2D:
    """Convenience wrapper that expands to up to four :class:`Axis` objects.

    The two axis directions ``dir_u`` and ``dir_v`` span the coordinate
    plane.  For each direction the ``range_*`` tuple ``(min, max)``
    defines the extents along the negative and positive side of
    ``origin``, mirroring :class:`Axes3D`.

    ``labels`` optionally names each axis.  A name label is attached to
    the positive half only.

    Parameters
    ----------
    origin:
        Common start point of both axes.  A 2D ``(x, y)`` pair is
        accepted and padded with a default z that places the axes in
        front of the grid but behind other objects.
    dir_u, dir_v:
        Axis directions.
    range_u, range_v:
        ``(min, max)`` extent along each axis.
    major_interval:
        Major tick spacing passed to each expanded :class:`Axis`.
    minor_interval:
        Minor tick spacing passed to each expanded :class:`Axis`.
    labels:
        Optional ``(u, v)`` axis name labels.

    Examples
    --------
    >>> axes = Axes2D(range_u=(-3, 3), range_v=(0, 4), labels=("X", "Y"))
    >>> len(axes.expand())
    3
    """

    origin: _Vec3 | _Vec2 = (0.0, 0.0)
    dir_u: _Vec3 = (1.0, 0.0, 0.0)
    dir_v: _Vec3 = (0.0, 1.0, 0.0)
    range_u: tuple[float, float] = (0.0, 5.0)
    range_v: tuple[float, float] = (0.0, 5.0)
    major_interval: float = 1.0
    minor_interval: float | None = None
    labels: tuple[str, str] | None = None

    def expand(self) -> list[Axis]:
        """Expand into individual :class:`Axis` objects (up to four)."""
        u_label = self.labels[0] if self.labels is not None else None
        v_label = self.labels[1] if self.labels is not None else None
        origin = _pad_origin(self.origin, _AXES_Z)
        axes: list[Axis] = []
        axes.extend(self._expand_dir(origin, self.dir_u, self.range_u, u_label))
        axes.extend(self._expand_dir(origin, self.dir_v, self.range_v, v_label))
        return axes

    def _expand_dir(
        self,
        origin: _Vec3,
        direction: _Vec3,
        extent: tuple[float, float],
        label: str | None,
    ) -> list[Axis]:
        """Expand one direction into its negative and positive axis halves."""
        lo, hi = extent
        axes: list[Axis] = []

        def make(end: _Vec3, value_step: float, name_label: str | None) -> Axis:
            return Axis(
                start=origin,
                end=end,
                major_interval=self.major_interval,
                minor_interval=self.minor_interval,
                label=name_label,
                value_step=value_step,
            )

        if hi != 0.0:
            axes.append(make(_scale_dir(origin, direction, hi), 1.0, label))
        if lo != 0.0:
            axes.append(make(_scale_dir(origin, direction, lo), -1.0, None))
        return axes


def _pad_origin(origin: _Vec3 | _Vec2, z: float) -> _Vec3:
    """Normalise a 2D or 3D origin to a 3-tuple, falling back to ``z`` for 2D."""
    if len(origin) == 2:
        return (origin[0], origin[1], z)  # type: ignore[return-value]
    return origin  # type: ignore[return-value]


def _scale_dir(origin: _Vec3, direction: _Vec3, extent: float) -> _Vec3:
    """Return ``origin + normalize(direction) * extent``."""
    import math

    norm = math.sqrt(sum(c * c for c in direction))
    if norm == 0.0:
        raise ValueError("Axis direction must be non-zero")
    return tuple(origin[i] + direction[i] / norm * extent for i in range(3))  # type: ignore[return-value]