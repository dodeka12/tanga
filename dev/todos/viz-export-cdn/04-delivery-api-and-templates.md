# Phase 4 — Delivery option through the Python API + templates

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Thread `delivery` (`"cdn" | "inline" | "offline"`) / `delivery_ref` from every
public export entry point down to the four render functions, and wire the
templates so each mode emits the right scripts and CSS.

## Files

- Edit: `py/pytanga/viz/export/_cdn.py` (extend `build_library_script_tag` for offline)
- Edit: `py/pytanga/viz/export/_html.py`
- Edit: `py/pytanga/viz/export/_figure_html.py`
- Edit: `py/pytanga/viz/export/_animated_figure.py`
- Edit: `py/pytanga/viz/export/_bootstrap/_html.py` (template signatures + third-party inlining)
- Edit: `py/pytanga/viz/export/templates/export_viewer.html`
- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/pytanga/viz/_scene_handle.py`
- Edit: `py/pytanga/viz/export/_exporter.py`
- New: `py/examples/viz/export/export_delivery.py`

## Steps

- [x] **4.1 — `build_library_script_tag` supports offline**
  - cdn → `<script type="module" src="{build_bundle_url(delivery_ref)}"></script>`.
  - inline → `<script type="module">{generate_library_js()}</script>`.
  - offline → `<script type="module">{offline_bundle_text}</script>` (reads the
    vendored `tanga-viewer.offline.js`).
- [x] **4.2 — Third-party inlining helper**
  - Add a helper returning the offline third-party block: inline `marked.min.js`,
    `katex.min.js` + `auto-render.min.js` + `katex.offline.css`,
    `html2canvas.min.js` from `templates/vendor/` (offline only; cdn/inline keep
    the existing CDN `<script>`/`<link>` tags).
- [x] **4.3 — Render functions accept `delivery`/`delivery_ref`**
  - Add the two keyword params to `render_snapshot`, `render_figure`,
    `render_export_animated_figure`, `render_export_animated_html`; pass the
    library script + third-party block to the template helpers.
- [x] **4.4 — Template helpers**
  - `html_fullpage_template`/`html_snippet_template`: add `library_script`,
    `third_party_scripts`, and `import_map` params (import map omitted offline).
  - `export_viewer.html`: add `__IMPORT_MAP__`, `__THIRD_PARTY__`,
    `__LIBRARY_SCRIPT__` placeholders around `__BOOTSTRAP_JS__`.
- [x] **4.5 — `Visualizer` + `SceneHandle` + `SceneExporter` threading**
  - Add `delivery`/`delivery_ref` to `_render_snapshot_html`,
    `_export_scene_snapshot`, `export_snapshot`, `_render_figure_html`,
    `_export_scene_figure`, `export_figure`, `display_snapshot`,
    `_open_scene_snapshot`; then to `_scene_handle.py` `export_snapshot` /
    `export_figure` / `display_snapshot`; `SceneExporter` delegates to defaults.
- [x] **4.6 — Example (all three delivery modes)**
  - Add `py/examples/viz/export/export_delivery.py` that exports the same scene
    via `delivery="cdn"`, `"inline"`, and `"offline"`, printing each output size.
  - Follow `dev/workflows/example-docs.md` (module docstring + `Keywords:`).

## Validation

`uv run pytest py/tests/viz -q && uv run ruff check py/pytanga/viz py/examples/viz/export/html_export.py`

## Notes

- offline mode has no `<script type="importmap">` (the offline bundle is
  import-free); cdn/inline keep the existing import map.
- `open_snapshot`/`display_snapshot` keep working over `file://`/data URLs
  because module `src` / import map are https (same as Three.js today).
