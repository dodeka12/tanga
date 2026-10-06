# Phase 3 — Rebuild the CDN viewer bundle

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md`) for the
> subsystem(s) this work touches, so the new code aligns with the documented
> architecture. If this work introduces or changes architecture, update the
> developer docs.

## Goal

Regenerate the committed `js/tanga-viewer.js` + `js/tanga-viewer.manifest.json` so
the CDN delivery mode carries the always-wrap scene-builder (and no stale identity
short-circuit).

## Files

- Edit (generated): `js/tanga-viewer.js`
- Edit (generated): `js/tanga-viewer.manifest.json`

## Steps

- [ ] **3.1 — Rebuild the bundle**
  - `uv run python tools/build-viewer-js.py`
- [ ] **3.2 — Confirm no drift**
  - `uv run python tools/build-viewer-js.py --check`

## Validation

```
uv run python tools/build-viewer-js.py --check
node --test js/dev/tests/*.test.mjs
```

## Notes

- The bundle is content-addressed; the manifest's `fingerprint_sha256` must change
  to reflect the new scene-builder source.
