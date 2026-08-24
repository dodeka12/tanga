# Changelog

## [Since 1.0.0] — 2026-08-24
- `VisualizerApp` shutdown (opt-in Ctrl+Q + `request_shutdown()`) · PGA3/PGA2 `dual`/`undual` Hodge-star sign fixes · blade-name parsing sign fix (`e31` → `-e13`)
- Bug fixes: canonical bivector attributes on 3D-space bases
→ [Details](2026-08-24_b7423f2.md)

## [Since 0.13.0] — 2026-08-22
- `show()` in Jupyter · idempotent `display()`/`show()` · scene context managers · `animate(auto_clear=True)` · `viz(...)` shorthand · viz docs restructure · multi-scene guide · browser full-server stop key · operator visualizations reworked
- Breaking: `animate()` no longer opens the viewer · PGA2/PGA3 `meet`/`join` inverted (Gunn/Dorst) · `e0_inv` → `e0_recip`
→ [Details](2026-08-22_fae3c1e.md)

## [Since 0.12.0] — 2026-08-21
- Per-scene browser interrupt key (`animate(stop_key=...)`, default `q`) · `KeyModifier` enum
- Breaking: `animate()` no longer stops the server on loop exit (teardown moves to the `atexit` hook)
→ [Details](2026-08-21_3b2483e.md)

## [Since 0.11.0] — 2026-08-20
- `Variable`/`Expression` symbolic layer · vectorized batch MV↔tensor conversion · expression inverse/`lstsq`/`svd` · `AffineExpression` · repeated-variable polynomial terms · geometry-derived variable masks · interruptible animation loops
- Bug fixes: snapshot export default camera now matches the live view
→ [Details](2026-08-20_0f11790.md)

## [Since 0.10.0] — 2026-08-20
- Bug fixes: macOS (Apple Clang/libc++) wheel build fails with an ambiguous `operator-` — the generic multivector `operator+`/`operator-` templates are now SFINAE-constrained so they no longer clash with std iterator subtraction via ADL
→ [Details](2026-08-20_8270b99.md)

## [Since 0.10.0] — 2026-08-19
- `meet` operator · `blade_join` renamed to `join` (meet exposed as `meet`) · Windows MSVC auto-detection for JIT compile (no developer shell required)
- Breaking: `LabelStyle.along` for `Circle` now (radius fraction, angle fraction × π) and for `Sphere` (radius fraction, two angle fractions × π)
- Bug fixes: `join` no longer hangs on non-unit blades — projection now uses the conjugate-based pseudo-inverse `conjugate(N) / IP(N, conjugate(N))`
→ [Details](2026-08-19_3745321.md)

## [Since 0.10.0] — 2026-08-18
- Consolidated display/export/serving API (`show`/`wait`/`start_server`/`stop_server` · `export_snapshot`/`export_figure`/`export_glb` · `animation=` keyword) · `display_snapshot()` · `display_row(mode="static")` · frontend version check
- Breaking: `open_figure()` → `open_snapshot()`; `Visualizer(port=..., host=...)` deprecated in favor of `start_server(...)`
- Bug fixes: `display_static()`/`display_snapshot()` renders via `<iframe srcdoc>` (no notebook style leakage) · frontend assets served with `Cache-Control: no-cache` · `start_server()`/`show()` default to port 8765 for reconnect
→ [Details](2026-08-18_95486fd.md)

## [Since 0.9.2] — 2026-08-16
- OPNS/IPNS flag on `Algebra.opns` · typed analyzers · MV-accepting constructors · `Geometry.__call__` · random entity generators · macOS compilation + Apple Silicon wheels · extended algebra/MV operators · `MV.prune(tol)` · `Color` enum · entities-module split
- Breaking: per-call `opns` removed · basis geometry methods removed
→ [Details](2026-08-16_7cb2db1.md)

## [0.9.1] — 2026-08-14
- Camera `up` decoupled · `up` config fields · screen-space fat lines (`Line2`)
→ [Details](2026-08-14_3869da1.md)

## [0.9.0] — 2026-08-12
- `View2DConfig` / `ViewPlaneConfig` · `set_camera()` · `Axis` / `Grid` / `Axes2D` / `Axes3D` · default axes+grid
- Breaking: removed `space_extent` / `show_grid` / `show_axes`
- Bug fixes: WebSocket backoff/reconnect · animated HTML export · `add()` returns `str`
→ [Details](2026-08-12_5d757c9.md)

## [0.8.0] — 2026-08-12
- Interactive 3D manipulation · `ActSceneObject` / `ActPoint` · `ActObjectStyle` / `ActPointStyle` · `set_interaction()` / `on_interaction()` · `DragMode`
- Breaking: `Circle` parameter order changed
→ [Details](2026-08-12_4dcfd2d.md)

## [0.5.3] — 2026-08-10
- `Circle.normal` optional (defaults to +z)
- Bug fixes: WebSocket startup/reconnect · 2D orthographic export · KaTeX titles · `PointPath` export renderer
→ [Details](2026-08-10_4c556d3.md)

## [0.5.2] — 2026-08-10
- `ControlEvent` · `get_label_ids()` · `flush(fit_camera=True)`
- Bug fixes: browser connection detection · GPU crash timeout · orbit target drift · sphere flicker · `reflection_point.js` renderer · `add()` returns `str`
→ [Details](2026-08-10_d9ffba4.md)