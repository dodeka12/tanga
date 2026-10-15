# Phase 3 — Rebuild the committed bundle

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md`).  The
> committed `js/tanga-viewer.js` is generated from the templates and must be
> rebuilt after any template change.

## Goal

Regenerate `js/tanga-viewer.js` and its manifest so the CDN/export bundle
matches the edited templates.

## Files

- Regenerate: `js/tanga-viewer.js`
- Regenerate: `js/tanga-viewer.manifest.json`

## Steps

- [x] **3.1 — Rebuild.**
  - Run `uv run python tools/build-viewer-js.py` and confirm it prints
    `bundled js/tanga-viewer.js (…)`.

- [x] **3.2 — Verify no drift.**
  - Run `uv run python tools/build-viewer-js.py --check` and confirm
    `js/tanga-viewer.js up to date`.

## Validation

`uv run python tools/build-viewer-js.py --check`

## Notes

- The bundle is content-addressed and incremental; `--check` is the CI gate for
  drift (`js/tanga-viewer.js` + `js/tanga-viewer.manifest.json`).
