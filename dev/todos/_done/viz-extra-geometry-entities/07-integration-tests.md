# Phase 7 — Integration tests + regression

## Goal

End-to-end coverage proving the new entities render in both viewers, and a full
regression pass.

## Files

- New: `py/examples/viz/entities/extra_entities.py` (or extend
  `py/examples/viz/entities/viz_entities.py`)
- Modify: `py/tests/viz/test_viz_styles.py`, `py/tests/viz/test_serializer.py`
  (as needed for any remaining assertions)
- New/Modify: `py/tests/viz/sdf/` as needed

## Steps

- [x] **7.1 — Example script**
  - A runnable `py/examples/viz/entities/extra_entities.py` showing a `Disk`,
    `PartialDisk`, `Box`, `Ellipsoid`, `Ellipse`, and `regular_polygon(6)` in
    one 3D scene (and note the `Visualizer(space_dim=2)` 2D usage).
  - Optionally a companion SDF example showing the same entities via
    `SdfObject(..., style=Sdf*Style(...))`.

- [x] **7.2 — Full Python regression**
  - `uv run pytest py/tests/geometry py/tests/viz -q`.

- [x] **7.3 — SDF regression**
  - `uv run pytest py/tests/viz/sdf -q`.

- [x] **7.4 — JS syntax + export bundle**
  - `node --input-type=module --check` on every touched JS file.
  - `uv run pytest py/tests/viz/test_export_renderers.py -q` — confirm the six
    new renderers appear in the generated bootstrap.
  - Static-export assertion: the generated `render_snapshot()` output contains
    `function createDisk(` / `function createBox(` / `function createEllipsoid(` /
    `function createRegularPolygon(` (mirrors the `test_export_static.py`
    pattern).

- [x] **7.5 — Manual browser smoke**
  - Run the example scripts and confirm the shapes render correctly in the live
    viewer (3D) and the 2D viewer (`space_dim=2`), and that SDF-styled versions
    ray-march correctly.

- [x] **7.6 — Validate**
  - `uv run pytest py/tests/geometry py/tests/viz py/tests/viz/sdf -q`.

## Validation

`uv run pytest py/tests/geometry py/tests/viz py/tests/viz/sdf -q`

## Notes

- No DOM test harness exists in the repo; browser behavior is validated by the
  manual viewer + export-bundle assertions.
- Keep the example scripts self-contained and runnable with
  `uv run python py/examples/viz/entities/extra_entities.py`.
