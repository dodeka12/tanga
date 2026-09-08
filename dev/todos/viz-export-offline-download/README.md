# Viz export offline download — Overview

**Created:** 2026-09-07 | **Status:** Done | **Branch:** `feat/viz-export-cdn`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Remove the vendored third-party assets (`js/three/`,
`py/pytanga/viz/templates/vendor/`) from the repo and the wheel.  Instead,
`delivery="offline"` downloads the pinned third-party assets (three.js, marked,
KaTeX + fonts, html2canvas) to a user cache at export time and bundles three.js
+ the Tanga library via esbuild.  If Node.js or esbuild is unavailable, export
raises a clear error.

## Architecture (short)

- New `py/pytanga/viz/export/_offline.py` owns the offline pipeline: pinned
  versions + URLs + sha256, a `~/.cache/tanga/offline/<version-hash>/` cache,
  node/esbuild discovery, the esbuild bundle build, and KaTeX font embedding.
- `_cdn.py::build_library_script_tag("offline")` and
  `_bootstrap/_html.py::third_party_scripts("offline")` / `offline_katex_css()`
  lazily delegate to `_offline.py`.
- The esbuild build reuses `generate_library_js()` (installed templates) + the
  downloaded three tree, exactly as `tools/vendor-third-party.py` did before it
  is removed.

### Fixed contract

```python
class OfflineToolchainError(RuntimeError): ...

def find_node() -> str         # shutil.which("node"); raise OfflineToolchainError
def find_esbuild() -> str      # TANGA_ESBUILD → which("esbuild") → dev/node_modules; raise
def ensure_offline_assets() -> OfflineAssets  # download + build, cached by version hash
def offline_library_js() -> str               # bundled three + Tanga library
def offline_third_party_html() -> str         # marked + katex.js + auto-render + html2canvas
def offline_katex_css() -> str                # katex CSS with base64 fonts
```

`delivery="offline"` raises `OfflineToolchainError` (a `RuntimeError`) when
node/esbuild cannot be found.

## Decisions (confirmed)

- Design B: nothing third-party committed; download + bundle at export time.
- Raise an exception when node/esbuild is missing.
- Cache downloads in `~/.cache/tanga/offline/` (override `TANGA_CACHE_DIR`).
- Keep `js/tanga-viewer.js` + manifest (our CDN bundle).
- Keep NOTICE MIT attribution.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-offline-builder-module.md](./01-offline-builder-module.md) | New `_offline.py` (spec, cache, toolchain check, download, esbuild, KaTeX) |
| 2 | [02-rewire-delivery-path.md](./02-rewire-delivery-path.md) | `_cdn.py` + `_bootstrap/_html.py` offline helpers delegate to `_offline.py` |
| 3 | [03-remove-vendored-assets.md](./03-remove-vendored-assets.md) | Delete `js/three/`, `vendor/`, `tools/vendor-third-party.py` |
| 4 | [04-tests.md](./04-tests.md) | Rewrite offline tests + toolchain-error test (skipif no node/esbuild) |
| 5 | [05-ci-precommit.md](./05-ci-precommit.md) | Remove vendored drift gates; add offline smoke job |
| 6 | [06-docs-changelog.md](./06-docs-changelog.md) | Example docs, architecture doc, NOTICE, changelog |

## Testing as you go

```bash
uv run pytest py/tests/viz -q
uv run ruff check py/pytanga/viz py/tests/viz
uv run python tools/build-viewer-js.py --check
uv run mkdocs build --strict
```

## Non-goals

- No change to `delivery="cdn"` / `"inline"` (still reference/inline `js/tanga-viewer.js`).
- No npm publish.
- No minification of the offline bundle.
