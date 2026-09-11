# Phase 2 — Bundle build tool + committed artifact + CDN resolver

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Add a content-addressed, incremental build tool that regenerates the committed
`js/tanga-viewer.js` bundle only when its inputs change, commit the bundle + its
manifest, and add a `_cdn.py` module that resolves the installed version to a
jsDelivr ref and builds the bundle URL.

## Files

- New: `tools/build-viewer-js.py`
- New: `js/tanga-viewer.js` (generated + committed)
- New: `js/tanga-viewer.manifest.json` (committed dependency manifest)
- New: `py/pytanga/viz/export/_cdn.py`
- Edit: `py/pytanga/viz/export/__init__.py`
- New: `py/tests/viz/test_export_cdn.py`

## Steps

- [x] **2.1 — `tools/build-viewer-js.py` (incremental + manifest)**
  - Compute the input fingerprint = sha256 over the ordered
    `library_source_files()` list, each file's sha256, and a `generator_sha256`
    (hash of `py/pytanga/viz/export/_bootstrap/`).
  - `build` (default): if `js/tanga-viewer.manifest.json` is missing or its
    stored `fingerprint_sha256` differs, regenerate `js/tanga-viewer.js` and
    rewrite the manifest; otherwise print "up to date" and do nothing.
  - `--force`: always regenerate + rewrite the manifest.
  - `--check`: regenerate in-memory, compare its hash to the committed bundle
    hash AND the computed fingerprint to the manifest's; exit 1 on mismatch.
  - Store POSIX-style relative paths and the ordered `files` array (with
    per-file sha256) in the manifest.
- [x] **2.2 — Commit bundle + manifest**
  - Run `uv run python tools/build-viewer-js.py`, then commit
    `js/tanga-viewer.js` and `js/tanga-viewer.manifest.json`.
  - `node --check js/tanga-viewer.js` must pass.
- [x] **2.3 — `py/pytanga/viz/export/_cdn.py`**
  - `DeliveryMode = Literal["cdn", "inline", "offline"]` (offline is delivered
    in phases 3–4; declared here per the fixed contract).
  - `_CDN_BASE = "https://cdn.jsdelivr.net/gh/dodeka12/tanga"`,
    `_BUNDLE_PATH = "js/tanga-viewer.js"`.
  - `resolve_delivery_ref(override=None)`:
    - return `override` unchanged when given;
    - else read `importlib.metadata.version("tanga-py")` and map to the git tag
      (`1.17.0` → `v1.17.0`, `1.17.0rc3` → `v1.17.0-rc3`);
    - raise a clear `ValueError` for dev/local versions (no tag exists) telling
      the caller to pass `delivery_ref`.
  - `build_bundle_url(ref=None)` →
    `f"{_CDN_BASE}@{resolve_delivery_ref(ref)}/{_BUNDLE_PATH}"`.
- [x] **2.4 — Re-export + unit tests**
  - Export `DeliveryMode`, `resolve_delivery_ref`, `build_bundle_url` from
    `export/__init__.py`.
  - Add `py/tests/viz/test_export_cdn.py` covering the version→tag mapping and
    the explicit-override and error paths.

## Validation

`uv run python tools/build-viewer-js.py --check && node --check js/tanga-viewer.js && uv run pytest py/tests/viz/test_export_cdn.py -q && uv run ruff check py/pytanga/viz/export/_cdn.py py/pytanga/viz/export/__init__.py tools/build-viewer-js.py`

## Notes

- The bundle must be committed so it exists in the git tree at every tag
  (jsDelivr serves from the tag's tree); the manifest is committed for
  incremental rebuilds in fresh clones/CI.
- Keep the mapping function small and explicit; only the `rc` prerelease form is
  used by this repo's tags today.
- Hashing the generator (`_bootstrap/`) makes the fingerprint faithful even when
  no JS/GLSL file changes but the emitted code does.
