# Phase 5 — Docs, example, changelog

## Goal

Document the new PH-curve entity, the reflection function, and the
`Colormap`/`PHCurveStyle` viz additions; add a runnable example; and write the
branch changelog.

## Files

- New: `docs/py/ga/geometry/phcurves.md`
- New: `py/examples/viz/entities/ph_curve.py`
- New: `docs/changelog/2026-08-31_fix-docs.md` (adjust date/branch if they change)
- Edit: `mkdocs.yml` (nav entry for the PH curves page)
- Edit: `docs/py/ga/geometry/reflection.md` (or `operators.md`) — document
  `refor`/`reflector`
- Edit: `docs/py/viz/entities/point-path.md` (or a viz styles page) — document
  `Colormap`/`PHCurveStyle`

## Steps

- [ ] **5.1 — Geometry docs**
  - `phcurves.md`: motivation ("not representable by a multivector"), the
    reflection-form math summary, `PHCurve2D`/`PHCurve3D` constructor and the
    evaluation API, plus a short code sample computing position/velocity/
    curvature.
  - Document `reflector` (E2 line / E3 plane, with the reflect test) and
    `refor` on the reflection/operators page.
- [ ] **5.2 — Viz docs**
  - Document `Colormap` presets + `PHCurveStyle` (`num_points`, `colormap`)
    and the "samples into a `PointPath`" behavior.
- [ ] **5.3 — Example**
  - `py/examples/viz/entities/ph_curve.py` following `dev/workflows/
    example-docs.md` (license header, one-line `<name>.py — …` docstring, a
    `Run with:` line, and a trailing `Keywords:` line).
  - Build a `PHCurve3D`, add it via `viz.add(..., style=PHCurveStyle(
    num_points=300, colormap=Colormap.turbo()))`, add start/end points +
    velocity directions, and `viz.run()`.
  - Regenerate docs: `uv run python tools/generate-example-docs.py` then
    `uv run python tools/generate-example-docs.py --check`.
- [ ] **5.4 — Nav**
  - Add the PH curves page to `mkdocs.yml` under the Geometry section.
- [ ] **5.5 — Changelog**
  - Create `docs/changelog/2026-08-31_fix-docs.md` per
    `dev/workflows/changelog.md` (title `# Changes since version <tag from
    tools/last-release.py>`; `## New Features` bullet covering PH curves +
    `reflector` + `Colormap`/`PHCurveStyle`).
- [ ] **5.6 — Final validation**
  - Full pytest + lint + strict docs build (see Validation).

## Validation

`uv run pytest -q && uv run ruff check py/pytanga/geometry py/pytanga/viz py/tests/geometry py/tests/viz && uv run mkdocs build --strict`

## Notes

- Rename the changelog to the hash form and update `docs/changelog/index.md`
  only at PR time, per `dev/workflows/pull-request.md`.
- Mark the plan `Status: Done` in `README.md` after this phase.
