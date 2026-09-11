# Phase 5 — Reproduction example (`py/examples/viz/app`)

## Goal

Add a runnable `VisualizerApp` example that exercises the fixes and serves as a
manual test bed: a horizontal split whose left pane is a vertical split of two
2D plots (`sin`/`cos`) and whose right pane is a 2D view with four `ActPoint`s
joined by lines. The `sin` pane additionally carries an `ActPoint` whose Y
coordinate sets the `sin` amplitude and re-plots the curve.

## Files

- New: `py/examples/viz/app/split_view_app.py`

## Steps

- [x] **5.1 — Create the module with the example-docs header**
  - License header + docstring per `dev/workflows/example-docs.md`: one-line
    `<name>.py — …` description, `Run with:  uv run python py/examples/viz/app/split_view_app.py`,
    and a trailing `Keywords:` line (e.g.
    `app, split view, ActPoint, drag, CoordinateSystem, plotting`).
- [x] **5.2 — Define `SplitViewApp(VisualizerApp)` with `space_dim=2`**
  - `super().__init__(title="…", space_dim=2, add_default_axes=False, add_default_grid=False)`.
  - Create the named scenes before `run()`:
    `self._sin_scene = self.viz.scene("sin")`, `self._cos_scene = self.viz.scene("cos")`.
- [x] **5.3 — Build the layout with embedded fit cameras**
  - `self._layout = SplitView("horizontal", [SplitView("vertical", [SceneView("sin", camera=fit_view2d((0, 2*math.pi), (-1.2, 1.2))), SceneView("cos", camera=fit_view2d((0, 2*math.pi), (-1.2, 1.2)))]), SceneView("", camera=View2DConfig(xmin=-3, xmax=3, ymin=-3, ymax=3))])`,
    using `Size.percent(...)` for the vertical split sizes.
- [x] **5.4 — Override `run()` to open the layout**
  - `self.viz.show(layout=self._layout, wait_for_browser=…)` then
    `asyncio.run(self._app_main())` (the `docs/py/viz/app/layouts.md` pattern),
    with `KeyboardInterrupt` handling and `self.viz.stop_server()` in `finally`.
- [x] **5.5 — Implement `init()`: two `CoordinateSystem`s**
  - `CoordinateSystem(self._sin_scene, xlim=(0, 2*math.pi), ylim=(-1.2, 1.2), labels=("x", "sin(x)"), camera=False)`
    (and the same for `cos`); store them as `self._sin_cs`/`self._cos_cs`.
  - Build a shared `xs = [0.05 * i for i in range(...)]` once.
  - Plot the static `cos` curve via `self._cos_cs.plot(xs, [cos(...)], style=PointPathStyle(line_thickness=2))`.
  - For `sin`, keep a live `PointPath` (`self._sin_path`) in data coordinates
    and register it via `self._sin_cs.add_plot(self._sin_path, style=PointPathStyle(line_thickness=2))`
    so the amplitude point can re-plot by mutating the path and calling
    `update_plots()`.
- [x] **5.6 — Add the amplitude `ActPoint` to the `sin` pane**
  - `self._amp = ActPoint(AMP_X, AMP0, 0.0, drag_mode=DragMode.XY_PLANE)`, added to
    `self._sin_scene` via `self._sin_scene.new(self._amp, color=…, style=PointStyle(size=0.15))`.
  - Register an `on_drag_end` handler that reads the final Y (`ap.point.y`),
    clamps it to `[0.05, 1.5]`, stores it as `self._amplitude`, re-fills
    `self._sin_path` with `(x, amplitude * sin(x))` (using `clear()` then `add(...)`),
    calls `self._sin_cs.update_plots()`, and `self._sin_scene.flush()`.
- [x] **5.7 — Add the four `ActPoint`s + connecting lines to the main scene**
  - Four `ActPoint`s at a quadrilateral's corners, added via
    `self.viz.new(ap, color=…, style=PointStyle(size=0.15))`.
  - Four `Line` entities joining consecutive points (kept as `VizObjectRef`s).
  - A per-point drag `handler` that rebuilds the two adjacent lines from
    `event.world_position` and returns `False` (letting `ActPoint` move + flush).
- [x] **5.8 — Add a non-interactive smoke assertion**
  - Add `py/tests/viz/test_example_split_view_app.py` that constructs
    `SplitViewApp()` without starting the server and asserts: all three scenes
    have `space_dim == 2`, the `sin`/`cos` scenes have no default `Axes2D`/`Grid`,
    the `sin` scene registers exactly one `ActPoint` interaction, and the main
    scene has four `ActPoint`s.

## Validation

`uv run ruff check py/examples/viz/app/ py/tests/viz/test_example_split_view_app.py && uv run pytest py/tests/viz/test_example_split_view_app.py -q && uv run python tools/generate-example-docs.py --check`

## Notes

- `DragMode`, `ActPoint`, `PointStyle`, `PointPath`, `PointPathStyle`,
  `VizObjectRef`, `fit_view2d`, `View2DConfig`, `Size`, `SplitView`, `SceneView`,
  `VisualizerApp`, `Line` (`pytanga.geometry`), `Point` (`pytanga.geometry`) are
  the imports needed.
- The example must be runnable end-to-end (open a browser) but the committed
  validation above must stay non-interactive.
- Because each plot pane embeds its camera via `SceneView(..., camera=fit_view2d(...))`,
  the corresponding `CoordinateSystem` uses `camera=False` to avoid re-owning it.
