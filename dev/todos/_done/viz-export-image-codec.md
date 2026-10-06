# Viz export image codec — Overview

**Created:** 2026-10-06 | **Status:** Done | **Branch:** `fix/html-export-transform`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md`) for the
> subsystem(s) this work touches, so the new code aligns with the documented
> architecture. If this work introduces or changes architecture, update the
> developer docs.

## Goal

Let callers control how images are compressed when embedded in a static or
animated HTML export, via a single `image_codec: EImageCodec | None = None`
option (`None` = auto-select).  This reuses the existing wire codec
(`EImageCodec`, `RAW`/`JPEG`/`ZLIB`) and the existing encoder
(`_image_wire._resolve_codec` / `encode_zlib_raw` / `encode_jpeg`) so the export
path matches the live-viewer path.  The frontend already decodes `codec:"zlib"`
via `DecompressionStream('deflate')` — **no JS change**.

The concrete wins over today's behaviour:

- `uint16` / `float32` / RGBA images are now **losslessly zlib-compressed**
  (today they are stored as raw base64 with no compression).
- JPEG quality is now **honored** from `ImageData.jpeg_quality` (today the
  export hardcodes 85 and ignores the field).
- Callers can **force** a codec (`image_codec=JPEG/ZLIB/RAW`) or opt back into
  raw (`image_codec=RAW`).

## Decisions (confirmed)

- **Type:** `image_codec: EImageCodec | None = None` (no new enum). `None` =
  auto-select, consistent with `_image_wire._resolve_codec` and
  `encode_image_frame(..., codec=None)`.
- **Param name:** `image_codec` on the public export methods.
- **Resolution order** (mirrors the live viewer, which passes `codec=img.codec`):
  1. export-level `image_codec` if set,
  2. else `ImageData.codec` (per-image hint),
  3. else auto via `_resolve_codec` (JPEG for uint8 1/3-channel, zlib otherwise).
- **`image_codec=JPEG` on a non-JPEG-eligible image** (uint16/float32/RGBA)
  **raises a clear `ValueError`** (JPEG cannot encode those dtypes), matching
  `encode_jpeg`'s existing strictness rather than silently falling back.
- Auto (`None`) honors `ImageData.jpeg_quality` (default 85).

## Steps

- [x] **1 — Core encoding logic (`py/pytanga/viz/export/_animation_recording.py`)**
  - `_image_asset(img, codec: EImageCodec | None = None)`:
    - `img.url is not None` → external-URL asset (unchanged, no codec).
    - else `effective = codec if codec is not None else img.codec`;
      `resolved = _resolve_codec(img.data, effective)` (import from
      `.._image_wire`).
    - `JPEG` → if not `img.supports_jpeg`, raise
      `ValueError("image_codec='jpeg' requires a uint8 image with 1 or 3 channels, got …")`;
      else `asset["source"]="url"`, `asset["url"] = img.to_jpeg_data_url(quality=img.jpeg_quality or 85)`.
    - `ZLIB` → `asset["source"]="data"`, `asset["codec"]="zlib"`,
      `asset["data"] = base64.b64encode(encode_zlib_raw(img.data)).decode("ascii")`.
    - `RAW` → `asset["source"]="data"`, `asset["codec"]="raw"`,
      `asset["data"] = img.to_base64()`.
  - `capture_image_assets(scene, codec=None)` → pass `codec` to `_image_asset`.
  - `image_hydration_frames(assets)` → for `data` assets emit
    `{"id", "codec": asset.get("codec", "raw"), "data_b64": asset["data"]}`
    (so `"zlib"` flows through).
  - `AnimationRecording.__init__(..., codec=None)` stores `self._codec`;
    `capture_assets()` calls `capture_image_assets(self._scene, self._codec)`.

- [x] **2 — Visualizer entry points (`py/pytanga/viz/visualizer.py`)**
  - Add `image_codec: EImageCodec | None = None` to `export_snapshot`,
    `export_figure`, `display_snapshot`, and `start_animation_recording`.
  - Thread through `_export_scene_snapshot`, `_export_scene_figure`,
    `_render_snapshot_html`, `_render_figure_html`, and
    `_start_scene_animation_recording`.
  - Static: pass `image_codec` to `capture_image_assets(scene, image_codec)`.
  - Animated: pass `codec=image_codec` to `AnimationRecording(...)`.

- [x] **3 — Handle + exporter forwarding**
  - `py/pytanga/viz/_scene_handle.py` — forward `image_codec` in
    `export_snapshot`, `export_figure`, `start_animation_recording`.
  - `py/pytanga/viz/export/_exporter.py` — forward `image_codec` in
    `export_animated_figure` / `export_animated_html` (deprecated wrapper).

- [x] **4 — Tests + changelog**
  - Update `py/tests/viz/test_image_canvas_export.py`:
    - `test_data_image_captured_as_base64` (uint16) and
      `test_uint8_rgba_image_captured_as_raw_base64` now expect `codec="zlib"`.
    - Add: `image_codec="raw"` forces raw; `image_codec="zlib"` forces zlib;
      `image_codec="jpeg"` on uint16 raises `ValueError`; `jpeg_quality` is
      honored in the JPEG data URL.
  - Add a `## Bug Fixes` / `## New Features` entry to
    `docs/changelog/2026/10/05_fix-html-export-transform.md`.

## Validation

- `uv run pytest py/tests/viz/test_image_canvas_export.py -q`
- `uv run ruff check py/pytanga/viz/export/_animation_recording.py py/pytanga/viz/visualizer.py py/pytanga/viz/_scene_handle.py py/pytanga/viz/export/_exporter.py`
- `uv run pytest py/tests/viz -q`

## Non-goals

- No frontend/JS change (the `codec:"zlib"` decode path already exists).
- No change to the live-viewer wire path (already uses `_resolve_codec` +
  zlib).
- No new compression format beyond `RAW`/`JPEG`/`ZLIB`.
