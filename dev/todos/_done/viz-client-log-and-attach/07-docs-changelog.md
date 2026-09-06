# Phase 7 — Docs + changelog

## Goal

Document the client-log protocol and the deferred-attach behavior, and record
the change in the branch changelog.

## Files

- Edit: `docs/dev/architecture/viz-controls-and-interactions.md`
- New: `docs/changelog/2026-09-05_fix-examples.md`

## Steps

- [x] **7.1 — Architecture doc**
  - In `viz-controls-and-interactions.md`, document the `client_log` channel:
    frontend `sendLog(level, message, { source, data })` → `event:"log"` →
    `control:log` → backend `ClientLog` control (`_controls.py`, id
    `"client_log"`), with the `on_log`/`viz.on_client_log` sink and default
    `tanga.viz.client` logging. Note `ClientLog` is backend-only (never
    serialized).
  - Document the opt-in trace forwarding: `setLogForwarding(true)` / `?log=1`
    forwards the frontend `_log(...)` init/WS trace lines at `info` level
    (default off — only warnings/errors are forwarded).
  - Add a note on overlay anchoring: a `parent_id` group in a
    `SceneView(overlay=[...])` is attached via CSS2D once its parent entity is
    registered (deferred attach), so it works on first load.

- [x] **7.2 — Changelog**
  - Create `docs/changelog/2026-09-05_fix-examples.md` per
    `dev/workflows/changelog.md`. Title from
    `uv run python tools/last-release.py` (currently
    `# Changes since version 1.17.0 (2.0.0-rc1)` — re-run to confirm).
  - `## New Features`: client → server log channel (`sendLog` + `ClientLog`,
    incl. opt-in `?log=1` trace forwarding).
  - `## Bug Fixes`: `parent_id` control groups not shown on the single-scene
    page (deferred attach).

## Validation

`uv run mkdocs build --strict && uv run pytest py/tests/viz -q && node --test 'dev/src/js-tests/*.test.mjs'`

## Notes

- Final phase per `dev/workflows/create-plan.md`: docs + changelog last.
- No `docs/changelog/index.md` update at plan time (PR-time per
  `dev/workflows/pull-request.md`).
