# Phase 5 — Figure + glTF export (`export_figure` / `export_glb` / `render_figure` / `build_glb`)

**Status:** Planned

## Goal

Consolidate the figure and glTF export surface: fold `export_figure_html`
into `export_figure(path=None)` (returns a string when no path is given),
rename the low-level renderers, and add `export_figure`/`export_glb` to
`Visualizer`/`VizSceneHandle`.

## Files

- Modify: `py/pytanga/viz/export/_figure_html.py`
- Modify: `py/pytanga/viz/export/_gltf.py`
- Modify: `py/pytanga/viz/export/_exporter.py`
- Modify: `py/pytanga/viz/visualizer.py`
- Modify: `py/pytanga/viz/_scene_handle.py`
- Modify: `py/pytanga/viz/export/__init__.py`

## Steps

- [ ] Rename `render_export_figure` → `render_figure`; add alias.
- [ ] Rename `build_gltf_scene` → `build_glb`; add alias.
- [ ] Change `SceneExporter.export_figure(path, *, style, overwrite)` to accept
      `path=None` and return the snippet string when `None`; add deprecated
      alias `export_figure_html(style=)`.
- [ ] Add `Visualizer.export_figure(path=None, *, style=None, overwrite=False)`
      and `Visualizer.export_glb(path, *, overwrite=False)`; delegators on
      `VizSceneHandle`.
- [ ] Update `export/__init__.py` `__all__`.

## Unit tests

- [ ] `py/tests/viz/test_export_static.py`: `render_figure` import.
- [ ] `py/tests/viz/test_export_renderers.py`: `build_gltf_scene` alias ==
      `build_glb`.
- [ ] New: `export_figure(path=None)` returns a `str`; `export_figure_html`
      alias returns the same.

## Verification

- [ ] `uv run pytest py/tests/viz/` passes.
