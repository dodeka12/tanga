# Phase 9 — Export asset store + URL source + recording flag

## Goal

Extend the export path so image pixel data is stored once (keyed by id) outside
the per-frame snapshots, with an optional `url` source that loads at runtime,
and an `include_images` flag on `capture_frame`.

## Files

- Edit: `py/pytanga/viz/export/_animation_recording.py`
- Edit: `py/pytanga/viz/export/_exporter.py`
- Edit: `py/pytanga/viz/scene.py` (`full_state` emits image asset refs)
- Edit: `py/pytanga/viz/export/_bootstrap/_entities.py` (embed/load assets)
- Edit: `py/pytanga/viz/export/_html.py` / `_figure_html.py` (asset `<script>`)
- New: `py/tests/viz/test_image_canvas_export.py`

## Steps

- [ ] **9.1 — asset store data structure**
  - `AnimationRecording` gains an `assets: dict[id, asset]` populated once at
    `start_animation_recording()`/first `set_image`; `capture_frame` gains
    `include_images: bool = False` and re-registers assets only when `True`.
  - Entity snapshots reference image ids, never inline pixels.

- [ ] **9.2 — `source:"url"` vs `source:"data"`**
  - `data` → base64-embed the raw buffer; `url` → store the URL string and let
    the exported HTML load it via `THREE.TextureLoader` (document CORS + async
    load-error via the log pipeline).

- [ ] **9.3 — bootstrap JS**
  - `_bootstrap/_entities.py` emits JS that creates a `THREE.Texture` per asset
    once and reuses it across frames by id (no per-frame re-upload).

- [ ] **9.4 — snapshot + figure export**
  - `export_snapshot`/`export_figure` embed the `assets` dict in a separate
    `<script type="application/octet-stream">` (or equivalent) referenced by the
    scene builder; note the future glTF path reuses the same id-keyed store.

- [ ] **9.5 — tests**
  - `py/tests/viz/test_image_canvas_export.py`: assets stored once;
    `include_images=False` keeps frames free of pixel data; `url` source emits
    only the URL; `data` source embeds base64.

## Validation

`uv run pytest py/tests/viz/test_image_canvas_export.py -q && uv run ruff check py/pytanga/viz/export/_animation_recording.py py/pytanga/viz/export/_exporter.py py/pytanga/viz/scene.py`

## Notes

- This is the general "texture/asset store" the design calls for: id-keyed, not
  image-specific, so future 3D-object textures reuse it without a second store.
- `capture_frame(include_images=True)` is the opt-in for per-frame image changes.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
