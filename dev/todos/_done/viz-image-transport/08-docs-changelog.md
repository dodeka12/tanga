# Phase 8 — Developer docs, user docs, example docs, changelog

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Land developer documentation (architecture) and user documentation (guides) for
the new transport, regenerate example docs for the Phase 7 scripts, and add the
changelog.

## Files

- Edit: `docs/dev/architecture/viz-architecture.md`
- New: `docs/py/viz/image/image-transport.md`
- New: `docs/py/viz/image/tiled-images.md`
- New: `docs/py/viz/image/image-stream.md`
- Edit: `docs/py/viz/image/index.md`
- New: `docs/changelog/2026/09/DD_feat-image-transport.md`

## Steps

- [x] **8.1 — developer docs (`viz-architecture.md`)**
  - Document the **v2 binary frame** (`codec` byte, v1 accepted / v2 emitted),
    the `/image/{id}/{level}/{x}/{y}` tile route, the `/stream/{id}` MJPEG
    route, and the export asset-store JPEG default.

- [x] **8.2 — user docs: `image-transport.md`**
  - Standard vs raw transport: `ImageData(codec=..., jpeg_quality=...)`, the
    auto-selection rule (uint8 1/3ch → JPEG, else lossless zlib), the `"raw"`
    opt-out, and when to choose each.

- [x] **8.3 — user docs: `tiled-images.md`**
  - Huge images via `viz.register_image_pyramid(...)`: tile size, levels,
    pan/zoom behaviour, and the multi-consumer pull model.

- [x] **8.4 — user docs: `image-stream.md`**
  - Camera feeds via `viz.register_camera_stream(...)` at 15–30 Hz, and pointing
    a camera pane / background at `/stream/{id}`.

- [x] **8.5 — nav + example docs**
  - Link the three new guides from `docs/py/viz/image/index.md`.
  - Regenerate example doc pages for the four Phase 7 scripts
    (`dev/workflows/example-docs.md`).

- [x] **8.6 — changelog**
  - Create `docs/changelog/2026/09/DD_feat-image-transport.md` per
    `dev/workflows/changelog.md` (title via `uv run python tools/last-release.py`;
    `## New Features` bullets for codec transport, tiled images, MJPEG streams,
    and JPEG-by-default export).

## Validation

```powershell
uv run mkdocs build --strict
uv run python tools/last-release.py
uv run pytest -q
```

## Notes

- The final phase always ends with docs + changelog; rename the changelog to the
  squashed-commit hash at PR time (`dev/workflows/pull-request.md`).
