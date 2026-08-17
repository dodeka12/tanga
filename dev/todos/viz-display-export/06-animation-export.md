# Phase 6 — Animated export via `animation=` keyword

**Status:** Planned

## Goal

Move the recording factory to `Visualizer`/`VizSceneHandle` and fold the
animated export variants into `export_snapshot(..., animation=rec)` /
`export_figure(..., animation=rec)`. `AnimationRecording` stays unchanged as
the frame store.

## Files

- Modify: `py/pytanga/viz/export/_animated_figure.py`
- Modify: `py/pytanga/viz/export/_exporter.py`
- Modify: `py/pytanga/viz/visualizer.py`
- Modify: `py/pytanga/viz/_scene_handle.py`

## Steps

- [ ] Rename `render_export_animated_html` → `render_snapshot(animation=…)`
      and `render_export_animated_figure` → `render_figure(animation=…)`;
      add deprecated aliases for the old names.
- [ ] Add `Visualizer.start_animation_recording()` returning
      `AnimationRecording(self._scene, styles_map=self.styles.kind)`.
- [ ] Add `VizSceneHandle.start_animation_recording()` for its scene.
- [ ] Extend `export_snapshot(path, *, animation=None, anim_style=None, …)`
      and `export_figure(path=None, *, animation=None, anim_style=None, …)` to
      render via the animated path when `animation` is set.
- [ ] Add deprecated aliases `export_animated_html` / `export_animated_figure`
      on `SceneExporter`.

## Unit tests

- [ ] `py/tests/viz/test_export_renderers.py`: old `render_export_animated_*`
      aliases match new `render_snapshot`/`render_figure` with `animation=`.
- [ ] New: `viz.start_animation_recording()` + `capture_frame()` +
      `export_snapshot(..., animation=rec)` writes a file.

## Verification

- [ ] `uv run python dev/src/test_viz_animation_export.py` still works (via
      aliases) and via the new API.
