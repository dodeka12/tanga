# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Coordinate-system helper for plotting graphs in 2D and 3D scenes.

:class:`CoordinateSystem` is **not** a scene object — it is a helper that
creates a single :class:`~pytanga.viz.VizGroup` holding a background plane, a
grid, two axes (with value labels), and any plotted point paths.  It keeps the
:class:`~pytanga.viz.VizObjectRef` of each child so axis-range changes update
the children in place instead of re-adding them.

In 2D the group lives in the XY plane (centred at the world origin) and the
class can compute and set a default :class:`~pytanga.viz.View2DConfig` with a
pixel border so labels are visible.  In 3D the group is placed/oriented via its
``transform`` so the plot plane sits at ``position`` with the given ``normal``;
the 3D camera is never set — it is left to the caller.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, Literal, cast

import numpy as np

from pytanga.geometry.entities import Direction, Line, Plane, Point

from . import _transforms as _T
from ._point_path import PointPath
from ._scale import (
    LogScale,
    Scale,
    generate_linear_intervals,
    make_scale,
    normalize_intervals,
)
from ._scene_objects import Axis, Grid
from .camera import (
    CameraConfig,
    CameraConfig2d,
    StretchMode,
    View2DConfig,
    _validate_stretch,
)
from ._styles import (
    AxisStyle,
    GridStyle,
    LabelStyle,
    ObjVizStyle,
    PlaneStyle,
    PointPathStyle,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from ._object_ref import VizObjectRef
    from ._scene_handle import VizSceneHandle
    from .visualizer import Visualizer

#: A 3-vector accepted by the placement helpers: a geometry vector or a triple.
Vec3Like = "Point | Direction | tuple[float, float, float]"

# Local-frame z ordering within the group.
_PLANE_Z = 0.0
_GRID_Z_3D = 0.01
_AXES_Z_3D = 0.02
_PLOT_Z_3D = 0.03
_GRID_Z_2D = -1.0
_AXES_Z_2D = -0.5
_PLOT_Z_2D = 0.0


def _coerce_handle(target: "Visualizer | VizSceneHandle") -> "VizSceneHandle":
    """Normalize a ``Visualizer`` or ``VizSceneHandle`` to a handle."""
    from ._scene_handle import VizSceneHandle
    from .visualizer import Visualizer

    if isinstance(target, VizSceneHandle):
        return target
    if isinstance(target, Visualizer):
        return target.scene("")
    raise TypeError(
        f"CoordinateSystem expects a Visualizer or VizSceneHandle, got {type(target).__name__!r}"
    )


def _as_range(value: "Sequence[float] | None") -> tuple[float, float]:
    """Normalize a ``(lo, hi)`` pair to an ascending float tuple."""
    if value is None:
        raise ValueError("range must be a (lo, hi) pair, not None")
    if len(value) != 2:
        raise ValueError(f"range must be a (lo, hi) pair, got {value!r}")
    lo, hi = float(value[0]), float(value[1])
    return (min(lo, hi), max(lo, hi))


def _as_vec3(
    value: "Point | Direction | tuple[float, float, float]",
) -> tuple[float, float, float]:
    if hasattr(value, "x") and hasattr(value, "y") and hasattr(value, "z"):
        vec = cast("Any", value)
        return (float(vec.x), float(vec.y), float(vec.z))
    if len(value) != 3:
        raise ValueError(f"expected a 3-vector, got {value!r}")
    return (float(value[0]), float(value[1]), float(value[2]))


def _as_size(
    value: "Sequence[float | None] | None",
) -> tuple[float | None, float | None]:
    """Normalize a ``size`` spec to an optional ``(size_x, size_y)`` pair.

    ``None`` (either the whole spec or one element) means "derive from the data
    range".  Explicit sizes must be positive.
    """
    if value is None:
        return (None, None)
    if len(value) != 2:
        raise ValueError(f"size must be a (size_x, size_y) pair, got {value!r}")
    sx = None if value[0] is None else float(value[0])
    sy = None if value[1] is None else float(value[1])
    for s in (sx, sy):
        if s is not None and s <= 0.0:
            raise ValueError(f"size must be positive, got {s}")
    return (sx, sy)


def fit_view2d(
    xlim: tuple[float, float],
    ylim: tuple[float, float],
    *,
    xscale: Scale | str = "linear",
    yscale: Scale | str = "linear",
    base: float = 10.0,
    border_world: float = 0.0,
    border_px: float = 60.0,
    stretch: StretchMode = "fit",
    x_intervals: "Sequence[float] | None" = None,
    y_intervals: "Sequence[float] | None" = None,
    pan_xlim: "Sequence[float] | None" = None,
    pan_ylim: "Sequence[float] | None" = None,
    min_zoom: float | None = None,
    max_zoom: float | None = None,
) -> View2DConfig:
    """Compute a centred :class:`View2DConfig` for the given data ranges.

    Mirrors the camera that :class:`CoordinateSystem` applies when it owns the
    scene camera (2D, no explicit ``size``): the visible world rectangle is the
    scale-mapped span of ``xlim``/``ylim`` centred at the origin.  Useful for
    embedding an exact per-pane camera into a ``SceneView(..., camera=...)`` at
    layout-construction time (before ``Visualizer.show``), e.g.::

        SceneView("sin", camera=fit_view2d((0, 6.28), (-1.2, 1.2)))

    Args:
        xlim: Data ``(lo, hi)`` range for the x axis.
        ylim: Data ``(lo, hi)`` range for the y axis.
        xscale: Scale for the x axis (``"linear"``/``"log"`` or a :class:`Scale`).
        yscale: Scale for the y axis (``"linear"``/``"log"`` or a :class:`Scale`).
        base: Logarithm base when a scale is given as ``"log"``.
        border_world: World-unit margin added on all sides.
        border_px: Pixel margin added on all sides (applied by the frontend).
            Defaults to ``60.0``, matching :class:`CoordinateSystem`'s label
            margin, so per-pane cameras keep axis labels visible.
        stretch: How the plot fills the view — ``"fit"`` (letterbox, default),
            ``"fill"`` (stretch both axes), ``"fill_x"`` (x fills, y keeps
            aspect), or ``"fill_y"`` (y fills, x keeps aspect).
        x_intervals: Allowed tick step values for the x axis (absolute data
            units).  ``None`` auto-generates 1/2/5 steps over the range.  Only
            used to derive the default ``max_zoom``.
        y_intervals: Allowed tick step values for the y axis.
        pan_xlim: Pan bounds for the x axis in data units; defaults to ``xlim``.
        pan_ylim: Pan bounds for the y axis in data units; defaults to ``ylim``.
        min_zoom: Max zoom-out; ``None`` derives it on the frontend so the full
            data rectangle stays contained (``fill_x``/``fill_y`` can zoom out
            until an overflowing axis is fully visible).
        max_zoom: Max zoom-in; ``None`` derives it from the finest interval.

    Returns:
        A :class:`View2DConfig` centred at the origin.
    """
    from ._scale import generate_linear_intervals, normalize_intervals

    xlo, xhi = _as_range(xlim)
    ylo, yhi = _as_range(ylim)
    xs = make_scale(xscale, base)
    ys = make_scale(yscale, base)
    span_x = xs.to_world(xhi) - xs.to_world(xlo)
    span_y = ys.to_world(yhi) - ys.to_world(ylo)

    # Pan bounds (world, centred) — default to the data rectangle.
    cx = (xs.to_world(xlo) + xs.to_world(xhi)) / 2.0
    cy = (ys.to_world(ylo) + ys.to_world(yhi)) / 2.0
    if pan_xlim is not None:
        plo, phi = _as_range(pan_xlim)
        pan_xmin, pan_xmax = sorted((xs.to_world(plo) - cx, xs.to_world(phi) - cx))
    else:
        pan_xmin, pan_xmax = -span_x / 2.0, span_x / 2.0
    if pan_ylim is not None:
        plo, phi = _as_range(pan_ylim)
        pan_ymin, pan_ymax = sorted((ys.to_world(plo) - cy, ys.to_world(phi) - cy))
    else:
        pan_ymin, pan_ymax = -span_y / 2.0, span_y / 2.0

    # Derive the default max zoom-in from the finest allowed interval.
    if max_zoom is None:
        spans: list[float] = []
        if not xs.is_log:
            xi = normalize_intervals(x_intervals) or generate_linear_intervals(xlo, xhi)
            if xi:
                spans.append(span_x / xi[0])
        if not ys.is_log:
            yi = normalize_intervals(y_intervals) or generate_linear_intervals(ylo, yhi)
            if yi:
                spans.append(span_y / yi[0])
        max_zoom = min(spans) if spans else None

    return View2DConfig(
        xmin=-span_x / 2.0,
        xmax=span_x / 2.0,
        ymin=-span_y / 2.0,
        ymax=span_y / 2.0,
        border_world=border_world,
        border_px=border_px,
        stretch=stretch,
        pan_xmin=pan_xmin,
        pan_xmax=pan_xmax,
        pan_ymin=pan_ymin,
        pan_ymax=pan_ymax,
        min_zoom=min_zoom,
        max_zoom=max_zoom,
    )


def _as_align(value: "Sequence[float] | None") -> tuple[float, float]:
    """Normalize an ``align`` spec to a ``(ax, ay)`` fraction pair."""
    if value is None:
        return (0.5, 0.5)
    if len(value) != 2:
        raise ValueError(f"align must be an (ax, ay) pair, got {value!r}")
    return (float(value[0]), float(value[1]))


def _as_axis_origin(
    value: "Sequence[float | None] | None",
) -> tuple[float | None, float | None]:
    """Normalize an ``axis_origin`` spec to an optional ``(x, y)`` data pair.

    ``None`` (the spec or one element) means "that axis' min edge".
    """
    if value is None:
        return (None, None)
    if len(value) != 2:
        raise ValueError(f"axis_origin must be an (x, y) pair, got {value!r}")
    return (
        None if value[0] is None else float(value[0]),
        None if value[1] is None else float(value[1]),
    )


def _cross(
    a: tuple[float, float, float], b: tuple[float, float, float]
) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _normalize(
    v: "tuple[float, float, float]",
) -> "tuple[float, float, float] | None":
    n = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    if n < 1e-12:
        return None
    return (v[0] / n, v[1] / n, v[2] / n)


def _resolve_limit(
    limit: "Sequence[float] | None",
    scale: Scale,
    space_dim: int,
    camera: "CameraConfig | View2DConfig | None",
    axis: str = "x",
) -> tuple[float, float]:
    """Resolve an axis range, falling back to the camera rect or a default."""
    if limit is not None:
        lo, hi = _as_range(limit)
    elif space_dim == 2 and isinstance(camera, CameraConfig2d):
        lo, hi = (
            (camera.xmin, camera.xmax) if axis == "x" else (camera.ymin, camera.ymax)
        )
    elif scale.is_log:
        lo, hi = 0.1, 100.0
    else:
        lo, hi = -5.0, 5.0
    return (min(lo, hi), max(lo, hi))


def _default_x_axis_style() -> AxisStyle:
    """Default x-axis style: value labels below, name label further down."""
    return AxisStyle(
        value_style=LabelStyle(align=(0.5, 0.0), offset_2d=(0.0, 6.0)),
        label_style=LabelStyle(align=(0.5, 0.0), offset_2d=(0.0, 28.0)),
    )


def _default_y_axis_style() -> AxisStyle:
    """Default y-axis style: right-aligned labels left, rotated name label."""
    return AxisStyle(
        value_style=LabelStyle(align=(1.0, 0.5), offset_2d=(-8.0, 0.0)),
        label_style=LabelStyle(
            align=(0.5, 0.5), offset_2d=(-50.0, 0.0), rotation=-90.0
        ),
    )


class CoordinateSystem:
    """A plotting coordinate system (axes + grid + optional plane) in one group.

    Parameters
    ----------
    target:
        A :class:`~pytanga.viz.Visualizer` or :class:`~pytanga.viz.VizSceneHandle`.
    xlim, ylim:
        ``(lo, hi)`` data ranges.  ``None`` auto-derives from a configured 2D
        camera rect, or defaults to ``(-5, 5)`` (``(0.1, 100)`` for log).
    xscale, yscale:
        ``"linear"`` / ``"log"`` or a :class:`~pytanga.viz._scale.Scale`.
    size:
        ``(size_x, size_y)`` world extents of the plot (plane width/height in
        embedding units).  ``None`` (or a ``None`` element) derives that axis
        from the data range — so the data range is otherwise stretched
        independently onto the given size.  In 2D, giving ``size`` switches to
        manual placement (via ``position``/``up``) and disables the auto camera.
    align:
        ``(ax, ay)`` fractional point of the plot plane that coincides with
        ``position`` — ``(0, 0)`` puts the bottom-left corner there, ``(1, 1)``
        the top-right.  Default ``(0.5, 0.5)`` (centre).
    axis_origin:
        ``(x, y)`` data point where the two axes cross.  ``None`` (or a ``None``
        element) uses that axis' min edge — the current spine layout.
    min_x_span:
        Minimum x-range span used when auto-fitting the x axis from registered
        plots (see :meth:`add_plot`); default ``5.0``.
    x_intervals, y_intervals:
        Allowed tick step values for the x / y axis (absolute data units,
        ascending).  ``None`` auto-generates ``1/2/5 × 10^k`` steps spanning the
        data range.  The smallest value is the finest subdivision and bounds the
        default zoom-in; linear scales only.
    min_tick_spacing_px:
        Minimum pixel spacing between adjacent ticks (overlay mode only).  The
        frontend derives the tick count per axis from the live viewport, so
        resizing or zooming re-densifies the grid.  Default ``60.0``.
    pan_xlim, pan_ylim:
        Pan bounds for the x / y axis in data units; the view centre stays
        within this rectangle (its edges can reach the view centre, never
        cross).  Defaults to ``xlim`` / ``ylim``.
    min_zoom, max_zoom:
        Interactive zoom range.  ``min_zoom`` is the max zoom-out; ``None`` (the
        default) derives it on the frontend so the full data rectangle stays
        contained — for ``fill_x``/``fill_y`` this lets you zoom out until the
        overflowing axis is fully visible.  ``max_zoom`` is the max zoom-in and
        defaults to the zoom where the finest allowed interval fills the view.
    base:
        Log base used when a scale is given as ``"log"``.
    value_format:
        Python format specifier for tick labels (default ``".4g"``).
    labels:
        ``(x, y)`` axis name labels.
    grid, axes:
        Whether to draw the grid / axes.
    display_mode:
        ``"world"`` (default) draws axes/grid as world-space scene objects that
        pan/zoom with the data.  ``"overlay"`` (2D only, no explicit ``size``)
        draws the axes as a fixed screen-space overlay frame and the grid as a
        screen-space underlay behind the data, with ranges tracked from the live
        camera.
    plane:
        Whether to draw a background plane.  ``None`` auto-enables in 3D.
    camera:
        ``"auto"`` (set a framing camera only if none is configured), ``True``
        (always set/update), or ``False`` (never).  Only affects 2D (and only
        when ``size`` is not given); a 3D coordinate system never sets the
        camera.
    stretch:
        How the 2D camera frames the plot plane: ``"fit"`` (letterbox,
        default), ``"fill"`` (stretch both axes), ``"fill_x"`` (x fills, y
        keeps aspect), or ``"fill_y"`` (y fills, x keeps aspect).  Only
        affects 2D (when this coordinate system owns the camera).  In
        ``display_mode="overlay"`` this is forced to ``"fill"`` so the data
        fills the fixed frame (letterboxing would leave grid lines outside the
        frame).
    border_px, border_world:
        2D camera margins so axis labels are visible.
    position, normal, up:
        Placement of the plot plane: the world point it sits at (combined with
        ``align``), its normal (3D), and the in-plane up/vertical direction
        (2D/3D).
    """

    def __init__(
        self,
        target: "Visualizer | VizSceneHandle",
        *,
        xlim: "Sequence[float] | None" = None,
        ylim: "Sequence[float] | None" = None,
        xscale: Scale | str = "linear",
        yscale: Scale | str = "linear",
        size: "Sequence[float | None] | None" = None,
        align: "Sequence[float] | None" = (0.5, 0.5),
        axis_origin: "Sequence[float | None] | None" = None,
        min_x_span: float = 5.0,
        x_intervals: "Sequence[float] | None" = None,
        y_intervals: "Sequence[float] | None" = None,
        min_tick_spacing_px: float = 60.0,
        pan_xlim: "Sequence[float] | None" = None,
        pan_ylim: "Sequence[float] | None" = None,
        min_zoom: float | None = None,
        max_zoom: float | None = None,
        base: float = 10.0,
        value_format: str = ".4g",
        labels: "Sequence[str]" = ("x", "y"),
        grid: bool = True,
        axes: bool = True,
        display_mode: Literal["world", "overlay"] = "world",
        plane: bool | None = None,
        camera: str | bool = "auto",
        stretch: StretchMode = "fit",
        border_px: float = 60.0,
        border_world: float = 0.0,
        position: "Point | Direction | tuple[float, float, float]" = (0.0, 0.0, 0.0),
        normal: "Point | Direction | tuple[float, float, float]" = (0.0, 0.0, 1.0),
        up: "Point | Direction | tuple[float, float, float]" = (0.0, 1.0, 0.0),
        x_style: AxisStyle | None = None,
        y_style: AxisStyle | None = None,
        grid_style: GridStyle | None = None,
        plane_style: PlaneStyle | None = None,
        group_name: str = "coordsys",
    ) -> None:
        self._handle = _coerce_handle(target)
        self._space_dim = int(self._handle.scene.config.space_dim)

        self._base = float(base)
        self._xscale = make_scale(xscale, self._base)
        self._yscale = make_scale(yscale, self._base)
        self._size = _as_size(size)
        self._size_given = size is not None
        self._display_mode = display_mode
        if display_mode not in ("world", "overlay"):
            raise ValueError(
                f"display_mode must be 'world' or 'overlay', got {display_mode!r}"
            )
        if display_mode == "overlay" and (self._space_dim != 2 or self._size_given):
            raise ValueError(
                "display_mode='overlay' requires a 2D coordinate system "
                "without an explicit size"
            )
        self._align = _as_align(align)
        self._axis_origin = _as_axis_origin(axis_origin)
        self.min_x_span = float(min_x_span)
        self.value_format = value_format
        self.labels = tuple(labels)

        self.show_grid = bool(grid)
        self.show_axes = bool(axes)
        self._show_plane = (self._space_dim == 3) if plane is None else bool(plane)

        self.border_px = float(border_px)
        self.border_world = float(border_world)

        self.x_style = x_style if x_style is not None else _default_x_axis_style()
        self.y_style = y_style if y_style is not None else _default_y_axis_style()
        self.grid_style = grid_style if grid_style is not None else GridStyle()
        self.plane_style = (
            plane_style if plane_style is not None else PlaneStyle(opacity=0.3)
        )

        self._position = _as_vec3(position)
        self._normal = _as_vec3(normal)
        self._up = _as_vec3(up)

        self._camera_mode = camera
        # Overlay axes need the data to fill the fixed frame (no letterbox), so
        # `stretch="fit"` would leave grid lines outside the letterboxed data.
        self._stretch = "fill" if display_mode == "overlay" else _validate_stretch(stretch)
        self._recompute_camera_ownership()

        cfg = self._handle.scene.config
        self._xlim = _resolve_limit(
            xlim, self._xscale, self._space_dim, cfg.camera, "x"
        )
        self._ylim = _resolve_limit(
            ylim, self._yscale, self._space_dim, cfg.camera, "y"
        )

        self._x_intervals = self._resolve_intervals(x_intervals, self._xlim, self._xscale)
        self._y_intervals = self._resolve_intervals(y_intervals, self._ylim, self._yscale)
        self.min_tick_spacing_px = max(1.0, float(min_tick_spacing_px))
        self._pan_xlim = pan_xlim
        self._pan_ylim = pan_ylim
        self._min_zoom = None if min_zoom is None else float(min_zoom)
        self._max_zoom = None if max_zoom is None else float(max_zoom)

        self._size_x = 0.0
        self._size_y = 0.0
        self._raw_xlo = 0.0
        self._raw_span_x = 0.0
        self._raw_ylo = 0.0
        self._raw_span_y = 0.0
        self._plot_z = 0.0

        self._group_name = group_name
        self._group = self._handle.add_group(group_name)
        self._data_group = self._group.add_group(f"{group_name}_data")
        self._refs: dict[str, Any] = {}
        self._plots: list[dict[str, Any]] = []
        self._vlines: dict[str, dict[str, Any]] = {}
        self._hlines: dict[str, dict[str, Any]] = {}
        self._lines: dict[str, dict[str, Any]] = {}
        self._points: dict[str, dict[str, Any]] = {}

        self._build()
        self._apply_transform()
        self._apply_camera()

    # ── Accessors ─────────────────────────────────────────────

    @property
    def group(self) -> "VizObjectRef":
        """The :class:`~pytanga.viz.VizObjectRef` of the underlying group."""
        return self._group

    @property
    def data_group(self) -> "VizObjectRef":
        """The inner data group (child of :attr:`group`) for data-space drawing.

        Children added here live in data coordinates (linear axes) or log-mapped
        coordinates (log axes); the group's transform maps them onto the plot
        plane.  See :meth:`vline` and :meth:`hline` for annotation helpers.
        """
        return self._data_group

    @property
    def handle(self) -> "VizSceneHandle":
        """The scene handle this coordinate system targets."""
        return self._handle

    @property
    def space_dim(self) -> int:
        return self._space_dim

    # ── Build / update ────────────────────────────────────────

    def _build(self) -> None:
        xlo, xhi = self._xlim
        ylo, yhi = self._ylim

        raw_xlo = self._xscale.to_world(xlo)
        raw_xhi = self._xscale.to_world(xhi)
        raw_ylo = self._yscale.to_world(ylo)
        raw_yhi = self._yscale.to_world(yhi)

        self._raw_xlo = raw_xlo
        self._raw_span_x = raw_xhi - raw_xlo
        self._raw_ylo = raw_ylo
        self._raw_span_y = raw_yhi - raw_ylo

        size_x = self._size[0] if self._size[0] is not None else self._raw_span_x
        size_y = self._size[1] if self._size[1] is not None else self._raw_span_y
        self._size_x = size_x
        self._size_y = size_y

        xticks = self._axis_ticks(
            self._xscale, xlo, xhi, size_x, raw_xlo, self._raw_span_x, self._x_intervals
        )
        yticks = self._axis_ticks(
            self._yscale, ylo, yhi, size_y, raw_ylo, self._raw_span_y, self._y_intervals
        )

        x0 = self._axis_origin[0] if self._axis_origin[0] is not None else xlo
        y0 = self._axis_origin[1] if self._axis_origin[1] is not None else ylo
        x0_local = (
            self._norm(raw_xlo, self._raw_span_x, self._xscale.to_world(x0)) - 0.5
        ) * size_x
        y0_local = (
            self._norm(raw_ylo, self._raw_span_y, self._yscale.to_world(y0)) - 0.5
        ) * size_y

        if self._show_plane:
            grid_z, axes_z, plot_z = _GRID_Z_3D, _AXES_Z_3D, _PLOT_Z_3D
        else:
            grid_z, axes_z, plot_z = _GRID_Z_2D, _AXES_Z_2D, _PLOT_Z_2D
        self._plot_z = plot_z

        if self._display_mode == "overlay":
            if self.show_axes:
                self._upsert_axes_overlay()
            if self.show_grid:
                self._upsert_grid_underlay()
        else:
            if self.show_grid:
                grid = Grid(
                    origin=(-size_x / 2.0, -size_y / 2.0, grid_z),
                    dir_u=(1.0, 0.0, 0.0),
                    dir_v=(0.0, 1.0, 0.0),
                    range_u=(0.0, size_x),
                    range_v=(0.0, size_y),
                    line_positions_u=[w for w, _ in xticks],
                    line_positions_v=[w for w, _ in yticks],
                )
                self._upsert("grid", grid, self.grid_style)

            if self.show_axes:
                x_axis = Axis(
                    start=(-size_x / 2.0, y0_local, axes_z),
                    end=(size_x / 2.0, y0_local, axes_z),
                    label=self.labels[0] if self.labels else None,
                    value_format=self.value_format,
                    ticks=xticks,
                )
                y_axis = Axis(
                    start=(x0_local, -size_y / 2.0, axes_z),
                    end=(x0_local, size_y / 2.0, axes_z),
                    label=self.labels[1] if len(self.labels) > 1 else None,
                    value_format=self.value_format,
                    ticks=yticks,
                )
                self._upsert("x", x_axis, self.x_style)
                self._upsert("y", y_axis, self.y_style)

        if self._show_plane:
            plane = Plane(
                point=Point(0.0, 0.0, _PLANE_Z),
                normal=Direction(0.0, 0.0, 1.0),
                span_u=Direction(size_x, 0.0, 0.0),
                span_v=Direction(0.0, size_y, 0.0),
            )
            self._upsert("plane", plane, self.plane_style)

        self._apply_data_transform()
        self._sync_lines()
        self._sync_points()

    def _build_axes_overlay_spec(self) -> dict[str, Any]:
        """Return the ``axes_overlay`` spec (overlay layer, screen-space frame)."""
        return {
            "xscale": "log" if self._xscale.is_log else "linear",
            "yscale": "log" if self._yscale.is_log else "linear",
            "base": self._base,
            "value_format": self.value_format,
            "labels": list(self.labels),
            "border_px": self.border_px,
            "min_tick_spacing_px": self.min_tick_spacing_px,
            "intervals_x": self._x_intervals,
            "intervals_y": self._y_intervals,
            "axis": {"x": self.x_style.to_dict(), "y": self.y_style.to_dict()},
        }

    def _build_grid_underlay_spec(self) -> dict[str, Any]:
        """Return the ``grid_underlay`` spec (underlay layer, screen-space grid)."""
        return {
            "xscale": "log" if self._xscale.is_log else "linear",
            "yscale": "log" if self._yscale.is_log else "linear",
            "base": self._base,
            "border_px": self.border_px,
            "min_tick_spacing_px": self.min_tick_spacing_px,
            "intervals_x": self._x_intervals,
            "intervals_y": self._y_intervals,
            "grid": self.grid_style.to_dict(),
        }

    def _upsert_payload_object(
        self,
        kind: str,
        oid: str,
        spec: dict[str, Any],
        layer: Literal["overlay", "underlay"],
    ) -> None:
        """Create or update a payload-style overlay/underlay node by stable id."""
        from ._nodes import VizOverlayObject
        from .scene import SceneObject

        scene = self._handle.scene
        try:
            node = scene.get_node(oid)
        except KeyError:
            node = None
        if node is None:
            scene.add_object(
                SceneObject(oid, layer=layer, kind=kind, data={"spec": spec}),
                object_id=oid,
            )
        else:
            cast(VizOverlayObject, node).set_payload(spec)

    def _upsert_axes_overlay(self) -> None:
        """Emit/refresh the ``axes_overlay`` (overlay) object for this plot."""
        self._upsert_payload_object(
            "axes_overlay",
            f"{self._group_name}_axes_overlay",
            self._build_axes_overlay_spec(),
            "overlay",
        )

    def _upsert_grid_underlay(self) -> None:
        """Emit/refresh the ``grid_underlay`` (underlay) object for this plot."""
        self._upsert_payload_object(
            "grid_underlay",
            f"{self._group_name}_grid_underlay",
            self._build_grid_underlay_spec(),
            "underlay",
        )

    def _upsert(
        self,
        key: str,
        obj: "Axis | Grid | Plane | Line | Point",
        style: "AxisStyle | GridStyle | PlaneStyle | None",
    ) -> None:
        ref = self._refs.get(key)
        if ref is None:
            ref = self._group.new(obj, style=style)
            self._refs[key] = ref
        else:
            ref.entity = obj

    def _axis_ticks(
        self,
        scale: Scale,
        lo: float,
        hi: float,
        size: float,
        raw_lo: float,
        raw_span: float,
        intervals: list[float] | None = None,
    ) -> list[tuple[float, str]]:
        ticks: list[tuple[float, str]] = []
        for value, _ in scale.ticks(lo, hi, intervals=intervals):
            norm = self._norm(raw_lo, raw_span, scale.to_world(value))
            ticks.append((norm * size, format(value, self.value_format)))
        return ticks

    @staticmethod
    def _norm(raw_lo: float, raw_span: float, value: float) -> float:
        """Normalize a raw scale value to a 0..1 fraction of the data range."""
        if raw_span == 0.0:
            return 0.5
        return (value - raw_lo) / raw_span

    def _local_xy(self, x: float, y: float) -> tuple[float, float]:
        """Map a data point to a centred in-plane ``(lx, ly)`` coordinate."""
        nx = self._norm(
            self._raw_xlo, self._raw_span_x, self._xscale.to_world(float(x))
        )
        ny = self._norm(
            self._raw_ylo, self._raw_span_y, self._yscale.to_world(float(y))
        )
        return ((nx - 0.5) * self._size_x, (ny - 0.5) * self._size_y)

    def _data_xy(self, x: float, y: float) -> tuple[float, float]:
        """Map a data point to scale-world (data-group) ``(wx, wy)`` coordinates."""
        return (self._xscale.to_world(float(x)), self._yscale.to_world(float(y)))

    def _align_offset(self) -> tuple[float, float]:
        """In-plane offset of the ``align`` point from the plane centre."""
        return (
            (self._align[0] - 0.5) * self._size_x,
            (self._align[1] - 0.5) * self._size_y,
        )

    def _rotation_matrix(
        self, normal: "tuple[float, float, float]", up: "tuple[float, float, float]"
    ) -> np.ndarray:
        n = _normalize(normal)
        if n is None:
            raise ValueError("normal must be a non-zero vector")
        u = _normalize(_cross(up, n))
        if u is None:
            u = _normalize(_cross((1.0, 0.0, 0.0), n))
        if u is None:
            u = _normalize(_cross((0.0, 1.0, 0.0), n))
        if u is None:  # pragma: no cover - n is non-zero so this is unreachable
            raise ValueError("could not derive an in-plane axis from normal/up")
        v = _cross(n, u)

        m = np.eye(4)
        m[:3, 0] = u
        m[:3, 1] = v
        m[:3, 2] = n
        return m

    def _apply_data_transform(self) -> None:
        """Set the inner data group's translate+scale (data → local frame).

        The group maps scale-world coordinates ``(to_world(x), to_world(y))``
        onto the centred local frame used by the grid/axes.  Degenerate data
        spans map the single value to the local origin.
        """
        if self._raw_span_x == 0.0:
            sx = 1.0
            tx = -self._raw_xlo
        else:
            sx = self._size_x / self._raw_span_x
            tx = -self._size_x / 2.0 - sx * self._raw_xlo
        if self._raw_span_y == 0.0:
            sy = 1.0
            ty = -self._raw_ylo
        else:
            sy = self._size_y / self._raw_span_y
            ty = -self._size_y / 2.0 - sy * self._raw_ylo
        self._data_group.set_transform(
            position=(tx, ty, self._plot_z),
            rotation=(0.0, 0.0, 0.0),
            scale=(sx, sy, 1.0),
        )

    def _apply_transform(self) -> None:
        if self._space_dim == 2 and not self._size_given:
            # No explicit size → plot centred at the origin (current 2D behaviour).
            self._group.set_transform(
                position=(0.0, 0.0, 0.0),
                rotation=(0.0, 0.0, 0.0),
                scale=(1.0, 1.0, 1.0),
            )
            return
        normal = (0.0, 0.0, 1.0) if self._space_dim == 2 else self._normal
        rotation = self._rotation_matrix(normal, self._up)
        ox, oy = self._align_offset()
        offset_world = rotation[:3, :3] @ np.array([ox, oy, 0.0])
        position = tuple(np.array(self._position) - offset_world)
        euler = _T.to_trs(rotation)[1]
        self._group.set_transform(position=position, rotation=euler)

    def _rebuild(self) -> None:
        """Rebuild geometry and re-apply the group transform."""
        self._build()
        self._apply_transform()

    def _recompute_camera_ownership(self) -> None:
        self._owns_camera = (
            self._space_dim == 2
            and not self._size_given
            and (
                self._camera_mode is True
                or (
                    self._camera_mode == "auto"
                    and self._handle.scene.config.camera is None
                )
            )
        )

    @staticmethod
    def _resolve_intervals(
        intervals: "Sequence[float] | None",
        limit: tuple[float, float],
        scale: Scale,
    ) -> list[float] | None:
        """Normalize explicit intervals, or auto-generate 1/2/5 steps.

        Returns ``None`` for log scales (their subdivision is fixed by the
        base) and for an empty/``None`` explicit list.
        """
        if scale.is_log:
            return None
        return normalize_intervals(intervals) or generate_linear_intervals(*limit)

    def _apply_camera(self) -> None:
        if not self._owns_camera:
            return
        cam = fit_view2d(
            self._xlim,
            self._ylim,
            xscale=self._xscale,
            yscale=self._yscale,
            base=self._base,
            border_world=self.border_world,
            border_px=self.border_px,
            stretch=self._stretch,
            x_intervals=self._x_intervals,
            y_intervals=self._y_intervals,
            pan_xlim=self._pan_xlim,
            pan_ylim=self._pan_ylim,
            min_zoom=self._min_zoom,
            max_zoom=self._max_zoom,
        )
        self._handle.set_camera(cam)

    # ── Data → world helpers ──────────────────────────────────

    def to_local(self, x: float, y: float) -> tuple[float, float]:
        """Map a data point to its centred in-plane ``(lx, ly)`` coordinate."""
        return self._local_xy(x, y)

    def to_world(self, x: float, y: float) -> tuple[float, float, float]:
        """Map a data point to its 3D world position (on the plot plane).

        Applies the group's transform, so the result is the embedded position
        of the data point (accounting for ``position``/``normal``/``up``).
        """
        lx, ly = self._local_xy(x, y)
        w = self._group.world_matrix @ np.array([lx, ly, 0.0, 1.0])
        return (float(w[0]), float(w[1]), float(w[2]))

    def to_data(self, x: float, y: float) -> tuple[float, float]:
        """Map a data point to data-group coordinates (scale-world ``(wx, wy)``).

        For linear axes this equals the data value; for log axes it is
        ``log(value, base)``.  Useful for pre-mapping a point before drawing it
        directly into :attr:`data_group`.
        """
        return self._data_xy(x, y)

    def transform(
        self, xs: "Sequence[float]", ys: "Sequence[float]"
    ) -> list[tuple[float, float, float]]:
        """Map ``(x, y)`` data series to group-local 3D points."""
        out: list[tuple[float, float, float]] = []
        for x, y in zip(xs, ys):
            lx, ly = self._local_xy(x, y)
            out.append((lx, ly, self._plot_z))
        return out

    def plot(
        self,
        xs: "Sequence[float]",
        ys: "Sequence[float]",
        *,
        color: str | None = None,
        style: PointPathStyle | None = None,
    ) -> "VizObjectRef":
        """Plot an ``(x, y)`` data series as a :class:`~pytanga.viz.PointPath`.

        Data is mapped through the scales and added as a child of the data
        group, whose transform places it on the plot plane (so it inherits the
        outer group's 3D placement).
        """
        path = PointPath()
        for x, y in zip(xs, ys):
            wx, wy = self._data_xy(x, y)
            path.add((wx, wy, 0.0), color=color)
        kwargs = {} if style is None else {"style": style}
        return self._data_group.new(path, color=color, **kwargs)

    # ── Registered (live) plots ───────────────────────────────

    def add_plot(
        self,
        path: PointPath,
        *,
        color: str | None = None,
        style: PointPathStyle | None = None,
        auto_x: bool = False,
    ) -> "VizObjectRef":
        """Register a live :class:`~pytanga.viz.PointPath` and add it to the data group.

        The path's points are in **data** coordinates; the coordinate system
        maps them onto the plot plane.  After mutating the path, call
        :meth:`update_plots` (then ``flush()`` on the scene) to refresh the view.

        With ``auto_x=True``, :meth:`update_plots` fits the x axis to the path's
        current x range (with a minimum span of ``min_x_span``) — useful for a
        live time axis.
        """
        render = PointPath()
        kwargs = {} if style is None else {"style": style}
        ref = self._data_group.new(render, color=color, **kwargs)
        entry: dict[str, Any] = {
            "path": path,
            "ref": ref,
            "render": render,
            "auto_x": bool(auto_x),
        }
        self._plots.append(entry)
        if entry["auto_x"]:
            self._fit_x()
        self._sync_plot(entry)
        return ref

    def update_plots(self) -> None:
        """Re-sync all registered plots and re-fit the auto-x range."""
        self._fit_x()
        for entry in self._plots:
            self._sync_plot(entry)

    def _sync_plot(self, entry: dict[str, Any]) -> None:
        src = entry["path"]
        render = entry["render"]
        render.clear()
        src_points = src.points
        src_colors = src.colors
        for i, (x, y, _z) in enumerate(src_points):
            wx, wy = self._data_xy(x, y)
            color = src_colors[i] if i < len(src_colors) else None
            render.add((wx, wy, 0.0), color=color)
        entry["ref"].entity = render

    def _fit_x(self) -> None:
        xs: list[float] = []
        for entry in self._plots:
            if entry["auto_x"]:
                xs.extend(p[0] for p in entry["path"].points)
        if not xs:
            return
        lo = min(xs)
        hi = max(xs)
        span = hi - lo
        if span < self.min_x_span:
            center = (lo + hi) / 2.0
            lo = center - self.min_x_span / 2.0
            hi = center + self.min_x_span / 2.0
        new_lim = (lo, hi)
        if new_lim != self._xlim:
            self.xlim = new_lim

    # ── Annotation lines (data-frame markers) ─────────────────

    def vline(
        self,
        x: float,
        *,
        name: str | None = None,
        y0: float | None = None,
        y1: float | None = None,
        color: str | None = None,
        style: ObjVizStyle | None = None,
        label: str | None = None,
        label_style: LabelStyle | None = None,
    ) -> "VizObjectRef":
        """Create or update a vertical line at data ``x``.

        The line spans ``y0..y1`` in data coordinates; ``None`` (the default)
        tracks the current ``ylim``.  Pass ``name`` to update the same line in
        place (e.g. to animate it); without a name a new line is created each
        call.  ``label``/``label_style`` attach a label (default anchor: the
        line midpoint; use ``LabelStyle(along=…)`` to move it).  Returns the
        :class:`~pytanga.viz.VizObjectRef` of the line.
        """
        return self._upsert_line(
            "v", float(x), name, y0, y1, color, style, label, label_style
        )

    def hline(
        self,
        y: float,
        *,
        name: str | None = None,
        x0: float | None = None,
        x1: float | None = None,
        color: str | None = None,
        style: ObjVizStyle | None = None,
        label: str | None = None,
        label_style: LabelStyle | None = None,
    ) -> "VizObjectRef":
        """Create or update a horizontal line at data ``y``.

        The line spans ``x0..x1`` in data coordinates; ``None`` (the default)
        tracks the current ``xlim``.  Pass ``name`` to update the same line in
        place (e.g. to animate it); without a name a new line is created each
        call.  ``label``/``label_style`` attach a label (default anchor: the
        line midpoint; use ``LabelStyle(along=…)`` to move it).  Returns the
        :class:`~pytanga.viz.VizObjectRef` of the line.
        """
        return self._upsert_line(
            "h", float(y), name, x0, x1, color, style, label, label_style
        )

    def line(
        self,
        start: "tuple[float, float] | Point",
        end: "tuple[float, float] | Point",
        *,
        name: str | None = None,
        color: str | None = None,
        style: ObjVizStyle | None = None,
        label: str | None = None,
        label_style: LabelStyle | None = None,
    ) -> "VizObjectRef":
        """Draw a line between two data points.

        ``start`` and ``end`` are data coordinates, each given as an ``(x, y)``
        2-tuple or a :class:`~pytanga.geometry.entities.Point`.  Pass ``name`` to
        update the same line in place; without a name a new line is created each
        call.  ``label``/``label_style`` attach a label (default anchor: the
        line midpoint).  Returns the :class:`~pytanga.viz.VizObjectRef` of the
        line.
        """
        p0 = self._normalize_point(start)
        p1 = self._normalize_point(end)
        return self._upsert_segment(p0, p1, name, color, style, label, label_style)

    def point(
        self,
        p: "tuple[float, float] | Point",
        *,
        name: str | None = None,
        color: str | None = None,
        style: ObjVizStyle | None = None,
        label: str | None = None,
        label_style: LabelStyle | None = None,
    ) -> "VizObjectRef":
        """Create or update a point marker at a data location.

        ``p`` is a data coordinate, given as an ``(x, y)`` 2-tuple or a
        :class:`~pytanga.geometry.entities.Point`.  Pass ``name`` to update the
        same marker in place; without a name a new marker is created each call.
        ``label``/``label_style`` attach a label anchored at the point.  Returns
        the :class:`~pytanga.viz.VizObjectRef` of the marker.

        The marker is added to the outer group at its local position (not the
        data group), so it is not stretched by the data group's non-uniform
        scale.
        """
        px, py = self._normalize_point(p)
        return self._upsert_point((px, py), name, color, style, label, label_style)

    def remove_vline(self, name: str) -> None:
        """Remove a named vertical line (a no-op if the name is unknown)."""
        entry = self._vlines.pop(name, None)
        if entry is not None:
            entry["ref"].remove()

    def remove_hline(self, name: str) -> None:
        """Remove a named horizontal line (a no-op if the name is unknown)."""
        entry = self._hlines.pop(name, None)
        if entry is not None:
            entry["ref"].remove()

    def remove_line(self, name: str) -> None:
        """Remove a named line (a no-op if the name is unknown)."""
        entry = self._lines.pop(name, None)
        if entry is not None:
            entry["ref"].remove()

    def remove_point(self, name: str) -> None:
        """Remove a named point marker (a no-op if the name is unknown)."""
        entry = self._points.pop(name, None)
        if entry is not None:
            entry["ref"].remove()

    def _upsert_line(
        self,
        kind: str,
        value: float,
        name: str | None,
        c0: float | None,
        c1: float | None,
        color: str | None,
        style: ObjVizStyle | None,
        label: str | None,
        label_style: LabelStyle | None,
    ) -> "VizObjectRef":
        store = self._vlines if kind == "v" else self._hlines
        if name is None:
            prefix = "vline" if kind == "v" else "hline"
            index = len(store)
            name = f"{prefix}_{index}"
            while name in store:
                index += 1
                name = f"{prefix}_{index}"
        entry: dict[str, Any] | None = store.get(name)
        if entry is None:
            entry = {
                "name": name,
                "value": value,
                "c0": None if c0 is None else float(c0),
                "c1": None if c1 is None else float(c1),
                "label": label,
                "label_style": label_style,
            }
            entry["ref"] = self._data_group.new(
                self._make_line(entry, kind),
                color=color,
                **self._annotation_kwargs(style, label, label_style),
            )
            store[name] = entry
        else:
            entry["value"] = value
            if c0 is not None:
                entry["c0"] = float(c0)
            if c1 is not None:
                entry["c1"] = float(c1)
            self._sync_line(entry, kind)
        ref: "VizObjectRef" = entry["ref"]
        return ref

    @staticmethod
    def _normalize_point(value: "tuple[float, float] | Point") -> tuple[float, float]:
        """Normalize a data point given as an ``(x, y)`` pair or a ``Point``."""
        if hasattr(value, "x") and hasattr(value, "y"):
            pt = cast("Any", value)
            return (float(pt.x), float(pt.y))
        seq = tuple(value)
        if len(seq) != 2:
            raise ValueError(f"expected an (x, y) pair or a Point, got {value!r}")
        return (float(seq[0]), float(seq[1]))

    @staticmethod
    def _annotation_kwargs(
        style: ObjVizStyle | None,
        label: str | None,
        label_style: LabelStyle | None,
    ) -> dict[str, Any]:
        """Collect the non-``None`` creation kwargs for an annotation."""
        kwargs: dict[str, Any] = {}
        if style is not None:
            kwargs["style"] = style
        if label is not None:
            kwargs["label"] = label
        if label_style is not None:
            kwargs["label_style"] = label_style
        return kwargs

    def _upsert_segment(
        self,
        p0: tuple[float, float],
        p1: tuple[float, float],
        name: str | None,
        color: str | None,
        style: ObjVizStyle | None,
        label: str | None,
        label_style: LabelStyle | None,
    ) -> "VizObjectRef":
        if name is None:
            prefix = "line"
            index = len(self._lines)
            name = f"{prefix}_{index}"
            while name in self._lines:
                index += 1
                name = f"{prefix}_{index}"
        entry: dict[str, Any] | None = self._lines.get(name)
        if entry is None:
            entry = {
                "name": name,
                "p0": p0,
                "p1": p1,
                "label": label,
                "label_style": label_style,
            }
            entry["ref"] = self._data_group.new(
                self._make_line(entry, "l"),
                color=color,
                **self._annotation_kwargs(style, label, label_style),
            )
            self._lines[name] = entry
        else:
            entry["p0"] = p0
            entry["p1"] = p1
            self._sync_line(entry, "l")
        ref: "VizObjectRef" = entry["ref"]
        return ref

    def _upsert_point(
        self,
        p: tuple[float, float],
        name: str | None,
        color: str | None,
        style: ObjVizStyle | None,
        label: str | None,
        label_style: LabelStyle | None,
    ) -> "VizObjectRef":
        if name is None:
            prefix = "point"
            index = len(self._points)
            name = f"{prefix}_{index}"
            while name in self._points:
                index += 1
                name = f"{prefix}_{index}"
        entry: dict[str, Any] | None = self._points.get(name)
        if entry is None:
            entry = {
                "name": name,
                "p": p,
                "label": label,
                "label_style": label_style,
            }
            entry["ref"] = self._group.new(
                self._make_point(entry),
                color=color,
                **self._annotation_kwargs(style, label, label_style),
            )
            self._points[name] = entry
        else:
            entry["p"] = p
            self._sync_point(entry)
        ref: "VizObjectRef" = entry["ref"]
        return ref

    def _sync_points(self) -> None:
        for entry in self._points.values():
            self._sync_point(entry)

    def _sync_point(self, entry: dict[str, Any]) -> None:
        entry["ref"].entity = self._make_point(entry)

    def _make_point(self, entry: dict[str, Any]) -> Point:
        lx, ly = self._local_xy(*entry["p"])
        return Point(lx, ly, self._plot_z)

    def _sync_lines(self) -> None:
        for entry in self._vlines.values():
            self._sync_line(entry, "v")
        for entry in self._hlines.values():
            self._sync_line(entry, "h")
        for entry in self._lines.values():
            self._sync_line(entry, "l")

    def _sync_line(self, entry: dict[str, Any], kind: str) -> None:
        entry["ref"].entity = self._make_line(entry, kind)

    def _make_line(self, entry: dict[str, Any], kind: str) -> Line:
        if kind == "v":
            value = entry["value"]
            c0 = entry["c0"]
            c1 = entry["c1"]
            lo = self._ylim[0] if c0 is None else c0
            hi = self._ylim[1] if c1 is None else c1
            p0 = (*self._data_xy(value, lo), 0.0)
            p1 = (*self._data_xy(value, hi), 0.0)
        elif kind == "h":
            value = entry["value"]
            c0 = entry["c0"]
            c1 = entry["c1"]
            lo = self._xlim[0] if c0 is None else c0
            hi = self._xlim[1] if c1 is None else c1
            p0 = (*self._data_xy(lo, value), 0.0)
            p1 = (*self._data_xy(hi, value), 0.0)
        else:  # kind == "l"
            p0 = (*self._data_xy(*entry["p0"]), 0.0)
            p1 = (*self._data_xy(*entry["p1"]), 0.0)
        return Line.from_points(Point(*p0), Point(*p1))

    # ── Mutators (rebuild / re-frame in place) ────────────────

    @property
    def xlim(self) -> tuple[float, float]:
        return self._xlim

    @xlim.setter
    def xlim(self, value: "Sequence[float] | None") -> None:
        self._xlim = _as_range(value)
        self._rebuild()
        self._apply_camera()

    @property
    def ylim(self) -> tuple[float, float]:
        return self._ylim

    @ylim.setter
    def ylim(self, value: "Sequence[float] | None") -> None:
        self._ylim = _as_range(value)
        self._rebuild()
        self._apply_camera()

    @property
    def xscale(self) -> Scale:
        return self._xscale

    @xscale.setter
    def xscale(self, value: Scale | str) -> None:
        self._xscale = make_scale(value, self._base)
        self._rebuild()
        self._apply_camera()

    @property
    def yscale(self) -> Scale:
        return self._yscale

    @yscale.setter
    def yscale(self, value: Scale | str) -> None:
        self._yscale = make_scale(value, self._base)
        self._rebuild()
        self._apply_camera()

    @property
    def size(self) -> tuple[float | None, float | None]:
        return self._size

    @size.setter
    def size(self, value: "Sequence[float | None] | None") -> None:
        self._size = _as_size(value)
        self._size_given = value is not None
        self._rebuild()
        self._recompute_camera_ownership()
        self._apply_camera()

    @property
    def align(self) -> tuple[float, float]:
        return self._align

    @align.setter
    def align(self, value: "Sequence[float] | None") -> None:
        self._align = _as_align(value)
        self._apply_transform()

    @property
    def axis_origin(self) -> tuple[float | None, float | None]:
        return self._axis_origin

    @axis_origin.setter
    def axis_origin(self, value: "Sequence[float | None] | None") -> None:
        self._axis_origin = _as_axis_origin(value)
        self._build()

    @property
    def base(self) -> float:
        return self._base

    @base.setter
    def base(self, value: float) -> None:
        self._base = float(value)
        if isinstance(self._xscale, LogScale):
            self._xscale = LogScale(self._base)
        if isinstance(self._yscale, LogScale):
            self._yscale = LogScale(self._base)
        self._rebuild()
        self._apply_camera()

    @property
    def position(self) -> tuple[float, float, float]:
        return self._position

    @position.setter
    def position(self, value: "Point | Direction | tuple[float, float, float]") -> None:
        self._position = _as_vec3(value)
        self._apply_transform()
        self._apply_camera()

    @property
    def normal(self) -> tuple[float, float, float]:
        return self._normal

    @normal.setter
    def normal(self, value: "Point | Direction | tuple[float, float, float]") -> None:
        self._normal = _as_vec3(value)
        self._apply_transform()
        self._apply_camera()

    @property
    def up(self) -> tuple[float, float, float]:
        return self._up

    @up.setter
    def up(self, value: "Point | Direction | tuple[float, float, float]") -> None:
        self._up = _as_vec3(value)
        self._apply_transform()
        self._apply_camera()
