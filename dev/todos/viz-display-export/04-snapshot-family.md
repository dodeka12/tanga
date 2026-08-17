# Phase 4 — Snapshot family (`export_snapshot` / `open_snapshot` / `display_snapshot` / `render_snapshot`)

**Status:** Planned

## Goal

Rename the static full-page HTML family to the "snapshot" noun:
`export_html` → `export_snapshot`, `open_figure` → `open_snapshot`,
`display_static` → `display_snapshot`, `render_export_html` → `render_snapshot`.

## Files

- Modify: `py/pytanga/viz/export/_html.py`
- Modify: `py/pytanga/viz/export/_exporter.py`
- Modify: `py/pytanga/viz/visualizer.py`
- Modify: `py/pytanga/viz/_scene_handle.py`
- Modify: `py/pytanga/viz/export/__init__.py`

## Steps

- [ ] Rename `render_export_html` → `render_snapshot`; add deprecated alias
      `render_export_html`.
- [ ] Rename `SceneExporter.export_html` → `export_snapshot`; add alias.
- [ ] Rename `SceneExporter.open_figure` → `open_snapshot` (repurposed to open
      the standalone full-page snapshot); add alias `open_figure`.
- [ ] Add `Visualizer.export_snapshot(path, *, overwrite=False)` and
      `Visualizer.open_snapshot()` (temp file + `webbrowser.open`).
- [ ] Rename `Visualizer.display_static` → `display_snapshot` (logic already
      fixed in Phase 1); add alias `display_static`.
- [ ] Add matching delegators on `VizSceneHandle`.
- [ ] Update `export/__init__.py` `__all__`.

## Unit tests

- [ ] `py/tests/viz/test_export_static.py`: update imports/calls to
      `render_snapshot`.
- [ ] `py/tests/viz/test_display.py`: `display_snapshot()` (and alias
      `display_static()`) return the iframe.
- [ ] `py/tests/viz/test_export_renderers.py`: `render_export_html` alias
      equals `render_snapshot`.

## Verification

- [ ] `uv run pytest py/tests/viz/test_export_static.py py/tests/viz/test_display.py py/tests/viz/test_export_renderers.py` passes.
