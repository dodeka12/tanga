# Phase 7 — Rebuild bundle + full validation

## Goal

Regenerate the committed `js/tanga-viewer.js` from the edited templates and gate
the change with the bundle drift check + the full Python suite.

## Files

- Edit (generated): `js/tanga-viewer.js`
- Edit (generated): `js/tanga-viewer.manifest.json`

## Steps

- [x] **7.1 — rebuild the bundle**
  - `uv run python tools/build-viewer-js.py` (regenerates the bundle + manifest
    because the renderer sources changed).

- [x] **7.2 — verify bundle is in sync**
  - `uv run python tools/build-viewer-js.py --check` (exit 0; no drift).

- [x] **7.3 — full Python suite**
  - `uv run pytest -q`. Confirm the only expected skips are the offline-export
    tests in `py/tests/viz/test_export_delivery.py` (per
    `dev/workflows/pull-request.md`).

## Validation

`uv run python tools/build-viewer-js.py --check && uv run pytest -q`

## Notes

- `js/tanga-viewer.js` is a build artifact; do not hand-edit it. The renderer +
  `scene-builder.js` changes appear there as bundled functions.
- A browser smoke of the original repro (animated `Circle` center) plus a
  rotation (e.g. a `Cylinder` with a non-+Y axis) is the manual acceptance check
  that placement now flows through the transform.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
