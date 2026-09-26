# EXR & HDR Image Readers + File Chooser — Overview

**Created:** 2026-09-26 | **Status:** Done | **Branch:** `fix/image-display`

## Goal

Add dependency-free readers for the two common HDR image formats — OpenEXR
(scanline, lossless: `NONE`/`RLE`/`ZIPS`/`ZIP`/`PIZ`) and Radiance RGBE
(`.hdr`) — so the viewer can load Blender renders and HDRIs without the
`OpenEXR` package or Pillow.  Separately (independent phase 6), upgrade the
file chooser: highlight the selected entry, double-click to select, filter by
file type, and select folders.

## Architecture (short)

- New pure module `py/pytanga/viz/_image_io.py` (numpy + stdlib `zlib` only):
  - `read_exr(source) -> np.ndarray`  (`float32`, `(H, W, C)`, `C ∈ {1, 3, 4}`)
  - `read_hdr(source) -> np.ndarray`  (`float32`, `(H, W, 3)`)
  `source` is a `str` path, `pathlib.Path`, or raw `bytes`.  Both return **raw
  linear values** (no tone mapping / colour transforms).
- Re-export `read_exr`/`read_hdr` from `pytanga.viz.image` (next to
  `pil_to_numpy`).
- File chooser (independent): `FileChooser` (`_controls.py`), `FileChooserView`
  (`views/control_views.py`), `FileChooserDialog` (`_dialog.py`) gain a
  `folders_only: bool` flag, and the existing `accept` string becomes a real
  extension filter applied server-side in `list_directory` (`_file_browser.py`).
  Frontend `views/file-chooser-view.js` + `views/file-browser-view.js` add
  highlight / double-click / folder-select; `_layout.py` passes
  `accept`/`folders_only` through the `file_browser_navigate` handler.

## Decisions (confirmed)

- **EXR scope**: scanline only; codecs `NONE` (0), `RLE` (1), `ZIPS` (2), `ZIP`
  (3), `PIZ` (4).  Channel types `UINT`/`HALF`/`FLOAT` → `float32`, sampling
  `xSampling == ySampling == 1`.  `dataWindow` is read; `displayWindow` cropping
  is ignored.
- **HDR scope**: `#?RADIANCE`/`#?RGBE`, standard resolution line (handle the
  sign/order variants), uncompressed + new (adaptive) RLE (legacy old RLE is
  read as flat, matching the reference reader).  RGBE→float via
  `v = (m + 0.5) / 256 * 2**(e - 128)`, with `e == 0 → 0`.
- **PIZ** follows the OpenEXR/Imath reference algorithm (Huffman-decode → signed
  16-bit wavelet coefficients → inverse Haar wavelet → undo bit-shuffle),
  cross-checked against `tinyexr` (BSD-3-Clause; attribute if code is closely
  derived).
- **File chooser**: single-click highlights (no accept), double-click accepts;
  `folders_only=True` hides files and adds a "Select this folder" action that
  accepts the current directory.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-hdr-reader.md](./01-hdr-reader.md) | Radiance RGBE reader + fixtures |
| 2 | [02-exr-container.md](./02-exr-container.md) | EXR container + NONE + channel/type decode |
| 3 | [03-exr-lossless-compression.md](./03-exr-lossless-compression.md) | RLE + ZIPS + ZIP |
| 4 | [04-exr-piz.md](./04-exr-piz.md) | PIZ |
| 5 | [05-integration-docs-changelog.md](./05-integration-docs-changelog.md) | Wire into load_image_from_disk + docs + changelog |
| 6 | [06-file-chooser.md](./06-file-chooser.md) | File chooser: highlight, double-click, filter, folder select |

## Testing as you go

- Python: `uv run pytest py/tests/viz/test_image_io.py py/tests/viz/test_file_chooser.py -q`
- Lint/type: `uv run ruff check …` / `uv run ruff format --check …` / `uv run ty check`
- Frontend (phase 6): `cd js/dev && node tests/check-syntax.mjs && node --test 'tests/*.test.mjs'` + `uv run python tools/build-viewer-js.py --check`
- Docs: `uv run mkdocs build --strict`

## Non-goals

- EXR: `PXR24`, `B44`/`B44A`, `DWAA`/`DWAB`, `HTJ2K`, tiled, multi-part, deep,
  subsampled channels, `displayWindow` cropping, tone mapping / colour spaces.
- HDR: XYZ (`32-bit_rle_xyze`) is returned as-is (no XYZ→RGB conversion).
- File chooser: drag-drop, thumbnails, recursive search, virtualised listing.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.
