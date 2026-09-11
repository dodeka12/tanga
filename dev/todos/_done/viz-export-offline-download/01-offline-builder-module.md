# Phase 1 — Export-time offline builder module

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Add `py/pytanga/viz/export/_offline.py`: the pinned spec, cache, toolchain
discovery, download, esbuild bundle build, and KaTeX embedding used by
`delivery="offline"` at export time.

## Files

- New: `py/pytanga/viz/export/_offline.py`

## Steps

- [x] **1.1 — Pinned spec + constants**
  - `THREE_VERSION = "0.170.0"`, `MARKED_VERSION`, `KATEX_VERSION = "0.16.11"`,
    `HTML2CANVAS_VERSION = "1.4.1"`, plus jsDelivr URLs and a
    `_VERSION_HASH` used for the cache key.
- [x] **1.2 — Cache + download helpers**
  - `_cache_root()` → `TANGA_CACHE_DIR` or `~/.cache/tanga/offline`.
  - `_download(url, dest)` with a User-Agent and sha256 verification; re-download
    on mismatch.
- [x] **1.3 — Node/esbuild discovery**
  - `find_node()` via `shutil.which("node")`.
  - `find_esbuild()`: `TANGA_ESBUILD` → `shutil.which("esbuild")` → repo
    `dev/node_modules/esbuild/bin/esbuild`.
  - Raise `OfflineToolchainError(RuntimeError)` with an install hint when missing.
- [x] **1.4 — esbuild bundle build**
  - Download + extract the three tarball; write `generate_library_js()` to a temp
    entry with `three/addons/` rewritten to relative paths; run esbuild
    `--bundle --format=esm --alias:three=...` → `tanga-viewer.offline.js`.
- [x] **1.5 — KaTeX offline CSS**
  - Download `katex.min.css` + woff2 fonts; build `katex.offline.css` with base64
    fonts (reuse the `@font-face` rewrite from the former vendor script).
- [x] **1.6 — Public helpers**
  - `OfflineAssets` (paths to built/downloaded files), `ensure_offline_assets()`,
    `offline_library_js()`, `offline_third_party_html()`, `offline_katex_css()`.

## Validation

`uv run ruff check py/pytanga/viz/export/_offline.py && uv run python -c "import pytanga.viz.export._offline as o; print(o.find_node()); print(o.find_esbuild())"`

## Notes

- Import `generate_library_js` lazily to avoid an import cycle with
  `_bootstrap/_html.py`.
- Keep downloads idempotent so repeated exports hit the cache.
