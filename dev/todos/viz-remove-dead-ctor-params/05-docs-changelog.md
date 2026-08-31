# Phase 5 — Docs & changelog

## Goal

Update the API docs and the branch changelog for the removed constructor
params.

## Files

- Edit: `docs/py/viz/visualizer/visualizer.md`
- Edit: `docs/py/viz/app/handlers.md`
- Edit: `docs/changelog/2026-08-31_fix-scene-alert.md`

## Steps

- [x] **5.1 — `visualizer.md`**
  - Remove `open_browser=None,` from the constructor snippet, and the
    `port` / `host` / `open_browser` rows from the parameter table.
  - Note that host/port go on `start_server(host=…, port=…)` /
    `show(host=…, port=…)`.
- [x] **5.2 — `handlers.md`**
  - Remove `port=8765`, `host="localhost"`, `open_browser=None` from the
    `VisualizerApp(...)` example and note `run(port=…, host=…)`.
- [x] **5.3 — changelog**
  - In `docs/changelog/2026-08-31_fix-scene-alert.md`, replace the
    "previously-ignored `Visualizer`/`VisualizerApp` parameters now take
    effect" bug-fix bullet with a `## Breaking Changes` bullet: removed
    `Visualizer(port/host/open_browser)` and
    `VisualizerApp(port/host/open_browser)`; use
    `start_server(host=…, port=…)` / `show(…)` / `run(port=…, host=…)`.

## Validation

`uv run mkdocs build --strict`

## Notes

- The changelog is renamed to its hash-based form and indexed in
  `docs/changelog/index.md` only at PR time (see
  `dev/workflows/pull-request.md`).
