# CoordinateSystem — labels on annotation helpers (and Line-based line drawing)

**Created:** 2026-08-25 | **Status:** Planned

## Goal

Add `label` / `label_style` support to the `CoordinateSystem` annotation helpers
(`vline`, `hline`, `line`, `point`), and draw the line helpers as
:class:`~pytanga.geometry.Line` entities (a straight line segment) instead of a
two-point `PointPath`. Using `Line` gives the helpers line rendering (not a
cylinder) **and** the existing `LabelStyle.along` label alignment for free,
instead of having to add a `PointPath` label anchor.

## Background / analysis

### Current state

- `vline` / `hline` / `line` build a two-point `PointPath` and add it as a child
  of the inner `data_group` (`py/pytanga/viz/_coordinate_system.py`). `point`
  adds a geometry `Point` to the outer group.
- None of these helpers accept `label` / `label_style`; they only forward
  `color` / `style` to `new(...)`.

### The label plumbing already exists

- `Visualizer.add`/`new` (and `VizSceneHandle.add`/`new`, and `VizObjectRef.new`
  via `**kwargs`) already accept `label` and `label_style`
  (`visualizer.py:329-421`).
- `_add_to_scene` (`visualizer.py:579-616`) resolves the label style, computes
  the anchor, and creates a `Label(text=…, position=…, parent_id=eid, style=…)`
  attached to the entity id.
- Because the named create/update path reuses the same `VizObjectRef` (and thus
  the same entity id), a label set at creation **persists** across `name` updates.

So piping labels is purely additive: add the kwargs and forward them to
`new(...)` at creation time. `LabelStyle` is already imported in
`_coordinate_system.py`.

### Why `Line` (not `PointPath`) for the line helpers

- `PointPath` is **not** in the label anchor/frame registries
  (`_label_anchor.py::_ANCHOR_FUNCS`, `_label_frame.py::EntityLike`), so a label
  on a `PointPath` falls back to the data-frame origin `(0,0,0)` — not on the
  line.
- `Line` **is** handled: `_label_anchor.py::_anchor_line` places the label at
  `direction · u · length` with `u = LabelStyle.along` (default `0.5` = midpoint).
- `Line` renders as a screen-space fat line by default (`line.js::createLine` →
  `makeFatLine`, `thickness` in px from `LineStyle`); only `CylinderLineStyle`
  renders a cylinder.
- `Line.from_points(start, end)` (`geometry/entities/line.py:54`) creates exactly
  the segment we need (`length = |end − start|`).

## Design decisions

1. **Line helpers draw a `Line`.** `vline` / `hline` / `line` emit
   `Line.from_points(Point(wx0, wy0, 0), Point(wx1, wy1, 0))` in the data group.
   `plot()` / `add_plot()` stay `PointPath` (polylines). `point` stays a
   geometry `Point`.
2. **`style` becomes `LineStyle`** for the line helpers (px `thickness`), instead
   of `PointPathStyle`.
3. **Labels are creation-time-only** (like `color`/`style` today). `name`-updates
   move the geometry; the label text/style persist (same entity id). Making label
   text/style updatable on later calls is out of scope.
4. **`along` for free.** Line labels default to the midpoint; users can pass
   `label_style=LabelStyle(along=0.0/0.5/1.0, …)` to align along the segment.
5. **Non-uniform scale caveat.** The fat line is unaffected (screen-space width)
   and `offset_2d` is pixel-based; only `offset_local` (world-unit perpendicular)
   skews under an explicit `size` with a different aspect ratio. Accepted and
   documented.

## Changes

### Step 1 — Switch line helpers to `Line`

**File:** `py/pytanga/viz/_coordinate_system.py`

- [x] Import `Line` from `pytanga.geometry.entities`.
- [x] Change `_sync_line` to build
      `Line.from_points(Point(wx0, wy0, 0.0), Point(wx1, wy1, 0.0))` (instead of
      a two-point `PointPath`).
- [x] Change `_upsert_line` / `_upsert_segment` to create the entity via
      `new(Line(...), ...)` and store it in the entry.
- [x] Keep the `name` create/update flow unchanged (update value/coords, then
      `ref.entity = line`).

### Step 2 — Pipe `label` / `label_style`

**File:** `py/pytanga/viz/_coordinate_system.py`

- [x] Add `label: str | None = None` and `label_style: LabelStyle | None = None`
      to `vline`, `hline`, `line`, `point`.
- [x] Thread them through `_upsert_line` / `_upsert_segment` / `_upsert_point`;
      store in the entry and forward to `new(...)` at creation only.

### Step 3 — Tests

**Files:** `py/tests/viz/test_coordinate_system.py`

- [x] Update vline/hline/line tests: `ref.entity` is now a `Line`; assert
      `origin`/`direction`/`length` (or `.start`/`.end`) instead of `.points`.
- [x] Add label tests: each helper accepts `label`/`label_style`; the label is
      attached to the entity; `label_style` (e.g. `along`/`offset_2d`) is
      respected; the label persists across a `name` update; `point` label anchors
      at the point.
- [x] Keep `test_point_*`, `test_plot_*`, `test_add_plot_*`, and scale tests green.

### Step 4 — Documentation

**File:** `docs/py/viz/scene-objects/coordinate-system.md`

- [x] Document `label`/`label_style` for the annotation helpers, and the
      `along`-based alignment for the line helpers (with `LineStyle`).
- [x] Update any snippets that pass `PointPathStyle` to the line helpers to use
      `LineStyle`.

### Step 5 — Examples

**Files:** `py/examples/viz/demo_cs_annotations.py` (and possibly
`demo_log_plot.py` / `demo_plot_3d.py`)

- [x] Add labels to a couple of annotations in the example(s) to demonstrate the
      feature (e.g. a labelled `vline`/`point`).

### Step 6 — Changelog

**File:** branch changelog per `dev/workflows/changelog.md`

- [ ] Add a New Features bullet for labels on the CS annotation helpers (and the
      `Line`-based line drawing).

## Verification

- [ ] `uv run pytest py/tests/viz -q` and `uv run pytest -q` green.
- [ ] `uv run ruff check` / `uv run ruff format --check` on touched files.
- [ ] Manual browser check: labelled vline/hline/line/point render the label at
      the expected position (midpoint / `along` for lines, at the point for
      `point`); moving a named line keeps its label.

## Notes / edge cases

- **Zero-length line** (`vline` with `y0 == y1`, etc.): `Line.from_points` yields
  a zero direction; add a small guard (skip or clamp) if desired.
- **`PointPath` helpers unchanged**: `plot`/`add_plot` remain `PointPath` and are
  out of scope for labels.
- **`LineStyle` thickness is screen-space px**, so the lines match `PointPath`'s
  fat-line look.
- **Label persistence**: the label is a separate overlay node keyed to the entity
  id, so it survives the `name` update path without re-adding.
- **Line label anchor fix.** `_label_anchor.py::_anchor_line` previously omitted
  the line's origin, so labels on lines with a non-zero origin were mis-placed.
  It now adds `line.origin`, which is required for the CS line helpers (which
  create lines at non-zero data origins). The existing
  `test_finite_line_label_at_midpoint` was updated to the corrected midpoint.

## Non-goals / follow-ups

- Label support on `plot`/`add_plot` (`PointPath` anchor would be needed first).
- Updating label text/style via a later `name` call (creation-time-only for now).
- A `PointPath` label anchor / frame.

