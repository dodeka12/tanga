# Phase 7 — Example + end-to-end/regression tests

## Goal

Ship a runnable example and add regression coverage proving the overlay frame and
underlay grid work end-to-end in the live viewer and standalone HTML export.

## Files

- New: `py/examples/viz/camera/axes_overlay_2d.py`
- New: `py/tests/viz/test_export_axes_overlay.py`

## Steps

- [x] **7.1 — example `axes_overlay_2d.py`**
  - Follow `dev/workflows/example-docs.md`: module docstring with description +
    `Keywords:` header (e.g. `Keywords: camera, 2D, CoordinateSystem, overlay,
    underlay, axes, grid`).
  - Build a `Visualizer(space_dim=2)` + `CoordinateSystem(viz,
    display_mode="overlay", xlim=..., ylim=...)` with a plotted `PointPath` and a
    `vline`/`hline` so pan/zoom is meaningful; `viz.show(); viz.wait()`.
  - Add an annotation explaining "scroll to zoom / right-drag to pan".

- [x] **7.2 — export regression test `test_export_axes_overlay.py`**
  - Build a 2D overlay coordinate system and export via `display_snapshot` /
    `export_snapshot`; assert the exported HTML includes the `axes_overlay` and
    `grid_underlay` specs and the `updateCoordinateOverlays` / `AxesOverlay` /
    `GridUnderlay` wiring (mirror existing `test_export_*.py` assertions).

- [x] **7.3 — full validation**
  - Run the full viz suite + build check.

## Validation

`uv run pytest py/tests/viz -q && uv run python tools/build-viewer-js.py --check`

## Notes

- The example doubles as the manual browser smoke for the overlay/underlay path.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
