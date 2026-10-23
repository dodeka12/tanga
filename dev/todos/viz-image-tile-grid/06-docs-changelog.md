# Phase 6 — Docs + examples + changelog

## Goal

Document the new per-tile streaming renderer and per-tile events, update the
examples to show tile coordinates, and write the branch changelog.

## Files

- Edit: `docs/dev/architecture/viz-architecture.md`
- Edit: `docs/dev/architecture/viz-controls-and-interactions.md`
- Edit: `py/examples/viz/image/huge_image_background.py` (+ generated docs)
- Edit: `docs/changelog/2026/10/23_fix-image-loading.md` (branch changelog)

## Steps

- [ ] **6.1 — `viz-architecture.md`**
  - Update "Image canvas (extension recipe)" and "Calibrated camera view
    (extension recipe)": a `source:"tiled"` layer renders as a per-tile mesh grid
    (viewport + one-tile border), not one full-level texture; multi-layer + tiled
    keeps the whole-level fallback.

- [ ] **6.2 — `viz-controls-and-interactions.md`**
  - Update "Image load events": `image_tile_load` / `image_tile_loaded` are
    per-tile and carry `tile_x`/`tile_y`; `image_loaded` is the first-frame
    signal.

- [ ] **6.3 — Example (`huge_image_background.py`)**
  - Include `tile_x`/`tile_y` in the log line for tile events, and regenerate
    example docs (`uv run python tools/generate-example-docs.py`).

- [ ] **6.4 — Branch changelog**
  - Append a **New Features** bullet (viewport-based per-tile streaming +
    per-tile events) and a **Bug Fixes** bullet (no longer loads the whole level;
    pan loads visible tiles) to the existing branch changelog.

## Validation

```
uv run python tools/generate-example-docs.py --check && uv run mkdocs build --strict && uv run pytest py/tests/viz -q
```

## Notes

- This extends (not replaces) the documented `image_status` channel, mirroring
  how the `client_log` section documents a backend-only reserved control.
