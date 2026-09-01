# Phase 7 — changelog

## Goal

Record the fix in the branch changelog per the repo workflow.

## Files

- New: `docs/changelog/<date>_fix-2d-camera-fit.md`

## Steps

- [x] **7.1 — Author the branch changelog**
  - Follow `dev/workflows/changelog.md`: create
    `docs/changelog/YYYY-MM-DD_fix-2d-camera-fit.md` (use the current date).
  - Title `# Changes since version <last-stable-release>` where
    `<last-stable-release>` comes from `uv run python tools/last-release.py`.
  - Add a `## Bug Fixes` bullet: 2D `fit_camera=True` now fits to the pane's
    size (not the window) so split-view 2D scenes are correctly aspected on
    first paint.
  - Add a `## Refactor` bullet: the ortho frustum/aspect math is unified into a
    single shared `camera-fit.js` used by the live viewer and HTML exports.
  - Note the deliberate fit-framing change (true contain-fit of the content box)
    if it is user-visible.

- [x] **7.2 — Validate**
  - Re-run the full suite.

## Validation

`uv run pytest py/tests/viz/ -q && node --test 'dev/src/js-tests/*.test.mjs'`

## Notes

- The `docs/changelog/index.md` entry and hash rename happen at PR time (see
  `dev/workflows/pull-request.md`), not here.
