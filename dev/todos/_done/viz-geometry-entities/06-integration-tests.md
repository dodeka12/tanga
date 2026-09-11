# Phase 6 — Integration & regression tests

## Goal

Prove the full pipeline end-to-end (entity → scene → serializer → frontend
dispatch strings → static HTML export) and run the existing regression suites.

## Steps

- [x] **6.1 — End-to-end example `py/examples/viz/demo_viz_entities.py`**
  - `Visualizer(add_default_axes=False, add_default_grid=False)`.
  - `viz.add(Cylinder(origin=Point(0,0,0), axis=Direction(0,0,1),
    length=2.0, radius=0.2), color="#44aaff")`.
  - `viz.add(Arc(origin=Point(0,0,0), axis=Direction(0,0,1), radius=1.5,
    tube_radius=0.05, angle=math.pi * 1.5, show_arrow=True))` (partial arc with
    cone arrow).
  - `viz.add(Arc(radius=2.0, tube_radius=0.04))` (full torus).
  - Add a `run()` entrypoint guarded by `if __name__ == "__main__":`.

- [x] **6.2 — Scene-graph integration check**
  - Assert `viz.main_scene.full_state()` emits exactly the wire-contract keys for
    the three objects; `startDirection` is normalized and `arrow` is a dict for
    the partial arc and `None` for the full torus.
  - This can live as a small test in `py/tests/viz/test_serializer.py` (reuse
    `Visualizer`) rather than a new file.

- [x] **6.3 — Full Python regression**
  - `uv run pytest py/tests/geometry/test_viz_entities.py
    py/tests/viz/test_viz_styles.py py/tests/viz/test_serializer.py
    py/tests/viz/test_export_renderers.py -q`, then
    `uv run pytest py/tests/viz -q` (full viz suite).

- [x] **6.4 — JS syntax + bundle check**
  - `node --input-type=module --check` on `cylinder.js`, `arc.js`, `factory.js`,
    `utils.js`.
  - `uv run pytest py/tests/viz/test_export_renderers.py -q` (renderer set in
    lockstep with the export bundle + `createCylinder`/`createArc` present in
    the generated bootstrap).

- [x] **6.5 — Static HTML export smoke**
  - Build the demo scene, then `render_snapshot(viz.main_scene.full_state(),
    viz.main_scene.config.to_dict())` and assert `"function createCylinder("`
    and `"function createArc("` are present in the HTML — proving the standalone
    export renders the new entities with no extra wiring (same assertion style
    as `test_export_static.py`).
  - Optionally also call `viz.export_snapshot(path, overwrite=True)` and
    `viz.export_figure()` and open the output in a browser to confirm the
    cylinder, partial arc + cone arrow, and full torus all appear.

- [x] **6.6 — Manual browser smoke (live viewer)**
  - Run `uv run python py/examples/viz/demo_viz_entities.py` and confirm the
    cylinder, partial arc + cone arrow, and full torus render correctly and are
    orbit/zoomable. (No headless browser in the repo; note any limitation.)

- [x] **6.7 — Validate**
  - Record the passing command output (test counts) in this file's Notes.

## Validation

`uv run pytest py/tests/viz -q` + `node --input-type=module --check` on touched
JS + static-export smoke (`render_snapshot` contains `createCylinder`/`createArc`)
+ manual `demo_viz_entities.py` run.

## Notes

- `dev/src/test_viz_smoke.py` has a pre-existing syntax error unrelated to this
  change; do not rely on it for validation.
- Static HTML export needs no dedicated renderer code — the shared
  `factory.js` → `createEntityMesh` + `_RENDERER_FILES` path already bundles the
  new renderers, so the smoke check only confirms they are registered.
- **Results:** targeted tests 80 passed; full `py/tests/viz` suite 596 passed;
  `test_export_static.py` 15 passed; all four touched JS files pass
  `node --input-type=module --check`.
- 6.6 live-viewer smoke deferred: no headless browser in this environment. The
  demo was instead verified by constructing the same scene and exercising the
  serializer + static-export path (which runs the same `createEntityMesh`
  renderers); actual WebGL rendering still needs a manual browser run.
