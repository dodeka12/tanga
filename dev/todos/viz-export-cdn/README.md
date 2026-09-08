# Viz export CDN delivery — Overview

**Created:** 2026-09-07 | **Status:** Done | **Branch:** `feat/viz-export-cdn`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Ship the viewer runtime — the ~136 KB of concatenated renderer + shared JS that
`generate_bootstrap_js` currently inlines into every export — as a single
committed ES module (`js/tanga-viewer.js`) served from jsDelivr's GitHub CDN.
Exports then reference that bundle by version tag instead of embedding it, so a
standalone HTML file produced by an older release keeps loading the matching
library forever.  Three delivery modes:

- `delivery="cdn"` (default) — Tanga library + Three.js + marked + KaTeX +
  html2canvas load from jsDelivr (smallest HTML, needs internet to view).
- `delivery="inline"` — Tanga library inlined; third-party assets still CDN.
- `delivery="offline"` — everything inlined (Tanga library + a bundled Three.js
  + marked + KaTeX with base64 fonts + html2canvas) for a truly self-contained
  file (~2–3 MB, no internet to view).

`display_snapshot()` uses CDN by default.

## Architecture (short)

- Split the export bootstrap into a **library** layer and a **scene adapter**.
  The library concatenates `_RENDERER_FILES` + `_SHARED_JS_FILES` (imports
  stripped, exactly as today), imports `three`/`three/addons`, injects the SDF
  shaders and a no-op `sendLog`/`sendEvent` stub, then exposes a stable
  `window.__tanga` bridge.
- The adapter is the scene-specific code that `export/_html.py`,
  `_figure_html.py`, and `_animated_figure.py` already generate; it now
  destructures its runtime + API from `window.__tanga` instead of relying on a
  single concatenated scope.
- `delivery="cdn"` emits
  `<script type="module" src="https://cdn.jsdelivr.net/gh/dodeka12/tanga@<ref>/js/tanga-viewer.js"></script>`;
  `delivery="inline"` inlines the identical library text.  The adapter
  `<script type="module">` is byte-for-byte the same in both modes.

### Fixed contract

Python API (keyword-only additions; all default to CDN):

```python
DeliveryMode = Literal["cdn", "inline", "offline"]   # py/pytanga/viz/export/_cdn.py

viz.export_snapshot(path, *, overwrite=False, animation=None, anim_style=None,
                    theme=None, delivery="cdn", delivery_ref=None)
viz.export_figure(path=None, *, style=None, overwrite=False, animation=None,
                  anim_style=None, theme=None, delivery="cdn", delivery_ref=None)
viz.display_snapshot(width="100%", height="500px", *, scene_name="",
                     delivery="cdn", delivery_ref=None)

render_snapshot(objects, scene_config, theme="dark", delivery="cdn", delivery_ref=None)
render_figure(objects, scene_config, figure_style, figure_config, theme="dark",
              delivery="cdn", delivery_ref=None)
render_export_animated_figure(..., delivery="cdn", delivery_ref=None)
render_export_animated_html(..., delivery="cdn", delivery_ref=None)
```

`delivery_ref` overrides the jsDelivr `@version` segment: a tag (`v1.17.0`), a
branch (`feat/view-architecture`), or a commit hash.  When omitted it is derived
from `importlib.metadata.version("tanga-py")` → tag (`1.17.0` → `v1.17.0`,
`1.17.0rc3` → `v1.17.0-rc3`); dev/local versions have no tag and raise a clear
`ValueError` telling the caller to pass `delivery_ref`.

Library bundle (`js/tanga-viewer.js`):

- ES module; imports `three` + `three/addons` (resolved by the page's import map).
- Sets `window.__tanga` to at least:
  `THREE, OrbitControls, CSS2DRenderer, CSS2DObject, Line2, LineSegments2,
  LineMaterial, LineGeometry, LineSegmentsGeometry, buildSceneObject,
  buildOverlay, fitCamera, orthoFrustum, finiteAspect`.

Vendored offline assets (`py/pytanga/viz/templates/vendor/`, shipped in the
wheel): a self-contained `tanga-viewer.offline.js` (esbuild-bundled Three.js +
addons + Tanga library), `marked.min.js`, `html2canvas.min.js`, and a `katex/`
directory whose `katex.offline.css` base64-embeds the fonts.  `delivery="offline"`
inlines all of these so the output needs no network to view or generate.

Each committed bundle ships with a content-addressed manifest (the ordered
source-file list, per-file sha256, a generator hash, and the fingerprint).
`tools/build-viewer-js.py` rebuilds only when that fingerprint changes;
`--check` verifies the committed bundle still matches its sources.

## Decisions (confirmed)

- Use the **`gh`** jsDelivr endpoint (tags + branches + commits; no npm publish).
- Use the **`window.__tanga` global bridge** so the adapter is identical in every
  mode and avoids remote named-export plumbing.
- Commit the CDN bundle (`js/tanga-viewer.js`), the offline bundle, and vendored
  third-party assets, and add CI drift gates; publish the bundle at every git
  tag (tags are immutable on jsDelivr).
- `delivery` is three-valued: `"cdn"` (default) → `"inline"` → `"offline"`.
- Offline assets are vendored into the wheel at build time so
  `delivery="offline"` needs no network to generate or view.
- Use esbuild (devDependency) only for the committed offline bundle; the live
  WebSocket viewer remains zero-build.
- Rebuild bundles via a content-addressed manifest (ordered source list +
  per-file sha256 + generator hash), committed alongside each bundle, and gate
  on `--check` in pre-commit + CI.
- Inject a no-op `sendLog`/`sendEvent` stub (fixes the dangling
  `import { sendLog } from '../events.js'` that `_strip_imports` removes today).
- `display_snapshot` also uses CDN by default (smaller data-URL IFrame).
- Add MIT attribution for three/marked/katex/html2canvas to `NOTICE`.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-library-bundle-extraction.md](./01-library-bundle-extraction.md) | Split `generate_bootstrap_js` into library + adapter; `window.__tanga` bridge; `sendLog` stub |
| 2 | [02-bundle-build-and-cdn-resolver.md](./02-bundle-build-and-cdn-resolver.md) | Incremental hash/manifest `build-viewer-js.py`, commit bundle + manifest, `_cdn.py` |
| 3 | [03-vendor-third-party-and-offline-bundle.md](./03-vendor-third-party-and-offline-bundle.md) | Vendor Three.js/marked/KaTeX/html2canvas + esbuild offline bundle |
| 4 | [04-delivery-api-and-templates.md](./04-delivery-api-and-templates.md) | Thread `delivery`/`delivery_ref`; templates emit cdn / inline / offline |
| 5 | [05-cdn-failure-detection-and-tests.md](./05-cdn-failure-detection-and-tests.md) | Failure banner + delivery-mode tests + smoke |
| 6 | [06-ci-drift-check.md](./06-ci-drift-check.md) | Pre-commit + CI `--check` drift gates for bundles + vendored assets |
| 7 | [07-docs-changelog.md](./07-docs-changelog.md) | Example docs + architecture doc + NOTICE + changelog |

## Testing as you go

```bash
uv run pytest py/tests/viz -q
uv run ruff check py/pytanga/viz py/tests/viz tools/build-viewer-js.py tools/vendor-third-party.py
node --check js/tanga-viewer.js                       # after phase 2
uv run python tools/build-viewer-js.py --check        # after phase 2
node --check py/pytanga/viz/templates/vendor/tanga-viewer.offline.js   # after phase 3
uv run python tools/vendor-third-party.py --check     # after phase 3
uv run python tools/generate-example-docs.py --check  # after phase 7
uv run mkdocs build --strict                          # after phase 7
```

## Non-goals

- No npm publish (the CDN uses the `gh` endpoint; esbuild is build-only).
- No change to the live (WebSocket) viewer or its module graph; only the export
  packing path changes.
- glTF/GLB, PNG, MP4 export paths unchanged.
- No retroactive rebuild of already-released tags.
