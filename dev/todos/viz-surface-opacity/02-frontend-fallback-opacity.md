# Phase 2 — Frontend fallback opacities → 1.0

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` (the per-kind renderer notes).
> The `styleParam(ent, 'opacity', fallback)` fallbacks are defensive only — the
> serializer always emits a merged `ent.style.opacity` — but they must match the
> Python defaults.

## Goal

Align the eight solid renderers' `styleParam(ent, 'opacity', …)` fallbacks to
`1.0` and regenerate the viewer bundle.

## Files

- Edit `py/pytanga/viz/templates/renderers/sphere.js` (0.4 → 1.0)
- Edit `py/pytanga/viz/templates/renderers/plane.js` (0.3 → 1.0)
- Edit `py/pytanga/viz/templates/renderers/box.js` (0.9 → 1.0)
- Edit `py/pytanga/viz/templates/renderers/cylinder.js` (0.9 → 1.0)
- Edit `py/pytanga/viz/templates/renderers/ellipsoid.js` (0.9 → 1.0)
- Edit `py/pytanga/viz/templates/renderers/disk.js` (0.9 → 1.0)
- Edit `py/pytanga/viz/templates/renderers/cone.js` (0.9 → 1.0)
- Edit `py/pytanga/viz/templates/renderers/partial_disk.js` (0.9 → 1.0)
- Regenerate `js/tanga-viewer.js` + `js/tanga-viewer.manifest.json`

## Steps

- [x] **2.1 — Update the eight fallback defaults**
  - Change the `styleParam(ent, 'opacity', <old>)` fallback to `1.0` in each of
    the eight files above.  Change only the numeric fallback, not the rest.

- [x] **2.2 — Regenerate the bundle**
  - `uv run python tools/build-viewer-js.py`

## Validation

```bash
node js/dev/tests/check-syntax.mjs
node --test js/dev/tests/*.test.mjs
uv run python tools/build-viewer-js.py --check
```

## Notes

- These fallbacks are not actually exercised (the wire dict always carries the
  merged `style.opacity`), but they must not drift from the Python defaults.
