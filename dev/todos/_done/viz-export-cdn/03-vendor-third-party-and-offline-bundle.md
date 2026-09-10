# Phase 3 — Vendored third-party assets + offline bundle

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Vendor the third-party CDN assets (Three.js, marked, KaTeX + fonts,
html2canvas) into the wheel and build a self-contained offline library bundle,
so `delivery="offline"` can inline everything with no network at export or view
time.

## Files

- New: `tools/vendor-third-party.py`
- New: `py/pytanga/viz/templates/vendor/manifest.json`
- New: `py/pytanga/viz/templates/vendor/tanga-viewer.offline.js` (built + committed)
- New: `py/pytanga/viz/templates/vendor/tanga-viewer.offline.manifest.json` (committed)
- New: `py/pytanga/viz/templates/vendor/marked.min.js`
- New: `py/pytanga/viz/templates/vendor/html2canvas.min.js`
- New: `py/pytanga/viz/templates/vendor/katex/` (`katex.min.js`,
  `auto-render.min.js`, `katex.offline.css`, `fonts/*.woff2`)
- New: `js/three/` (`build/three.module.js` + `examples/jsm/`, build-time only)
- Edit: `dev/package.json` (add esbuild devDependency)

## Steps

- [x] **3.1 — Pin + download third-party assets**
  - `tools/vendor-third-party.py` downloads pinned versions (three@0.170.0,
    katex@0.16.11, html2canvas@1.4.1, and a pinned marked version) into the
    vendored directories above.
  - Record versions + sha256 hashes in `manifest.json`.
- [x] **3.2 — KaTeX offline CSS (fonts base64)**
  - Generate `katex.offline.css` by rewriting every `url(fonts/…)` to
    `data:font/woff2;base64,…` for the vendored woff2 files.
- [x] **3.3 — Offline Three.js + Tanga library bundle**
  - Add esbuild to `dev/package.json` devDependencies.
  - Have the build script write `generate_library_js()` to a temp entry module
    and run esbuild `--bundle --format=esm` with `three` →
    `js/three/build/three.module.js` and `three/addons/*` →
    `js/three/examples/jsm/*`, producing `tanga-viewer.offline.js` with no
    external imports.
  - Give the offline bundle the same content-addressed manifest treatment:
    fingerprint = hash over `library_source_files()` + the vendored `js/three/`
    source + the generator; rebuild incrementally and write
    `tanga-viewer.offline.manifest.json`.
- [x] **3.4 — Commit artifacts + wheel packaging**
  - Commit `py/pytanga/viz/templates/vendor/` (auto-included in the wheel via
    `packages=["py/pytanga"]`), including the offline manifest; commit
    `js/three/` for reproducible rebuilds.
  - Confirm `tanga-viewer.offline.js` is import-free (`node --check` and no
    `import` statements remain).
- [x] **3.5 — Unit test**
  - Add a test asserting the vendored files exist, `manifest.json` hashes match,
    the offline manifest fingerprint matches its sources, and
    `tanga-viewer.offline.js` contains `window.__tanga`.

## Validation

`uv run python tools/vendor-third-party.py --check && node --check py/pytanga/viz/templates/vendor/tanga-viewer.offline.js && uv run pytest py/tests/viz/test_export_cdn.py -q`

## Notes

- This introduces a node/esbuild build step for committed artifacts (consistent
  with the committed-bundle approach); the live WebSocket viewer stays
  zero-build.
- Keep the vendored `three/` source out of the wheel (it lives under `js/` and
  is not force-included); only the `py/pytanga/viz/templates/vendor/` runtime
  assets ship.
- Offline single-file output is ~2–3 MB (dominated by Three.js + KaTeX fonts).
