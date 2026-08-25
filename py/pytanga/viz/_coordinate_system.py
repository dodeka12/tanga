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
from typing import Any

import numpy as np

from pytanga.geometry.entities import Direction, Plane, Point

from . import _transforms as _T
from ._point_path import PointPath
from ._scale import LogScale, Scale, make_scale
from ._scene_objects import Axis, Grid
from .camera import CameraConfig2d, View2DConfig
from ._styles import AxisStyle, GridStyle, LabelStyle, PlaneStyle

# Local-frame z ordering within the group.
_PLANE_Z = 0.0
_GRID_Z_3D = 0.01
_AXES_Z_3D = 0.02
_PLOT_Z_3D = 0.03
_GRID_Z_2D = -1.0
_AXES_Z_2D = -0.5
_PLOT_Z_2D = 0.0


def _coerce_handle(target):
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


def _as_range(value) -> tuple[float, float]:
    """Normalize a ``(lo, hi)`` pair to an ascending float tuple."""
    if value is None:
        raise ValueError("range must be a (lo, hi) pair, not None")
    if len(value) != 2:  # type: ignore[arg-type]
        raise ValueError(f"range must be a (lo, hi) pair, got {value!r}")
    lo, hi = float(value[0]), float(value[1])  # type: ignore[index]
    return (min(lo, hi), max(lo, hi))


def _as_vec3(value) -> tuple[float, float, float]:
    if hasattr(value, "x") and hasattr(value, "y") and hasattr(value, "z"):
        return (float(value.x), float(value.y), float(value.z))
    if len(value) != 3:  # type: ignore[arg-type]
        raise ValueError(f"expected a 3-vector, got {value!r}")
    return (float(value[0]), float(value[1]), float(value[2]))  # type: ignore[index]


def _as_size(value) -> tuple[float | None, float | None]:
    """Normalize a ``size`` spec to an optional ``(size_x, size_y)`` pair.

    ``None`` (either the whole spec or one element) means "derive from the data
    range".  Explicit sizes must be positive.
    """
    if value is None:
        return (None, None)
    if len(value) != 2:  # type: ignore[arg-type]
        raise ValueError(f"size must be a (size_x, size_y) pair, got {value!r}")
    sx = None if value[0] is None else float(value[0])  # type: ignore[index]
    sy = None if value[1] is None else float(value[1])  # type: ignore[index]
    for s in (sx, sy):
        if s is not None and s <= 0.0:
            raise ValueError(f"size must be positive, got {s}")
    return (sx, sy)


def _as_align(value) -> tuple[float, float]:
    """Normalize an ``align`` spec to a ``(ax, ay)`` fraction pair."""
    if value is None:
        return (0.5, 0.5)
    if len(value) != 2:  # type: ignore[arg-type]
        raise ValueError(f"align must be an (ax, ay) pair, got {value!r}")
    return (float(value[0]), float(value[1]))  # type: ignore[index]


def _as_axis_origin(value) -> tuple[float | None, float | None]:
    """Normalize an ``axis_origin`` spec to an optional ``(x, y)`` data pair.

    ``None`` (the spec or one element) means "that axis' min edge".
    """
    if value is None:
        return (None, None)
    if len(value) != 2:  # type: ignore[arg-type]
        raise ValueError(f"axis_origin must be an (x, y) pair, got {value!r}")
    return (
        None if value[0] is None else float(value[0]),  # type: ignore[index]
        None if value[1] is None else float(value[1]),  # type: ignore[index]
    )


def _cross(a, b) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _normalize(v):
    n = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    if n < 1e-12:
        return None
    return (v[0] / n, v[1] / n, v[2] / n)


def _resolve_limit(
    limit,
    scale: Scale,
    space_dim: int,
    camera,
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
    base:
        Log base used when a scale is given as ``"log"``.
    value_format:
        Python format specifier for tick labels (default ``".4g"``).
    labels:
        ``(x, y)`` axis name labels.
    grid, axes:
        Whether to draw the grid / axes.
    plane:
        Whether to draw a background plane.  ``None`` auto-enables in 3D.
    camera:
        ``"auto"`` (set a framing camera only if none is configured), ``True``
        (always set/update), or ``False`` (never).  Only affects 2D (and only
        when ``size`` is not given); a 3D coordinate system never sets the
        camera.
    border_px, border_world:
        2D camera margins so axis labels are visible.
    position, normal, up:
        Placement of the plot plane: the world point it sits at (combined with
        ``align``), its normal (3D), and the in-plane up/vertical direction
        (2D/3D).
    """

    def __init__(
        self,
        target,
        *,
        xlim=None,
        ylim=None,
        xscale="linear",
        yscale="linear",
        size=None,
        align=(0.5, 0.5),
        axis_origin=None,
        min_x_span: float = 5.0,
        base: float = 10.0,
        value_format: str = ".4g",
        labels=("x", "y"),
        grid: bool = True,
        axes: bool = True,
        plane: bool | None = None,
        camera: str | bool = "auto",
        border_px: float = 60.0,
        border_world: float = 0.0,
        position=(0.0, 0.0, 0.0),
        normal=(0.0, 0.0, 1.0),
        up=(0.0, 1.0, 0.0),
        x_style=None,
        y_style=None,
        grid_style=None,
        plane_style=None,
        group_name: str = "coordsys",
    ) -> None:
        self._handle = _coerce_handle(target)
        self._space_dim = int(self._handle.scene.config.space_dim)

        self._base = float(base)
        self._xscale = make_scale(xscale, self._base)
        self._yscale = make_scale(yscale, self._base)
        self._size = _as_size(size)
        self._size_given = size is not None
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
        self._recompute_camera_ownership()

        cfg = self._handle.scene.config
        self._xlim = _resolve_limit(
            xlim, self._xscale, self._space_dim, cfg.camera, "x"
        )
        self._ylim = _resolve_limit(
            ylim, self._yscale, self._space_dim, cfg.camera, "y"
        )

        self._size_x = 0.0
        self._size_y = 0.0
        self._raw_xlo = 0.0
        self._raw_span_x = 0.0
        self._raw_ylo = 0.0
        self._raw_span_y = 0.0
        self._plot_z = 0.0

        self._group = self._handle.add_group(group_name)
        self._data_group = self._group.add_group(f"{group_name}_data")
        self._refs: dict[str, object] = {}
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
    def group(self):
        """The :class:`~pytanga.viz.VizObjectRef` of the underlying group."""
        return self._group

    @property
    def data_group(self):
        """The inner data group (child of :attr:`group`) for data-space drawing.

        Children added here live in data coordinates (linear axes) or log-mapped
        coordinates (log axes); the group's transform maps them onto the plot
        plane.  See :meth:`vline` and :meth:`hline` for annotation helpers.
        """
        return self._data_group

    @property
    def handle(self):
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
            self._xscale, xlo, xhi, size_x, raw_xlo, self._raw_span_x
        )
        yticks = self._axis_ticks(
            self._yscale, ylo, yhi, size_y, raw_ylo, self._raw_span_y
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

    def _upsert(self, key: str, obj, style) -> None:
        ref = self._refs.get(key)
        if ref is None:
            ref = self._group.new(obj, style=style)
            self._refs[key] = ref
        else:
            ref.entity = obj  # type: ignore[attr-defined]

    def _axis_ticks(
        self, scale: Scale, lo, hi, size, raw_lo, raw_span
    ) -> list[tuple[float, str]]:
        ticks: list[tuple[float, str]] = []
        for value, _ in scale.ticks(lo, hi):
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

    def _rotation_matrix(self, normal, up) -> np.ndarray:
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

    def _apply_camera(self) -> None:
        if not self._owns_camera:
            return
        xlo, xhi = self._xlim
        ylo, yhi = self._ylim
        span_x = self._xscale.to_world(xhi) - self._xscale.to_world(xlo)
        span_y = self._yscale.to_world(yhi) - self._yscale.to_world(ylo)
        cam = View2DConfig(
            xmin=-span_x / 2.0,
            xmax=span_x / 2.0,
            ymin=-span_y / 2.0,
            ymax=span_y / 2.0,
            border_world=self.border_world,
            border_px=self.border_px,
            uniform=True,
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

    def transform(self, xs, ys) -> list[tuple[float, float, float]]:
        """Map ``(x, y)`` data series to group-local 3D points."""
        out: list[tuple[float, float, float]] = []
        for x, y in zip(xs, ys):
            lx, ly = self._local_xy(x, y)
            out.append((lx, ly, self._plot_z))
        return out

    def plot(self, xs, ys, *, color=None, style=None):
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

    def add_plot(self, path, *, color=None, style=None, auto_x: bool = False):
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

    def vline(self, x, *, name=None, y0=None, y1=None, color=None, style=None):
        """Create or update a vertical line at data ``x``.

        The line spans ``y0..y1`` in data coordinates; ``None`` (the default)
        tracks the current ``ylim``.  Pass ``name`` to update the same line in
        place (e.g. to animate it); without a name a new line is created each
        call.  Returns the :class:`~pytanga.viz.VizObjectRef` of the line.
        """
        return self._upsert_line("v", float(x), name, y0, y1, color, style)

    def hline(self, y, *, name=None, x0=None, x1=None, color=None, style=None):
        """Create or update a horizontal line at data ``y``.

        The line spans ``x0..x1`` in data coordinates; ``None`` (the default)
        tracks the current ``xlim``.  Pass ``name`` to update the same line in
        place (e.g. to animate it); without a name a new line is created each
        call.  Returns the :class:`~pytanga.viz.VizObjectRef` of the line.
        """
        return self._upsert_line("h", float(y), name, x0, x1, color, style)

    def line(self, start, end, *, name=None, color=None, style=None):
        """Draw a line between two data points.

        ``start`` and ``end`` are data coordinates, each given as an ``(x, y)``
        2-tuple or a :class:`~pytanga.geometry.entities.Point`.  Pass ``name`` to
        update the same line in place; without a name a new line is created each
        call.  Returns the :class:`~pytanga.viz.VizObjectRef` of the line.
        """
        p0 = self._normalize_point(start)
        p1 = self._normalize_point(end)
        return self._upsert_segment(p0, p1, name, color, style)

    def point(self, p, *, name=None, color=None, style=None):
        """Create or update a point marker at a data location.

        ``p`` is a data coordinate, given as an ``(x, y)`` 2-tuple or a
        :class:`~pytanga.geometry.entities.Point`.  Pass ``name`` to update the
        same marker in place; without a name a new marker is created each call.
        Returns the :class:`~pytanga.viz.VizObjectRef` of the marker.

        The marker is added to the outer group at its local position (not the
        data group), so it is not stretched by the data group's non-uniform
        scale.
        """
        px, py = self._normalize_point(p)
        return self._upsert_point((px, py), name, color, style)

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

    def _upsert_line(self, kind, value, name, c0, c1, color, style):
        store = self._vlines if kind == "v" else self._hlines
        if name is None:
            prefix = "vline" if kind == "v" else "hline"
            index = len(store)
            name = f"{prefix}_{index}"
            while name in store:
                index += 1
                name = f"{prefix}_{index}"
        entry = store.get(name)
        if entry is None:
            render = PointPath()
            kwargs = {} if style is None else {"style": style}
            ref = self._data_group.new(render, color=color, **kwargs)
            entry = {
                "name": name,
                "value": value,
                "c0": None if c0 is None else float(c0),
                "c1": None if c1 is None else float(c1),
                "color": color,
                "ref": ref,
                "render": render,
            }
            store[name] = entry
        else:
            entry["value"] = value
            if c0 is not None:
                entry["c0"] = float(c0)
            if c1 is not None:
                entry["c1"] = float(c1)
        self._sync_line(entry, kind)
        return entry["ref"]

    @staticmethod
    def _normalize_point(value) -> tuple[float, float]:
        """Normalize a data point given as an ``(x, y)`` pair or a ``Point``."""
        if hasattr(value, "x") and hasattr(value, "y"):
            return (float(value.x), float(value.y))
        seq = tuple(value)
        if len(seq) != 2:
            raise ValueError(f"expected an (x, y) pair or a Point, got {value!r}")
        return (float(seq[0]), float(seq[1]))

    def _upsert_segment(self, p0, p1, name, color, style):
        if name is None:
            prefix = "line"
            index = len(self._lines)
            name = f"{prefix}_{index}"
            while name in self._lines:
                index += 1
                name = f"{prefix}_{index}"
        entry = self._lines.get(name)
        if entry is None:
            render = PointPath()
            kwargs = {} if style is None else {"style": style}
            ref = self._data_group.new(render, color=color, **kwargs)
            entry = {
                "name": name,
                "p0": p0,
                "p1": p1,
                "color": color,
                "ref": ref,
                "render": render,
            }
            self._lines[name] = entry
        else:
            entry["p0"] = p0
            entry["p1"] = p1
        self._sync_line(entry, "l")
        return entry["ref"]

    def _upsert_point(self, p, name, color, style):
        if name is None:
            prefix = "point"
            index = len(self._points)
            name = f"{prefix}_{index}"
            while name in self._points:
                index += 1
                name = f"{prefix}_{index}"
        entry = self._points.get(name)
        if entry is None:
            obj = Point(0.0, 0.0, self._plot_z)
            kwargs = {} if style is None else {"style": style}
            ref = self._group.new(obj, color=color, **kwargs)
            entry = {"name": name, "p": p, "color": color, "ref": ref}
            self._points[name] = entry
        else:
            entry["p"] = p
        self._sync_point(entry)
        return entry["ref"]

    def _sync_points(self) -> None:
        for entry in self._points.values():
            self._sync_point(entry)

    def _sync_point(self, entry: dict[str, Any]) -> None:
        lx, ly = self._local_xy(*entry["p"])
        entry["ref"].entity = Point(lx, ly, self._plot_z)

    def _sync_lines(self) -> None:
        for entry in self._vlines.values():
            self._sync_line(entry, "v")
        for entry in self._hlines.values():
            self._sync_line(entry, "h")
        for entry in self._lines.values():
            self._sync_line(entry, "l")

    def _sync_line(self, entry: dict[str, Any], kind: str) -> None:
        color = entry["color"]
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
        render = entry["render"]
        render.clear()
        render.add(p0, color=color)
        render.add(p1, color=color)
        entry["ref"].entity = render

    # ── Mutators (rebuild / re-frame in place) ────────────────

    @property
    def xlim(self) -> tuple[float, float]:
        return self._xlim

    @xlim.setter
    def xlim(self, value) -> None:
        self._xlim = _as_range(value)
        self._rebuild()
        self._apply_camera()

    @property
    def ylim(self) -> tuple[float, float]:
        return self._ylim

    @ylim.setter
    def ylim(self, value) -> None:
        self._ylim = _as_range(value)
        self._rebuild()
        self._apply_camera()

    @property
    def xscale(self) -> Scale:
        return self._xscale

    @xscale.setter
    def xscale(self, value) -> None:
        self._xscale = make_scale(value, self._base)
        self._rebuild()
        self._apply_camera()

    @property
    def yscale(self) -> Scale:
        return self._yscale

    @yscale.setter
    def yscale(self, value) -> None:
        self._yscale = make_scale(value, self._base)
        self._rebuild()
        self._apply_camera()

    @property
    def size(self) -> tuple[float | None, float | None]:
        return self._size

    @size.setter
    def size(self, value) -> None:
        self._size = _as_size(value)
        self._size_given = value is not None
        self._rebuild()
        self._recompute_camera_ownership()
        self._apply_camera()

    @property
    def align(self) -> tuple[float, float]:
        return self._align

    @align.setter
    def align(self, value) -> None:
        self._align = _as_align(value)
        self._apply_transform()

    @property
    def axis_origin(self) -> tuple[float | None, float | None]:
        return self._axis_origin

    @axis_origin.setter
    def axis_origin(self, value) -> None:
        self._axis_origin = _as_axis_origin(value)
        self._build()

    @property
    def base(self) -> float:
        return self._base

    @base.setter
    def base(self, value) -> None:
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
    def position(self, value) -> None:
        self._position = _as_vec3(value)
        self._apply_transform()
        self._apply_camera()

    @property
    def normal(self) -> tuple[float, float, float]:
        return self._normal

    @normal.setter
    def normal(self, value) -> None:
        self._normal = _as_vec3(value)
        self._apply_transform()
        self._apply_camera()

    @property
    def up(self) -> tuple[float, float, float]:
        return self._up

    @up.setter
    def up(self, value) -> None:
        self._up = _as_vec3(value)
        self._apply_transform()
        self._apply_camera()
