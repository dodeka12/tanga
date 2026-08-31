# Phase 10 — Tests, examples, docs, changelog, PR

**Status:** Implemented (except the PR, which needs a push + `gh pr create`).

## Goal

Lock in the SDF viewer with tests, user-facing examples, documentation, a
changelog entry, and a pull request following the repository workflows.

## Steps

- [x] Full-suite run:
  - [x] `uv run pytest py/tests/viz/sdf` — runs the accumulated per-phase
        tests (each already run in its phase); this is the integration
        regression pass, not the first time the tests execute.
- [x] Smoke test (Python):
  - [x] `dev/src/test_viz_sdf.py` driving `SdfVisualizer` headless (server
        boot, scene serialization, algebra path + calibration, combine modes,
        distance/opacity setters).
- [x] Examples. Already delivered (not re-done here): `demo_sdf_entities.py`
      (6a), `demo_sdf_composed.py` (6b — already demonstrates subtraction via
      `Composed`), `demo_sdf_arrowhead.py`, `demo_sdf_light_animation.py`.
      Remaining (now done):
  - [x] `py/examples/viz/demo_sdf_algebra.py` — MV rendering with mixed
        algebras + calibration + distance-function switching.
  - [x] `py/examples/viz/demo_sdf_booleans.py` — the per-object
        `combine=`/`polarity=` API (union/intersection/subtract across
        *separate* scene objects — distinct from `Composed`, which
        `demo_sdf_composed.py` already covers).
  - [x] `py/examples/viz/demo_sdf_opacity.py` — distance → opacity transfer
        functions (`step`/`linear`/`sigmoid`) and soft translucent objects.
  - [x] Cross-check each example runs (headless dry-run with `show`/`wait`
        stubbed, plus `py_compile`).
- [x] Docs:
  - [x] The plan README (`dev/todos/viz-sdf-viewer/README.md`) is up to date
        with the shipped phases 1–12.
  - [x] New `docs/py/viz/sdf-viewer.md` covering architecture, the two
        rendering paths, distance functions, normalization, and the WebGL2
        requirement.
  - [x] Linked from the viz index and the mkdocs nav; the WebGL2 prerequisite
        is noted.
- [x] Changelog:
  - [x] Added Phase 7–12 entries to `docs/changelog/2026-08-22_feat-sdf-viewer.md`
        (per `dev/workflows/changelog.md`).
- [ ] Pull request:
  - [ ] Open a PR following `dev/workflows/pull-request.md` (rename the
        changelog to the hash form, update `docs/changelog/index.md`, push, and
        `gh pr create`) — **pending, needs a remote push + `gh`**.

## Verification

- [x] `uv run pytest py/tests/viz/sdf` passes (accumulated suite, 133 tests).
- [x] `uv run python dev/src/test_viz_sdf.py` passes (headless smoke).
- [x] `demo_sdf_algebra.py` / `demo_sdf_booleans.py` / `demo_sdf_opacity.py`
      run headlessly (dry-run with `show`/`wait` stubbed); the browser render
      is the user-facing confirmation.
- [ ] Docs render and build (`mkdocs`) — not run here.
- [x] Changelog entry present and correctly formatted.