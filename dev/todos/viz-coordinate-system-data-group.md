# CoordinateSystem — inner data group (group-transform based data → plane mapping)

**Created:** 2026-08-25 | **Status:** Planned

## Goal

Extend `CoordinateSystem` (`py/pytanga/viz/_coordinate_system.py`) with a second,
**inner** `VizGroup` that is a child of the existing CS group. This inner group
carries only a translation + non-uniform scale that performs the **affine** part
of the data → plot-plane mapping, so that:

1. For **linear** axes, a `PointPath` can be added as a child of this inner group
   with **raw data coordinates**; the frontend group transform then places the
   points correctly. Python-side scaling is reduced to the nonlinear part (the
   `log` in `Scale.to_world`), which is only needed for log axes.
2. The inner group is exposed publicly, together with `vline`/`hline` helpers
   (create + update by an optional `name`, for animating marker lines), so user
   programs can draw their own annotations in data coordinates.

## Background / analysis

### Current mechanism

- `CoordinateSystem.__init__` creates **one** `VizGroup` via
  `self._handle.add_group(group_name)` and stores it in `self._group`.
- `_build()` computes, in the group's **local** frame (centred, `size_x`×`size_y`):
  `raw_xlo` / `raw_span_x` / `raw_ylo` / `raw_span_y` from `scale.to_world(lim)`,
  then builds the grid, the two `Axis` objects, and the `Plane` as direct children
  (`_upsert` → `self._group.new(...)`).
- Data → local mapping lives in `_local_xy()`:
  `nx = (to_world(x) − raw_xlo) / raw_span_x`, then `lx = (nx − 0.5) · size_x`
  (same for y).
- `plot()` and `add_plot()` / `_sync_plot()` build a `PointPath` whose points are
  **already scaled into local-frame coordinates** `(lx, ly, plot_z)` and add it as
  a direct child of `self._group`.

### Why an inner group works (key finding)

The frontend **already** supports nested groups with transforms, so **no JS
changes are needed**:

- `templates/scene-builder.js::buildSceneObject` parents any node under
  `parent_id` (via the registry) and applies `position`/`rotation`/`scale` with
  `applyTransformToObject`.
- `templates/renderers/group.js::createVizGroup` renders a `VizGroup` as an empty
  `THREE.Group`.
- `Scene._dfs_preorder` (`py/pytanga/viz/scene.py`) emits parents before children,
  so the inner group is registered before its point-path children.

Three.js composes parent → child transforms, so a point added under the inner
group is transformed by `CS_group @ inner_group @ point` — exactly the desired
behaviour.

### The inner-group transform

The affine data → local mapping is:

```
wx = xscale.to_world(x)              # identity for linear, log_b(x) for log
sx = size_x / raw_span_x             # raw_span_x = to_world(xhi) - to_world(xlo)
tx = -size_x/2 - sx * raw_xlo
```

so that `lx = sx · wx + tx` (and the same for y). The inner group therefore gets:

```
position = (tx, ty, plot_z)
rotation = (0, 0, 0)
scale    = (sx, sy, 1.0)
```

and points are added at `(wx, wy, 0)`; the z-translation supplies `plot_z`. For a
linear axis `to_world` is the identity, so raw data coordinates can be used
directly; for a log axis the `log` is still applied in Python (a TRS group cannot
express the nonlinearity).

### Degenerate range

Today `_norm()` returns `0.5` when `raw_span == 0` (centres the single value).
To preserve that, when `raw_span_x == 0` use `sx = 1.0`, `tx = -raw_xlo` (which
maps `wx == raw_xlo` to `0`), and the same for y.

## Design decisions

1. **Two frames, one group each.** The existing `_group` remains the "plot plane"
   frame (grid/axes/plane stay its direct children, built in centred local
   coordinates). A new **`data_group`** child of `_group` is the "data" frame; it
   is used only for data-space drawing (plots + user annotations).
2. **Affine part moves into the group; nonlinear part stays in Python.** The
   inner group handles translate + scale; `Scale.to_world` (the `log`) remains
   Python-side and is only exercised by log axes. `plot()` / `add_plot()` store
   scale-world coordinates `(to_world(x), to_world(y), 0)` in the child path.
3. **Public `data_group` property** (a `VizObjectRef`) exposes the inner group for
   external annotation drawing. Default child group name: `f"{group_name}_data"`.
   Named `vline`/`hline` helpers build on it (create-and-update by an optional
   `name`), re-synced when lims/scales/size change.
4. **Backward-compatible helpers.** `to_local()`, `to_world()`, and `transform()`
   keep their current semantics (local/world coordinates via `_local_xy` and
   `self._group.world_matrix`); they do not route through the inner group.
5. **Degenerate spans** are handled as described above instead of dividing by zero.

## Analysis: should the axes and grid also live in the data frame?

Moving the grid, axes, and plane into `data_group` as well would mean their
geometry is specified in scale-world (data) coordinates and placed by the same
affine group transform, instead of the current explicit local-frame offsets.

**Advantages**

- **One affine transform, one source of truth.** `_norm` / `_axis_ticks` /
  `_local_xy` currently re-derive the same scale+translate math per child; in the
  data frame the group does it once, and grid line positions / axis endpoints /
  tick offsets are simply `to_world(value)`.
- **Symmetric linear/log handling.** Both become "map data → scale-world, let the
  group place it"; only `to_world` differs.
- **Conceptual clarity.** The CS becomes "outer placement group + inner data
  frame", with everything (plane, grid, axes, plots, annotations) in one frame.

**Disadvantages**

- **Non-uniform scale skews derived directions.** The axis renderer computes
  `perp`/`binormal` from `start`/`end` and applies `LabelStyle.offset_local` along
  them; those offsets are world-unit and would be stretched differently per axis
  (the default axis styles use pixel `offset_2d`, so the default appearance is
  unaffected, but `offset_local` users would see skewed label placement).
- **Z-layering bookkeeping.** With a single shared transform, `plot_z` can no
  longer be baked into the group's z-translate; each child must carry its own z
  (plane/grid/axes/plots), which is more fiddly than today's per-child local z.
- **Any fixed-size geometry breaks.** Future tick marks, arrowheads, or markers in
  the data frame would be stretched by `sx ≠ sy`; the current design keeps such
  geometry in the orthonormal local frame.
- **Refactor risk for little functional gain.** The explicit-placement approach is
  already working and tested; the move is largely cosmetic and would touch
  grid/axes/plane serialization semantics.

**Recommendation.** Keep the plane, grid, and axes as direct children of the outer
`_group` (current behaviour), and reserve `data_group` for data-space drawing
(plots + `vline`/`hline` + user annotations). Revisit moving the grid/axes into
the data frame only if `offset_local`/fixed-size ticks are not a concern and the
code-symmetry benefit is worth the refactor.

## Changes

### Step 1 — Create and maintain the inner group

**File:** `py/pytanga/viz/_coordinate_system.py`

- [x] In `__init__`, immediately after creating `self._group`, add:
      `self._data_group = self._group.add_group(f"{group_name}_data")`.
- [x] Add a `_apply_data_transform()` method that computes `sx/tx` and `sy/ty`
      from `self._size_x/_size_y`, `self._raw_xlo/_raw_span_x`,
      `self._raw_ylo/_raw_span_y`, and `self._plot_z`, then calls
      `self._data_group.set_transform(position=(tx, ty, self._plot_z),
      rotation=(0, 0, 0), scale=(sx, sy, 1.0))`.
      - Degenerate span guard: `sx = 1.0, tx = -raw_xlo` (and same for y) when the
        raw span is `0`.
- [x] Call `_apply_data_transform()` at the end of `_build()` (after
      `self._plot_z` is set), so every `_rebuild()` (lim/scale/size/axis_origin
      change) re-applies it.

### Step 2 — Repoint plotting onto the inner group

**File:** `py/pytanga/viz/_coordinate_system.py`

- [ ] Add a `_data_xy(x, y)` helper returning
      `(self._xscale.to_world(float(x)), self._yscale.to_world(float(y)))`.
- [ ] Update `plot()`:
      - build the `PointPath` with `(*self._data_xy(x, y), 0.0)` per point,
      - return `self._data_group.new(path, color=color, **kwargs)`.
- [ ] Update `_sync_plot()` (used by `add_plot`/`update_plots`):
      - write `(*self._data_xy(x, y), 0.0)` into the render path,
      - keep `entry["ref"].entity = render` (the ref already points at the
        `_data_group` child created in `add_plot`).
- [ ] Update `add_plot()` to create its render path via
      `self._data_group.new(render, color=color, **kwargs)` instead of
      `self._group.new(...)`.

### Step 3 — Public API

**File:** `py/pytanga/viz/_coordinate_system.py`

- [ ] Add a read-only `data_group` property returning `self._data_group`, with a
      docstring explaining children live in data coordinates (linear) /
      log-mapped coordinates (log) and inherit the auto placement.
- [ ] (Optional) Add a `to_data(x, y)` helper returning `self._data_xy(x, y)` so
      users can pre-map a log-axis value without drawing through the group.
- [ ] Keep `to_local()` / `to_world()` / `transform()` unchanged.

### Step 4 — vline / hline annotation helpers

**File:** `py/pytanga/viz/_coordinate_system.py`

- [ ] Store named line specs: `self._vlines: dict[str, dict]` and
      `self._hlines: dict[str, dict]` (each entry: name, fixed value, optional
      span, color, style, and the `VizObjectRef` of its `PointPath`).
- [ ] Add `vline(x, *, name=None, y0=None, y1=None, color=None, style=None)` and
      `hline(y, *, name=None, x0=None, x1=None, color=None, style=None)`:
      - `name=None` → always create a new line (return its `VizObjectRef`).
      - `name` given → create if missing, otherwise update the existing line in
        place (`ref.entity = ...`) so animations can move it without re-adding.
      - `y0/y1` (resp. `x0/x1`) default to the current `ylim` (resp. `xlim`).
      - Endpoints are computed via `_data_xy` so log axes map correctly.
- [ ] Add `_sync_lines()` that rebuilds every stored line from its spec (using
      `_data_xy` and the current limits) and assigns `ref.entity`; call it at the
      end of `_build()` so lines track `xlim`/`ylim`/scale/size changes.
- [ ] Add `remove_vline(name)` and `remove_hline(name)` that unregister a named
      line and remove its node from the scene.

### Step 5 — Tests

**Files:** `py/tests/viz/test_coordinate_system.py`

- [ ] Update `TestCoordinateSystemPlots::test_add_plot_and_update`: the render
      path now holds **scale-world** coordinates, so the final assertion becomes
      `render.points[-1][0] == pytest.approx(9.0)` (the auto-x data value) instead
      of the current local `1.0`.
- [ ] Add tests:
      - `cs.data_group` is a `VizObjectRef` and a child of `cs.group`
        (`cs.data_group.parent.id == cs.group.id`).
      - For linear axes, `cs.plot([1, 2], [3, 4])` produces render points equal to
        the raw data `(1,3)`, `(2,4)` and the group transform maps them back to the
        same local coords `cs.transform(...)` returns.
      - `data_group.transform` equals the affine formula (`position`/`scale`) for a
        known `xlim/ylim/size` (and for a log axis, the `log`-mapped limits).
      - A point-path added directly via `cs.data_group.new(...)` (annotation
        pattern) has `parent_id == cs.data_group.id`.
      - Degenerate range (`xlim == (5, 5)`) yields `scale_x == 1` and a transform
        that maps the value to local `0`.
      - `vline`/`hline`: create-and-update by name reuses the same `VizObjectRef`
        and moves the line; unnamed calls create new refs; the default span tracks
        `ylim`/`xlim`; endpoints are log-mapped for log axes.
- [ ] Ensure existing tests `test_transform_and_plot`, `test_2d_size_up_rotates_plane`,
      `test_to_world_applies_group_transform`, `test_align_*`,
      `test_position_accepts_point_and_direction`, and the scale tests stay green
      (they exercise `transform`/`to_world`/group transform, which are unchanged).

### Step 6 — Documentation

**Files:** `docs/py/viz/scene-objects/coordinate-system.md`,
`docs/py/viz/scene-objects/coordinate-system.ipynb` (as applicable)

- [ ] Document `data_group` and the "draw your own annotations" pattern
      (e.g. `cs.data_group.new(...)` for a line at a fixed `x` or `y`).
- [ ] Document `vline`/`hline` (create + update by name, for animating marker
      lines) alongside the `data_group` annotation pattern.
- [ ] Clarify the linear vs. log distinction: linear axes can draw directly in data
      coordinates; log axes are `log`-mapped by `plot()` / `add_plot()` and by the
      user via `to_data()` when drawing directly into `data_group`.
- [ ] Note the caveat that `data_group` applies a non-uniform scale, so it is
      intended for paths/lines; shaded markers should be placed via `to_world()`.

### Step 7 — Examples

**Files:** `py/examples/viz/demo_cs_annotations.py` (new)

- [ ] Add a runnable example demonstrating the new features:
      - a `plot()` in a 2D coordinate system,
      - fixed `vline`/`hline` annotations in data coordinates,
      - a named, animated `vline` (create once, update each frame via
        `cs.vline(x=..., name="cursor")`), and
      - drawing directly into `cs.data_group`.
- [ ] Match the existing example style (header docstring with a
      `uv run python ...` run line, `viz.show()` / `viz.animate(...)` loop).

### Step 8 — Changelog

**File:** branch changelog per `dev/workflows/changelog.md`

- [ ] Add New Features bullets for the inner data group, the `data_group`
      exposure, and the `vline`/`hline` helpers (append to the current branch
      changelog; the index update happens at PR time per the workflow).

## Verification

- [ ] `uv run pytest py/tests/viz -q` green (updated + new coordinate-system tests).
- [ ] `uv run pytest -q` full suite green.
- [ ] `uv run ruff check` and `uv run ruff format --check` on the touched files.
- [ ] `node --check` on the viz templates is **not** needed (no JS changes), but a
      headless smoke test should confirm `full_state()` emits the CS group → inner
      group → point-path hierarchy in DFS pre-order with correct `parent_id`s.
- [ ] Manual browser check (pending): `demo_log_plot.py` and `demo_plot_3d.py`
      still render identically; a user-added annotation under `data_group`
      (e.g. a vertical line at a data `x` value) lands on the correct plane
      position, including on a tilted 3D plane.

## Notes / edge cases

- **Non-uniform group scale.** Ideal for `PointPath`/`Line`; `Line2` fat-line width
  is screen-space so it is not distorted, but shaded entities (spheres, etc.)
  added to `data_group` would be stretched — document and steer users to
  `to_world()` for those.
- **`plot()` is one-shot.** Changing `xscale`/`yscale` after a `plot()` re-applies
  the data-group transform but does **not** re-map already-plotted points (same
  limitation as today; only `add_plot`/`update_plots` re-syncs). No regression.
- **Log axes still need `to_world`.** Only the affine part moves into the group;
  `LogScale.to_world` (and its `value <= 0` validation) remains Python-side.
- **`_plot_z` moves into the inner group.** Point children are stored at `z = 0`;
  the inner group's `position[2] = plot_z` preserves the existing grid/axes/plot
  layering.
- **vline/hline re-sync.** Named lines are rebuilt in `_build`, so they track
  `xlim`/`ylim`/scale/size changes; unnamed lines are one-shot and not re-synced.

## Non-goals / follow-ups

- Moving the grid/axes/plane into the data frame — see the analysis above; they
  stay direct children of `_group` in the centred local frame for now.
- Any frontend (JS) change.



