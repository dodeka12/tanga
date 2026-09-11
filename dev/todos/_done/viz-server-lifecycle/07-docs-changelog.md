# Phase 7 — Changelog

## Goal

Record all three fixes in the branch changelog (per
`dev/workflows/changelog.md`).

## Files

- Edit: `docs/changelog/2026-08-31_fix-scene-alert.md`

## Steps

- [x] **7.1 — Add a "Bug Fixes" section to the branch changelog**
  - Append a `## Bug Fixes` section to the existing branch changelog
    `docs/changelog/2026-08-31_fix-scene-alert.md` (all changes on this branch
    share the one branch changelog).
  - Bullets covering: (a) server start/stop no longer leaks the caller's event
    loop or the `SIGINT`/`SIGTERM` handlers, and a busy port reports a clear
    message instead of a traceback or the misleading 5 s timeout; (b) the
    previously-ignored `Visualizer(port=/host=/open_browser=)` and
    `VisualizerApp(timeout=…)` parameters now take effect, and
    `VisualizerApp` forwards `add_default_axes`/`add_default_grid`; (c)
    `show(layout=…)` now opens the layout URL on the default reconnect path
    instead of a blank single scene.

## Validation

`uv run mkdocs build --strict`

## Notes

- The changelog is renamed to its hash-based form and indexed in
  `docs/changelog/index.md` only at PR time (see
  `dev/workflows/pull-request.md`), so leave it as-is here.
