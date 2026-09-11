# Coordinate System & Logarithmic Plotting

**Created:** 2026-08-24 | **Status:** Planned

## Goal

Add a `CoordinateSystem` helper that builds a complete 2D/3D plotting coordinate
system — background plane, grid, axes (with value labels), and plotted point
paths — inside a single `VizGroup`, and support **logarithmic scales for any
base** while keeping the underlying world coordinates linear.

The class is *not* a scene object itself; it owns the group and the
`VizObjectRef`s of the objects it creates, and updates them in place when the
axis ranges change.

## Background (current state)

- `Axis` (`_scene_objects.py`) renders a line + value labels, but labels are
  placed **uniformly** on the frontend (`renderers/axis.js`:
  `value = valueStart + i * majorInterval * valueStep` at offset `i * majorInterval`).
- `Grid` (`renderers/grid.js`) draws lines at **uniform** `interval_u`/`interval_v`
  steps.
- `Axes2D`/`Axes3D` expand into `Axis` halves split at world-origin 0 — awkward for
  log axes whose world range straddles 0.
- The scene graph already provides the building blocks we need:
  - `handle.add_group(name)` → `VizObjectRef` wrapping a `VizGroup`.
  - `group_ref.new(obj, style=...)` → adds a child, returns its `VizObjectRef`.
  - `ref.entity = new_obj` → `VizSceneObject.set_entity`, re-serializes and marks
    `content` (or `full`) dirty — the in-place update path.
  - `VizObjectRef.set_transform(position=…, rotation=euler, …)` +
    `Transform.set_matrix` (decomposes 4×4 → TRS via `_T.to_trs`).
- Camera:
  - `View2DConfig(xmin/xmax/ymin/ymax, border_world, border_px, uniform)`.
    `border_px` insets the content area by N px on all sides (frontend
    `view_mode.js`), giving a pixel margin so axis labels are not clipped.
  - `View3dConfig(point, normal, extent_u, extent_v, fov, up)` frames a virtual
    plane via `get_camera_view3d`.
  - `set_camera(...)` exists on both `Visualizer` and `VizSceneHandle`.
- `Plane` (`geometry.entities.Plane`) supports `span_u`/`span_v` and
  `from_center_and_half_span(...)`; `renderers/plane.js` orients it from `normal`.
  `PlaneStyle` controls color/opacity.

## Design decisions

1. **Log spacing is explicit placement, not frontend math.** Compute tick
   positions + labels in Python and pass them to `Axis`/`Grid` as explicit
   position lists. The world stays linear; data → world conversion is done in
   Python (`to_world`/`transform`). Same code path for live viewer and HTML export.
2. **Extend (not replace) `Axis` and `Grid`** with optional explicit-placement
   fields that override the uniform loops when present. Fully backward compatible.
3. **`CoordinateSystem` uses two full-range `Axis` objects** (one per direction)
   rather than `Axes2D`, so a single axis can span a world range that crosses 0
   (typical for log) and each direction can be styled independently. Grid + plane
   are separate children.
4. **Everything lives in one `VizGroup`** built in the group's *local* 2D frame
   (centered at the plot center). In 3D the group's `transform` places/orients
   the whole system (plane + grid + axes + plots) with arbitrary position/rotation.
5. **2D default span + camera:** axes span the camera's world rect; if no camera
   is configured, `CoordinateSystem` creates and sets a `View2DConfig` with
   `border_px` so labels stay visible.
6. **3D placement:** `position` = world center of the plot plane, `normal` = plane
   normal (plot +z), `up` = reference fixing in-plane x. Plane size = the
   coordinate system's world span (derived from `xlim`/`ylim` + scales).

## Changes

### Step 1 — Explicit placement on `Axis` and `Grid`

**Files:** `py/pytanga/viz/_scene_objects.py`, `py/pytanga/viz/serializer.py`,
`py/pytanga/viz/templates/renderers/axis.js`,
`py/pytanga/viz/templates/renderers/grid.js`

- [x] `_scene_objects.py`
  - `Axis`: add `ticks: list[tuple[float, str]] | None = None`
    (`(offset, label)` along the axis from `start`, overriding the
    `major_interval`/`value_start`/`value_step` label loop when set).
  - `Grid`: add `line_positions_u: list[float] | None = None` and
    `line_positions_v: list[float] | None = None` (absolute offsets from
    `origin` along `dir_u`/`dir_v`, overriding the interval loops when set).
  - Update docstrings with the new fields.
- [x] `serializer.py`
  - `_serialize_axis`: emit `"ticks": [[pos, label], ...]` only when set.
  - `_serialize_grid`: emit `"line_positions_u"` / `"line_positions_v"` only when set.
- [x] `renderers/axis.js` (`addAxis`): if `axis.ticks` is present, draw value
  labels at each explicit position (reusing the existing `makeLabel` /
  perpendicular / offset logic) instead of the `majorInterval` loop.
- [x] `renderers/grid.js` (`createGrid`): if `ent.line_positions_u` /
  `ent.line_positions_v` are present, draw lines at those offsets (clamped to the
  range) instead of the `interval_u`/`interval_v` loops.

### Step 2 — Scale & tick computation module

**File:** `py/pytanga/viz/_scale.py` (new)

- [x] `class Scale` (protocol): `to_world(v) -> float`, `from_world(w) -> float`,
  `ticks(lo, hi) -> list[tuple[float, str]]` (data value + label, ascending),
  `is_log: bool`.
- [x] `class LinearScale`: identity mapping; `ticks` uses a "nice" 1/2/5 × 10^k
  algorithm targeting ~5–8 ticks.
- [x] `class LogScale(base)`: `to_world(v) = log(v, base)`; `ticks` returns integer
  powers of `base` within `[lo, hi]` (e.g. 0.1, 1, 10, 100). Validate `lo > 0`.
- [x] `make_scale(kind_or_scale, base=10.0)` accepting `"linear" | "log" | Scale`.
- [x] Label formatting uses a single `value_format` string (default `".4g"`),
  applied in the `CoordinateSystem` (not in `Scale`).

### Step 3 — `CoordinateSystem` helper class

**Files:** `py/pytanga/viz/_coordinate_system.py` (new),
`py/pytanga/viz/templates/renderers/plane.js`

- [x] Constructor accepts `target` = `Visualizer` or `VizSceneHandle` (normalize to
  a handle; read `space_dim` from `handle.scene.config.space_dim`), plus:
  - data: `xlim`, `ylim` (None → auto), `xscale`, `yscale` (`"linear"|"log"|Scale`),
    `base`, `value_format`, `labels=("x","y")`
  - visuals: `grid=True`, `axes=True`, `plane=None` (None → True in 3D, False in 2D)
  - 2D camera: `camera="auto"` (`"auto"|True|False`), `border_px=40.0`, `border_world=0.0`
  - 3D placement: `position=(0,0,0)`, `normal=(0,0,1)`, `up=(0,1,0)`
  - styles: `x_style=AxisStyle()`, `y_style=AxisStyle()`, `grid_style=GridStyle()`,
    `plane_style=PlaneStyle(opacity=0.3)`, `group_name="coordsys"`
- [x] `__init__` creates the `VizGroup` via `handle.add_group(group_name)` and
  stores `self._group` + the per-child `VizObjectRef`s in `self._refs`.
- [x] `_build()` derives world spans `[wx_lo, wx_hi] × [wy_lo, wy_hi]` from
  `xlim`/`ylim` + scales and per-axis `ticks(...)`, then create-or-updates:
  - grid: `Grid(origin=(min corner), dir_u=(1,0,0), dir_v=(0,1,0),
    range_u=(0, span_x), range_v=(0, span_y), line_positions_u/v)`.
  - two `Axis` objects spanning the full world range, with explicit `ticks` and
    `label`/`value_format`.
  - 3D plane: `Plane(point=(0,0,0), normal=(0,0,1), span_u=(span_x,0,0),
    span_v=(0,span_y,0))`; **`plane.js` extended** to honor `span_u`/`span_v`
    (rectangular quad) instead of the square `extent` fallback.
  - first call creates children via `self._group.new(...)`; later calls update via
    `ref.entity = ...`.
- [x] 2D camera handling: `_apply_camera()` builds a centered `View2DConfig` with
  `border_world`/`border_px`/`uniform=True` and calls `handle.set_camera(...)`
  per the `camera` flag; `xlim/ylim=None` auto-fills from an existing
  `CameraConfig2d` rect (else `(-5, 5)` / `(0.1, 100)` for log).
- [x] 3D placement: compute `N=normalize(normal)`, `U=normalize(cross(up, N))`
  (fallback if degenerate), `V=cross(N, U)`; build the rotation, decompose to
  Euler via `_T.to_trs`, then `self._group.set_transform(position=position,
  rotation=euler)`. 3D camera (if `camera` allows) = `View3dConfig(point=position,
  normal=normal, extent_u=width, extent_v=height)`.
- [x] Data → world helpers: `to_world(x, y)`, `transform(xs, ys) -> list[(x,y,z)]`
  (group-local coords).
- [x] `plot(xs, ys, *, color=None, style=None) -> VizObjectRef`: transform, build a
  `PointPath`, add as a `VizGroup` child.
- [x] Mutators/properties that call `_build()` (and `_apply_camera()` where
  relevant): `xlim`, `ylim`, `xscale`, `yscale`, `base`, `position`, `normal`,
  `up`.

### Step 4 — Public exports

**File:** `py/pytanga/viz/__init__.py`

- [x] Import and add to `__all__`: `CoordinateSystem`, `Scale`, `LinearScale`,
  `LogScale`.

### Step 5 — Tests

**Files:** `py/tests/viz/test_scale.py` (new),
`py/tests/viz/test_coordinate_system.py` (new),
`py/tests/viz/test_scene_session.py`, `py/tests/viz/test_serializer.py`

- [x] `test_scale.py`: linear nice ticks, log power ticks (any base), degenerate
  ranges, `lo <= 0` validation for log, `make_scale` dispatch.
- [x] `test_coordinate_system.py`:
  - 2D: auto span from a `CameraConfig2d`; default camera set with `border_px`;
    `xlim` update updates the stored refs in place (same IDs, changed entities).
  - 3D: group transform from `position`/`normal`/`up`; background plane child
    sized to the world span; `plot`/`transform` produce local-frame points.
  - log axes produce `ticks` on the serialized `Axis`.
- [x] Serialization tests (in `test_scene_session.py`): `Axis(ticks=...)` emits
  `ticks`; default omits it; `Grid(line_positions_* )` emits the fields; default
  omits them.

### Step 6 — Example

**Files:** `py/examples/viz/demo_log_plot.py` (new),
`py/examples/viz/demo_plot_3d.py` (new)

- [x] 2D log-log plot with `CoordinateSystem(viz, xlim=(0.1, 100), ylim=(0.1, 100),
  xscale="log", yscale="log")` + `plot(...)`.
- [x] 3D example with a tilted/offset plane (`position`, `normal`, `up`).

### Step 7 — Documentation

**Files:** `docs/py/viz/scene-objects/plotting.md` (new), `mkdocs.yml`

- [x] Document `CoordinateSystem`, `Scale`/`LinearScale`/`LogScale`, log scales,
  2D auto-camera/`border_px`, 3D plane placement, and `plot`/`transform`.
- [x] Add `plotting.md` to the `scene-objects` nav section in `mkdocs.yml`.

### Step 8 — Changelog

**Files:** `docs/changelog/2026-08-24_feat-multi-view.md` (appended)

- [x] Add a branch changelog per `dev/workflows/changelog.md` (appended a
  "New Features" bullet to the existing `feat/multi-view` branch changelog).
  `docs/changelog/index.md` is updated at PR time (after the hash rename), per
  the workflow.

## Verification

- [x] `uv run pytest py/tests/viz -q` (plus new `test_scale.py` /
  `test_coordinate_system.py`) — 630 passed; full suite `uv run pytest` → 1845 passed.
- [x] `node --check` on `py/pytanga/viz/templates/renderers/axis.js`, `grid.js`,
  and `plane.js`.
- [x] `uv run ruff check` + `ruff format --check` on all files touched by this
  feature (pre-existing repo-wide violations outside these files remain).
- [x] Headless smoke: 2D log plot and 3D tilted-plane plot construct and add the
  expected node kinds (group + grid + axes [+ plane] + point path).
- [ ] Manual browser check (pending): open `demo_log_plot.py` / `demo_plot_3d.py`
  and confirm log-spaced labels are visible (not clipped) and the 3D plot
  renders on a tilted plane; confirm `export_snapshot` matches the live view.

## Notes / edge cases

- Log scale requires `xlim`/`ylim` strictly positive; validate and raise a clear
  `ValueError` otherwise.
- `ticks` takes precedence over `major_interval`/`value_start`/`value_step` on the
  wire, but those fields remain for the existing uniform path.
- The 2D axes are drawn with explicit `ticks` even for linear scales (nice 1/2/5
  values), which is a small, intended improvement over uniform `major_interval`.
- 3D `position` is the plot-plane **center** (local origin), not a corner; the
  plane spans `[wx_lo, wx_hi] × [wy_lo, wy_hi]` around it.
- `CoordinateSystem` must never be registered as a `SceneEntity`/`VizInputType`/
  serializer kind — it is a scene-graph helper only.
