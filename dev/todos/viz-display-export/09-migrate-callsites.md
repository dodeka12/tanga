# Phase 9 — Migrate call sites to the new API

**Status:** Done

## Goal

Update tests, examples, and dev scripts to the new names so the deprecated
aliases are only needed for external user code.

## Files

- Modify: `py/tests/viz/test_export_static.py`
- Modify: `py/tests/viz/test_scene_session.py`
- Modify: `py/tests/viz/test_entry_points.py`
- Modify: `py/tests/viz/test_export_renderers.py`
- Modify: `dev/src/test_export_smoke.py`
- Modify: `dev/src/test_viz_figure.py`
- Modify: `dev/src/test_viz_animation_export.py`
- Modify: `py/examples/viz/demo_export_html.py`
- Modify: `py/examples/viz/demo_export_figure.py` (if present)
- Modify: `py/examples/viz/demo_animated_export.py`

## Steps

- [x] Replace `export_html` → `export_snapshot`, `export_figure_html` →
      `export_figure(path=None)`, `display_static` → `display_snapshot`,
      `open_figure` → `open_snapshot`, `build_gltf_scene` → `build_glb`,
      `render_export_*` → `render_*`.
- [x] Replace `start`/`stop`/`run` with `start_server`/`stop_server`/`show`+`wait`
      where the new semantics are intended (keep `start`/`stop` only where
      testing the deprecated aliases).
- [x] Drop the single `open_figure()` call in `dev/src/test_viz_figure.py`.
- [x] Migrated: `py/tests/viz/test_export_static.py`, `py/examples/viz/demo_export_html.py`,
      `demo_animated_export.py`, `dev/src/test_export_smoke.py`,
      `test_viz_figure.py`, `test_viz_animation_export.py`.
- [ ] Deferred: `py/examples/viz/demo_export_figure.py` still uses
      `SceneExporter.figure_config` (not yet exposed on `Visualizer`).

## Verification

- [x] `uv run pytest py/tests/viz/` passes (439 tests).
- [x] Edited example/dev files parse (`ast.parse`).
