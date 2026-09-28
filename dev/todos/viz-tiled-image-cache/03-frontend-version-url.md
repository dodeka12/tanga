# Phase 3 — Frontend tile URL + export bundle

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Make `makeTiledTexture` / `makeTiledDataTexture` request
`/image/{id}/{version}/{level}/{x}/{y}` and rebuild the committed export bundle.

## Files

- Edit: `py/pytanga/viz/templates/renderers/image.js`
- Edit (generated): `js/tanga-viewer.js` + `js/tanga-viewer.manifest.json`

## Steps

- [x] **3.1 — Tile URLs (`image.js`)**
  - In `makeTiledDataTexture` and `makeTiledTexture`, change
    `/image/${img.id}/${level}/${x}/${y}` to
    `/image/${img.id}/${img.version ?? 0}/${level}/${x}/${y}` (the `?? 0`
    guards an older meta without `version`).

- [x] **3.2 — Rebuild the export bundle**
  - Run `uv run python tools/build-viewer-js.py` to regenerate `js/tanga-viewer.js`
    and `js/tanga-viewer.manifest.json`.

## Validation

```bash
cd js/dev && npm run check                             # JS syntax over templates + tests
uv run python tools/build-viewer-js.py --check
```

## Notes

- `createImage` and `_backgroundTexture` just call `makeTiledTexture`, so they
  pick up the versioned URL automatically — no change there.
