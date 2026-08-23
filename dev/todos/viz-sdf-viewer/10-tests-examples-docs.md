# Phase 10 — Tests, examples, docs, changelog, PR

**Status:** Planned

## Goal

Lock in the SDF viewer with tests, user-facing examples, documentation, a
changelog entry, and a pull request following the repository workflows.

## Steps

- [ ] Full-suite run:
  - [ ] `uv run pytest py/tests/viz/sdf` — runs the accumulated per-phase
        tests (each already run in its phase); this is the integration
        regression pass, not the first time the tests execute.
- [ ] Smoke test (Python):
  - [ ] `dev/src/test_viz_sdf.py` driving `SdfVisualizer` headless where
        feasible (server boot, config message, basic scene serialization).
- [ ] Examples. Already delivered (not re-done here): `demo_sdf_entities.py`
      (6a), `demo_sdf_composed.py` (6b — already demonstrates subtraction via
      `Composed`), `demo_sdf_arrowhead.py`, `demo_sdf_light_animation.py`.
      Remaining:
  - [ ] `py/examples/viz/demo_sdf_algebra.py` — MV rendering with
        OPNS/IPNS + distance-function switching.
  - [ ] `py/examples/viz/demo_sdf_booleans.py` — the per-object
        `combine=`/`polarity=` API (union/intersection/subtract across
        *separate* scene objects — distinct from `Composed`, which
        `demo_sdf_composed.py` already covers).
  - [ ] `py/examples/viz/demo_sdf_opacity.py` — distance → opacity transfer
        functions (`step`/`linear`/`sigmoid`) and soft translucent objects.
  - [ ] Cross-check each example runs with `uv run python …`.
- [ ] Docs:
  - [ ] The plan README (`dev/todos/viz-sdf-viewer/README.md`) already exists
        and must be brought up to date with the shipped phases 1–6c and the
        lighting/overlay/update additions before finalizing.
  - [ ] New `docs/py/viz/sdf-viewer.md` (or similar) covering architecture,
        the two rendering paths, distance functions, normalization, and the
        WebGL2 requirement.
  - [ ] Link from the docs index; note the WebGL2 prerequisite clearly.
- [ ] Changelog:
  - [ ] Add an entry following `dev/workflows/changelog.md`.
- [ ] Pull request:
  - [ ] Open a PR following `dev/workflows/pull-request.md`.

## Verification

- [ ] `uv run pytest py/tests/viz/sdf` passes (accumulated suite).
- [ ] `uv run python py/examples/viz/demo_sdf_algebra.py` renders MVs and
      responds to distance-function changes.
- [ ] `uv run python py/examples/viz/demo_sdf_booleans.py` renders a subtract
      (negative sphere carving a positive sphere) and an intersection correctly.
- [ ] `uv run python py/examples/viz/demo_sdf_opacity.py` renders `linear` and
      `sigmoid` transfers with soft translucent edges.
- [ ] Docs render and build (`mkdocs`); no broken links.
- [ ] Changelog entry present and correctly formatted.