# Phase 8 — Demote `SceneExporter` to deprecated aliases

**Status:** Done

## Goal

`SceneExporter` currently owns the `export_*`/`open_*` methods. After Phases
4–6 those methods also exist on `Visualizer`/`VizSceneHandle`. Turn
`SceneExporter` into a thin deprecated wrapper delegating to the visualizer,
so `SceneExporter(viz).export_html(...)` keeps working.

## Files

- Modify: `py/pytanga/viz/export/_exporter.py`
- Modify: `py/pytanga/viz/export/__init__.py` (if re-exported)

## Steps

- [x] Emit `DeprecationWarning` from `SceneExporter.__init__` recommending the
      direct `viz`/`viz.scene(name)` API.
- [x] `SceneExporter.open_figure` was already removed/aliased in Phase 4
      (`open_snapshot`).
- [x] Methods already route through `self._viz` (kept as-is to avoid subtle
      behavior regressions in `_default_figure_style`/`_resolve_export_path`).

## Unit tests

- [x] `py/tests/viz/test_export_static.py`: `SceneExporter(viz)` emits
      `DeprecationWarning`.
- [x] `dev/src/test_export_smoke.py` / `dev/src/test_viz_figure.py` keep
      working via the deprecated aliases.

## Verification

- [x] `uv run pytest py/tests/viz/` passes (439 tests).
