# pytanga.viz issue report: `VisualizerApp` + `SplitView` + `CoordinateSystem` — duplicate grid/axes and non-fitting 2D camera

Status: report for upstream (pytanga) filing. No code changes applied in `fpk-viz` for this
issue; this is a read-only analysis produced on request.

`pytanga-py` version: 1.11.0 (confirmed via `uv pip show tanga-py`).

## Use case

An app subclasses `pytanga.viz.VisualizerApp` and shows a `SplitView` layout with three
panes: two 2D line-plot panes built from `CoordinateSystem`, plus one "main" pane showing the
live 2D scenario (draggable `ActPoint`s, circles, and paths). Dragging an endpoint rebuilds
the scenario and re-plots both graphs live. See
[src/examples/smart_viz_risk_playground.py](../../src/examples/smart_viz_risk_playground.py)
for the full source; the relevant parts are reproduced below.

```python
class SmartVizRiskPlayground(VisualizerApp):
    def __init__(self) -> None:
        super().__init__(title="smart_viz risk playground", space_dim=2, reuse_existing=False)
        # Named scenes must exist before run() opens the layout (SceneView looks them up by
        # name when the browser connects), so they're created here rather than in init().
        self._overlap_scene = self.viz.scene("overlap_plot")
        self._risk_scene = self.viz.scene("risk_plot")
        self._layout = SplitView(
            "horizontal",
            [
                SplitView("vertical", [SceneView("overlap_plot"), SceneView("risk_plot")]),
                SceneView(""),
            ],
        )
        ...

    def run(self, *, wait_for_browser: bool = True, timeout: float = 30.0) -> None:
        ok = self.viz.show(layout=self._layout, wait_for_browser=wait_for_browser)
        ...
        asyncio.run(self._app_main())  # calls init(), then the control loop

    async def init(self) -> None:
        ...
        self._overlap_cs = CoordinateSystem(self._overlap_scene, xlim=(0.0, _TOTAL_TIME), ylim=(0.0, 1.0), labels=(...))
        self._overlap_cs.add_plot(self._overlap_area_path, ...)
        self._risk_cs = CoordinateSystem(self._risk_scene, xlim=(0.0, _TOTAL_TIME), ylim=(0.0, 1.05), labels=(...))
        self._risk_cs.add_plot(self._hazard_rate_path, ...)
        self._risk_cs.add_plot(self._cumulative_risk_path, ...)
        self._recompute_and_redraw(...)
```

Two visual problems show up in the two `CoordinateSystem`-backed panes (`overlap_plot`,
`risk_plot`) once the app is actually run in a browser:

1. Each pane shows a generic default grid *and* axes underneath the `CoordinateSystem`'s own
   (correctly-scaled) grid and axes — a visible duplication.
2. The 2D camera in each pane does not auto-fit to the plot's `xlim`/`ylim` bounds, even
   though `CoordinateSystem`'s default `camera="auto"` is designed to do exactly that.

## Root cause analysis (via source inspection of the installed 1.11.0 package)

### 1. Duplicate grid/axes

- `Visualizer.scene(name)` — used by `self.viz.scene("overlap_plot")` / `self.viz.scene("risk_plot")`
  in `__init__` — calls `self._add_default_scene_objects(name)` for **every** newly created
  scene, main or named.
- `_add_default_scene_objects` adds a generic `Axes2D(range_u=(-5,5), range_v=(-5,5))` and
  `Grid(range_u=(-5,5), range_v=(-5,5))` whenever the visualizer-wide `add_default_axes` /
  `add_default_grid` flags are true. Both default to `True`.
- `VisualizerApp.__init__` does **not** expose `add_default_axes` / `add_default_grid` at all
  (unlike the raw `Visualizer.__init__`, which does). It only forwards `port`, `host`,
  `open_browser`, `reuse_existing`, `title`, `annotation`, `background_color`, `camera`,
  `space_dim`, `enable_server_stop_key` to the underlying `Visualizer`. So there is currently
  **no constructor-level way**, from a `VisualizerApp` subclass, to suppress the default
  grid/axes on any scene, including plot-only scenes created purely to host a
  `CoordinateSystem`.
- `CoordinateSystem.__init__` then draws its own `grid=True, axes=True` (defaults), scaled to
  the caller's `xlim`/`ylim`, in the same scene — on top of the generic defaults above.

### 2. Camera not auto-fitting

- `CoordinateSystem.__init__` calls `_recompute_camera_ownership()`, which grants
  `self._owns_camera = True` when `space_dim == 2`, no explicit `size=` was given, and
  (`camera is True`) or (`camera == "auto"` and `scene.config.camera is None`). This condition
  is satisfied here, since a freshly created named scene starts with `config.camera is None`.
- With ownership granted, `_apply_camera()` computes a `View2DConfig` fit exactly to
  `xlim`/`ylim` and calls `VizSceneHandle.set_camera(cam)` →
  `Visualizer.set_camera(camera, scene_name=...)`, which sets `scene.config.camera` and calls
  `self._push_scene_config(scene_name)`.
- The ordering problem: `VisualizerApp.run()`'s override calls
  `self.viz.show(layout=self._layout, wait_for_browser=True)` *first* — this registers/serializes
  the layout (`Visualizer.set_layout` → `serialize_layout`, called once) and is presumably also
  when each pane first establishes its rendering/camera state. Only afterward does
  `asyncio.run(self._app_main())` invoke `init()`, where the `CoordinateSystem`s are actually
  constructed and `_apply_camera()` / `set_camera()` run — i.e., the auto-fitted camera is
  computed and pushed only *after* the "overlap_plot"/"risk_plot" panes already exist and are
  rendering with whatever default camera they started with.
- `SceneView._serialize()` does *not* embed a camera snapshot when no explicit `camera=` is
  passed to `SceneView(...)` (it only serializes `"camera"` if `self.camera is not None`), so
  this isn't simply "frozen at layout-serialize time" — the pane is meant to read the scene's
  own (live) camera. But it's unclear from the Python source alone whether a *later*
  `set_camera()` / `_push_scene_config()` call (issued after the pane already exists, as
  happens here) is actually re-applied to an already-initialized pane's camera by the
  frontend, or whether only the dedicated runtime API `Visualizer.set_view_camera(view,
  camera)` (documented in `layouts.md`'s `on_topdown` example) is guaranteed to retarget an
  already-open pane. This final step lives in frontend JS that wasn't inspected as part of
  this analysis.

## What initialization flow would suit this use case

For an app like this (`VisualizerApp` subclass + `SplitView` layout + one or more
`CoordinateSystem`-backed plot panes), the flow that would avoid both problems above would be
one where:

1. **Plot-only scenes can opt out of default grid/axes at creation time**, e.g. either:
   - `Visualizer.scene(name, *, add_axes=False, add_grid=False)` exposing the existing
     (currently private/internal-only) per-call override that `_add_default_scene_objects`
     already supports internally, or
   - `VisualizerApp.__init__` forwarding `add_default_axes` / `add_default_grid` like the raw
     `Visualizer.__init__` already does, so an app-level default can be set once for scenes
     meant to host a `CoordinateSystem` (which draws its own grid/axes) instead of the
     generic placeholder ones.
2. **`CoordinateSystem`'s camera auto-fit is guaranteed to apply regardless of whether the
   scene is already showing in a `SplitView` pane at construction time** — either by:
   - Documenting/guaranteeing that `set_camera()` after the pane already exists is picked up
     live by any pane with no per-pane `camera=` override (if that's already the intended
     contract, then the bug is a frontend gap, not an API gap), or
   - Providing an ergonomic way to construct `CoordinateSystem` (or at least compute/apply its
     fitted camera) *before* `VisualizerApp.run()`/`Visualizer.show(layout=...)` is called, so
     the fitted `View2DConfig` can be embedded directly into `SceneView(name, camera=...)` at
     layout-construction time — the same mechanism already used for explicit per-pane camera
     overrides in the docs (`layouts.md`). This would require exposing the fit computation
     (`xlim`/`ylim` → `View2DConfig`) independently of constructing a full `CoordinateSystem`
     bound to a scene handle, since today `CoordinateSystem.__init__` requires a scene/handle
     and eagerly draws content, which in this app's flow isn't available until `init()` (i.e.,
     after the layout is already shown).

In short: the app would like to build "the same plots, but embedded in a `SplitView` pane
whose initial camera is exactly right and whose scene has no dueling default grid/axes",
without needing to defer all `CoordinateSystem` construction to a point where the layout (and
each pane's camera) has, by app-lifecycle necessity (`run()` → `show(layout=...)` before
`init()`), already been sent to the browser.

## Reference source locations (installed 1.11.0, for filing upstream)

- `Visualizer.scene`, `Visualizer._add_default_scene_objects`, `Visualizer.set_camera`,
  `Visualizer.set_layout` — `pytanga/viz/visualizer.py`
- `VisualizerApp.__init__` — `pytanga/viz/app.py` (module inferred from
  `inspect.getmodule`; forwards a narrower parameter set than `Visualizer.__init__`)
- `CoordinateSystem.__init__`, `_recompute_camera_ownership`, `_apply_camera` —
  `pytanga/viz` coordinate-system module
- `SceneView.__init__`, `SceneView._serialize`, `serialize_layout` —
  `pytanga/viz/views.py`
