# Phase 6 — Docs + changelog

## Goal

Record the fix in the branch changelog per the repo workflow.

## Files

- Edit: `docs/changelog/2026-09-01_fix-tabular.md`

## Steps

- [x] **6.1 — Append a Bug Fixes entry**
  - Follow `dev/workflows/changelog.md` (wrap ~80 cols, self-contained bullet).
  - Under the existing `## Bug Fixes` section add a bullet: standalone HTML
    export of 2D views now recomputes the orthographic camera on window resize
    (the old handler only updated `aspect`, a no-op for orthographic cameras, so
    2D snapshots/figures stretched and never self-corrected); it now recomputes
    `left/right/top/bottom` via the shared `applyOrthoFrustum`, matching the
    live viewer.

## Validation

`uv run pytest py/tests/viz/ -q && node --test 'dev/src/js-tests/*.test.mjs'`

## Notes

- The `docs/changelog/index.md` entry and the hash rename happen at PR time (see
  `dev/workflows/pull-request.md`), not here.
- This appends to the current branch (`fix/tabular`) changelog. If this work
  lands on its own branch instead, name the changelog
  `YYYY-MM-DD_<branch-name>.md` per `dev/workflows/changelog.md`.
