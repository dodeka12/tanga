# 2D view switch & per-scene space dimension — Overview

**Created:** 2026-09-06 | **Status:** Done | **Branch:** `fix/examples`

## Goal

Make the space dimension of a scene a first-class, **per-scene**,
**switchable** property of the Tanga viewer, and close the 2D-view API gaps
reported in `dev/notes/bugs-in-2-0-0rc1.md`:

- Set `space_dim` when creating a named scene (`viz.scene(name, space_dim=…)`,
  `viz.add_scene(name, space_dim=…)`).
- Switch the dimension at runtime (`viz.set_space_dim(2|3, scene_name=…)` /
  `handle.space_dim = 3`) and have the browser re-apply camera + controls
  without a reload.
- A runnable example that toggles one scene between a flat 2D view and a tilted
  3D view with a `CheckboxView`.
- Fix the broken `py/examples/viz/plotting/multi_plot.py` so it actually shows
  different plots in separate split panes.
- Fix 2D plots clipping in split panes (labels/axes outside the view).

## Architecture (short)

- **Backend** (`visualizer.py`, `_layout.py`, `_scene_handle.py`): `space_dim`
  already lives on `SceneConfig` and is pushed by `_push_scene_config`; the
  missing pieces are (a) a per-scene creation parameter and (b) a runtime
  setter that mutates `scene.config` and re-pushes. `Visualizer._create_scene`
  is the single choke point that builds a named scene's `SceneConfig`.
- **Frontend** (`templates/views/three-view.js`, `templates/view_mode.js`):
  `_applySceneConfig` already re-applies camera/controls/space-dim on every
  `scene_config` message. The only gap is `switchToCamera`'s default branch,
  which creates an ortho camera for `spaceDim === 2` but never re-creates a
  perspective camera when switching back to `spaceDim === 3`.
- **2D split fit**: the full-view case works because `CoordinateSystem` owns
  the camera with `border_px=60` (label margin). The split-view pattern embeds
  a camera via `fit_view2d(...)`, whose `border_px` defaulted to `0.0` — no
  margin, so CSS2D axis labels (fixed-pixel offsets beyond the axes) and the
  axes themselves get clipped. Fixing `fit_view2d`'s default to `60.0` makes
  per-pane cameras consistent with the full-view case.

## Decisions (confirmed)

- **New public API** (fixed up front):

  ```python
  viz.scene(name, *, space_dim=None, enable_server_stop_key=False,
            add_axes=True, add_grid=True) -> VizSceneHandle
  viz.add_scene(name, *, space_dim=None, add_axes=True, add_grid=True) -> VizSceneHandle
  viz.set_space_dim(space_dim, *, scene_name="", camera=None) -> None

  handle.space_dim            # int property (get/set)
  handle.set_space_dim(dim, camera=None)
  ```

  `space_dim` is `2 | 3 | None`; `None` means "inherit the visualizer default".

- **`set_space_dim` camera rules**: if `camera` is given, it is normalized via
  `_normalize_camera_config`; if `_deduce_space_dim(camera)` disagrees with
  `space_dim`, raise `ValueError`. If `camera` is omitted and the scene's
  current camera dimension disagrees with `space_dim`, clear it to `None`
  (frontend auto-fits). Always `_push_scene_config(scene_name)`.

- **Frontend**: extend `switchToCamera` with a symmetric default branch —
  `spaceDim === 3 && camera.isOrthographicCamera` replaces the camera with a
  default perspective camera (`position (6, 4.5, 7.5)`, lookAt origin, fov 50).

- **`fit_view2d`** default `border_px` becomes `60.0` (matches
  `CoordinateSystem`'s own default), so `SceneView(..., camera=fit_view2d(...))`
  pans get label margins. `View2DConfig.border_px` keeps its `0.0` default
  (raw input spec).

- **Examples**: new example lives at `py/examples/viz/camera/switch_2d_3d.py`
  (plain script, blocking tail guarded by `if __name__ == "__main__":` so a
  smoke test can import it). `py/examples/viz/plotting/multi_plot.py` is
  rewritten as three 2D plots in three split panes.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-backend-space-dim-api.md](./01-backend-space-dim-api.md) | Per-scene `space_dim` + `set_space_dim` + handle accessor |
| 2 | [02-frontend-default-3d-switch.md](./02-frontend-default-3d-switch.md) | `switchToCamera` default perspective branch |
| 3 | [03-fit-view2d-border-default.md](./03-fit-view2d-border-default.md) | `fit_view2d` default `border_px=60` |
| 4 | [04-switch-2d-3d-example.md](./04-switch-2d-3d-example.md) | Checkbox 2D/3D switch example |
| 5 | [05-multi-plot-example.md](./05-multi-plot-example.md) | Fix `multi_plot.py` split-pane plots |
| 6 | [06-docs-changelog.md](./06-docs-changelog.md) | Example docs + changelog |

## Testing as you go

```bash
uv run pytest py/tests/viz -q
uv run ruff check py/pytanga/viz py/examples/viz/camera py/examples/viz/plotting py/tests/viz
node --check py/pytanga/viz/templates/view_mode.js
uv run python tools/generate-example-docs.py --check
uv run mkdocs build --strict
```

## Non-goals

- Not touching `templates/controls-panel.js` extraction (a separate bug in
  `bugs-in-2-0-0rc1.md`).
- Not swapping a scene's default `Axes2D`/`Axes3D`/`Grid` objects when
  `space_dim` changes at runtime (switching changes camera mode/controls, not
  retroactively the already-added default objects).
- Not changing the export/static snapshot path beyond what the `fit_view2d`
  default change implies.
