# Changelog

## [Since 1.12.0] — 2026-08-31
- Scrollable `StackView`/`GroupView` panes (`scrollable=True` + custom scrollbar) · horizontal-toolbar example
- Breaking: banner `on_close` now receives the control value, not the banner id
- Bug fixes: `FileChooserView` selected-path write-back & `root=` clamp · `controls_define` no longer wipes layout-view controls · banner button clicks dispatch
- Refactor: unified `(id, event)` control/interaction registry · single control model · single event envelope & dispatch tail
→ [Details](2026-08-31_7848e4a2.md)

## [Since 1.11.1] — 2026-08-31
- Scene-scoped `alert`/`confirm`/`update_control` on `VizSceneHandle` · `Visualizer.scene(add_axes=…, add_grid=…)` · `fit_view2d()` camera helper · `ActSceneObject.drag_anchor()` ideal-drag hook
- Breaking: deprecated `Visualizer`/`VisualizerApp` `port`/`host`/`open_browser` constructor params removed
- Bug fixes: server lifecycle no longer corrupts global state · `update_entity` re-applies rotation & creation-only geometry · per-pane pointer interaction and 2D aspect ratio
→ [Details](2026-08-31_3ea3a8ab.md)

## [Since 1.11.0] — 2026-08-30
- Docs restructured to mirror the example topic layout: GA reference under `docs/py/ga/` · viz docs regrouped into `app/`·`entities/`·`plotting/`·`interaction/`·`labels/`·`styling/`·`sdf/` · new reference page for every declarative `xxxView` control
- Bug fixes: `update_label` now works on entity refs with attached labels
→ [Details](2026-08-30_83af75c1.md)

## [Since 1.10.1] — 2026-08-30
- Editable table control (`add_table` / `TableView`) with per-change async handlers · unified, tighter camera auto-fit shared by live viewer + HTML export
- Bug fixes: standalone HTML export now renders KaTeX math labels
→ [Details](2026-08-30_bd929aad.md)

## [Since 1.10.0] — 2026-08-29
- Searchable example docs gallery: every `py/examples/` example gets a keyworded docs page (with full source) under a new top-level "Examples" nav section · `dev/workflows/example-docs.md` + cline rule
→ [Details](2026-08-29_f2359f9e.md)

## [Since 1.9.1] — 2026-08-28
- Wireframe dash-pattern and control `View` classes re-exported from `pytanga.viz` · viz docs/examples corrected to match the public API
→ [Details](2026-08-28_c050a11d.md)

## [Since 1.9.0] — 2026-08-28
- Documentation fixes: `Inversion(center=…, radius=…)` example · precompiled-wheel binding list (seven bindings) · `Geometry` `BasisXX`-only restriction
- Bug fixes: `GeneralRotor` label frame no longer dereferences a missing `.rotor`
→ [Details](2026-08-28_020ee37f.md)

## [Since 1.8.0] — 2026-08-27
- In-place control value updates (`set_control_value` · `set_control_view_value` · `control_update`) · value-edit stepper control (`add_value_edit` / `ValueEditView`)
- Breaking: control `default` field renamed to `value` (no alias kept)
→ [Details](2026-08-27_0041385d.md)

## [Since 1.7.0] — 2026-08-27
- New interactive controls (`add_text_field` · `add_text_area` · `add_color_picker` · `add_checkbox`) · button icons + icon model · control tooltips · reusable text editor (`open_editor`) · `ActPoint` drag-mode constraint
→ [Details](2026-08-27_265517f8.md)

## [Since 1.6.0] — 2026-08-26
- Extra visualization-only geometry entities (`Disk`/`PartialDisk`/`Box`/`Ellipsoid`/`Ellipse`/`RegularPolygon`) · mesh + SDF style classes and Three.js renderers · new `partialDisk`/`regularPolygon` SDF primitives · analytic SDF silhouette edge anti-aliasing (`SdfStyle.antialias`, off by default)
→ [Details](2026-08-26_c798944f.md)

## [Since 1.5.0] — 2026-08-26
- Awaitable flush (`flush_async`) + blocking `flush(wait=True)` · banners/dialogs (`show_banner`/`alert`/`confirm`, modal + per-scene) · compute offload to the user loop (`submit_user`/`run_user`) · slider `on_press`/`on_release` · file chooser with a backend-driven file browser
→ [Details](2026-08-26_d870e5be.md)

## [Since 1.4.0] — 2026-08-26
- `ActPoint` drag lifecycle handlers (`on_drag_start` / `on_drag_end`) · `ActPoint` label support · `clear(add_axes=, add_grid=)` re-add options
- Bug fixes: 2D pointer interaction (stale camera + orthographic drag scale) · removing an entity now removes its attached labels
→ [Details](2026-08-26_a074adb3.md)

## [Since 1.3.0] — 2026-08-25
- WebGL2 SDF viewer (`SdfVisualizer`) · SDF primitive/combinator GLSL library · analytic entity→SDF serializer · SDF objects in the standard viewer (proxy renderer, `Composed`/`SdfGroup`, per-object CSG + materials) · `SdfObject`/`Combine` + `ECompose` operator object model · per-entity `Sdf*Style` classes · configurable lighting + grid/axes overlays
- Bug fixes: inverted SDF rotations · patchy lighting normals · SDF browser connect/reconnect parity
→ [Details](2026-08-25_cbc7adc7.md)

## [Since 1.2.0] — 2026-08-25
- Per-frame camera playback in animated HTML export · default 2D view now uses an orthographic camera · HTML export honors the live scene camera · viz examples reorganized into topic subfolders
- Bug fixes: default 2D orthographic camera · HTML export applies the full camera config
→ [Details](2026-08-25_88f3e3d9.md)

## [Since 1.1.0] — 2026-08-25
- CoordinateSystem inner data group (`cs.data_group` + `to_data`) · `vline`/`hline`/`line`/`point` annotation helpers (create-or-update by name + `remove_*`)
→ [Details](2026-08-25_c6f85e08.md)

## [Since 1.0.1] — 2026-08-24
- Split views (`SplitView` panes) · `StackView` + control views (`SliderView`/`ButtonView`/`DropdownView`) · multi-scene WebSocket subscription · per-pane scene cameras · viz-only `Cylinder`/`Arc` entities · `CoordinateSystem` plotting helper
- Bug fixes: standalone HTML export no longer crashes on duplicate renderer helper declarations
→ [Details](2026-08-24_d31afff.md)

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