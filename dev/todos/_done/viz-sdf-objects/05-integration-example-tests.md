# Phase 5 — Example + tests + browser smoke + regression

## Goal

Prove the feature end-to-end: a runnable example mixing standard meshes with
SDF-styled objects, Python regression tests, a manual browser smoke check, and
a full-suite regression run.

## Files

- New: `py/examples/viz/demo_sdf_objects.py` — standard viewer with a mix of
  normal and `SdfStyle` objects.
- Modify: `py/tests/viz/sdf/test_standard_serializer_sdf.py` (extend), any
  integration test module under `py/tests/viz/`.

## Steps

- [x] **5.1 — Example**
  - `Visualizer()` with, e.g., a normal `Sphere`/`Plane` (mesh) plus an
    SDF-styled `Sphere` and an SDF-styled `Composed` (a bead with a hole) via
    `style=SdfStyle(...)`. Include an animated SDF object (a tween) to exercise
    the transform-update path, and a label + interaction on an SDF object.
  - `uv run python py/examples/viz/demo_sdf_objects.py` opens the standard
    `viewer.html`.

- [x] **5.2 — Regression tests**
  - SDF-styled object serializes to `kind:"sdf"` with `tree`/`bound`/`transform`.
  - Non-SDF scene unchanged (existing `py/tests/viz/` suite).
  - `SdfVisualizer` unchanged (existing `py/tests/viz/sdf/` suite).

- [ ] **5.3 — Manual browser smoke** (no headless browser in the repo; run
  `uv run python py/examples/viz/demo_sdf_objects.py` to verify visually)
  - SDF object renders smooth, is correctly occluded by / occludes a mesh and
    another SDF object, orbits with the camera, and the animated SDF object
    moves without shader recompile (no console spam).
  - WebGL1 fallback: SDF objects render as their mesh equivalent with one warning.

- [x] **5.4 — Validate**
  - `uv run pytest py/tests/viz/ -q` (full suite green).
  - `node --input-type=module --check` on all touched JS.

## Validation

`uv run pytest py/tests/viz/ -q` + `node --input-type=module --check` on touched
JS + the `demo_sdf_objects.py` manual browser check.

## Notes

- This is the "vertical slice complete" gate: after this phase the feature is
  usable and documented; Phase 6 (shadows) is optional.
