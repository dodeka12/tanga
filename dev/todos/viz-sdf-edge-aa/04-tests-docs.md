# Phase 4 — Tests, validation, docs + changelog

## Goal

Lock in the shader changes with structural assertions, run the full regression,
do a manual browser smoke test, and record the change in the changelog.

## Files

- Modify: `py/tests/viz/sdf/test_proxy_shader.py`
- Modify: `py/tests/viz/sdf/test_raymarch_shader.py`
- New: `docs/changelog/YYYY-MM-DD_feat-geo-objects.md` (append; see
  `dev/workflows/changelog.md`)

## Steps

- [x] **4.1 — Structural AA assertions**
  - `test_proxy_shader.py`: assert the `res` tracking, `dFdx`/`dFdy`, and
    `smoothstep` fade appear in `proxy.glsl`, that `gl_FragDepth` is still
    written on both the hit and near-miss paths, and brace balance is still `0`.
  - ~~`test_raymarch_shader.py`~~ — skipped: Phase 3 (fullscreen AA) is deferred.

- [ ] **4.2 — Full regression**
  - `uv run pytest py/tests/viz -q` (all viz + sdf tests).

- [ ] **4.3 — JS syntax + export bundle**
  - `node --check` on `renderers/sdf.js` (and `glsl.js` if touched).
  - `uv run pytest py/tests/viz/test_export_renderers.py -q` — the export
    bootstrap still assembles the renderer set (GLSL is inlined, so the AA code
    rides along automatically).

- [ ] **4.4 — Manual browser smoke (the real proof)**
  - `uv run python py/examples/viz/sdf/mesh_vs_sdf_grid.py` — verify the SDF
    twins' silhouettes are smooth and still occlude the mesh twins correctly.
  - Run a fullscreen example (e.g. `py/examples/viz/sdf/entities.py`) to confirm
    Phase 3.

- [ ] **4.5 — Changelog**
  - Append a `## New Features` / `## Bug Fixes` bullet to
    `docs/changelog/YYYY-MM-DD_feat-geo-objects.md` describing analytic edge AA
    for SDF objects (both viewers), per `dev/workflows/changelog.md`.

- [ ] **4.6 — Validate**
  - `uv run pytest py/tests/viz -q`.

## Validation

`uv run pytest py/tests/viz -q`

## Notes

- There is no DOM/WebGL test harness, so the only pixel-level verification is the
  manual browser smoke; the automated tests guard *structure* (single `main`,
  GLSL3 output, `gl_FragDepth`, brace balance, map contract) rather than pixels.
- Keep the changelog bullet self-contained and wrap at ~80 columns.
