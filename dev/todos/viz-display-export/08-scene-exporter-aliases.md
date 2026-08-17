# Phase 8 — Demote `SceneExporter` to deprecated aliases

**Status:** Planned

## Goal

`SceneExporter` currently owns the `export_*`/`open_*` methods. After Phases
4–6 those methods also exist on `Visualizer`/`VizSceneHandle`. Turn
`SceneExporter` into a thin deprecated wrapper delegating to the visualizer,
so `SceneExporter(viz).export_html(...)` keeps working.

## Files

- Modify: `py/pytanga/viz/export/_exporter.py`
- Modify: `py/pytanga/viz/export/__init__.py` (if re-exported)

## Steps

- [ ] Rewrite each `SceneExporter` method to delegate to the matching
      `Visualizer` method (or keep bodies but route through `self._viz`).
- [ ] Emit `DeprecationWarning` from `SceneExporter.__init__` recommending the
      direct `viz`/`viz.scene(name)` API.
- [ ] Remove `SceneExporter.open_figure` (superseded by
      `Visualizer.open_snapshot`); keep the name as a module-level alias if
      needed for import compatibility.

## Unit tests

- [ ] `dev/src/test_export_smoke.py` and `dev/src/test_viz_figure.py` still
      pass using `SceneExporter` (deprecated).

## Verification

- [ ] `uv run pytest py/tests/viz/` passes.
