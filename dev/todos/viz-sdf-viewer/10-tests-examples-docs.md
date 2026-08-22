# Phase 10 — Tests, examples, docs, changelog, PR

**Status:** Planned

## Goal

Lock in the SDF viewer with tests, user-facing examples, documentation, a
changelog entry, and a pull request following the repository workflows.

## Steps

- [ ] Unit tests (Python):
  - [ ] `py/tests/viz/sdf/test_distance.py` — `sdf/distance.py` (distance enum)
        and primitive-tree serialization.
  - [ ] `py/tests/viz/sdf/test_serializer.py` — entity → SDF tree structure
        and parameters for every supported kind.
  - [ ] `py/tests/viz/sdf/test_algebra_embedding.py` — `M` vs direct
        `ip/op` reconstruction, ordering consistency, normalize on/off, P3
        trivector case, N3 quadratic case.
- [ ] Smoke test (Python):
  - [ ] `dev/src/test_viz_sdf.py` driving `SdfVisualizer` headless where
        feasible (server boot, config message, basic scene serialization).
- [ ] Examples:
  - [ ] `py/examples/viz/demo_sdf_entities.py` — analytic entities.
  - [ ] `py/examples/viz/demo_sdf_algebra.py` — MV rendering with
        OPNS/IPNS + distance-function switching.
  - [ ] `py/examples/viz/demo_sdf_booleans.py` — positive/negative objects
        (`combine`/`polarity`) demonstrating union, intersection, subtraction.
  - [ ] `py/examples/viz/demo_sdf_opacity.py` — distance → opacity transfer
        functions (`step`/`linear`/`sigmoid`) and soft translucent objects.
  - [ ] Cross-check each example runs with `uv run python …`.
- [ ] Docs:
  - [ ] New `docs/py/viz/sdf-viewer.md` (or similar) covering architecture,
        the two rendering paths, distance functions, normalization, and the
        WebGL2 requirement.
  - [ ] Link from the docs index; note the WebGL2 prerequisite clearly.
- [ ] Changelog:
  - [ ] Add an entry following `dev/workflows/changelog.md`.
- [ ] Pull request:
  - [ ] Open a PR following `dev/workflows/pull-request.md`.

## Verification

- [ ] `uv run pytest py/tests/viz/sdf` passes.
- [ ] `uv run python py/examples/viz/demo_sdf_entities.py` renders analytic
      entities in the browser.
- [ ] `uv run python py/examples/viz/demo_sdf_algebra.py` renders MVs and
      responds to distance-function changes.
- [ ] `uv run python py/examples/viz/demo_sdf_booleans.py` renders a subtract
      (negative sphere carving a box) and an intersection correctly.
- [ ] `uv run python py/examples/viz/demo_sdf_opacity.py` renders `linear` and
      `sigmoid` transfers with soft translucent edges.
- [ ] Docs render and build (`mkdocs`); no broken links.
- [ ] Changelog entry present and correctly formatted.