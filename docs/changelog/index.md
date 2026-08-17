# Changelog

## [Since 0.9.2] — 2026-08-17
- Unified live/export render pipeline (shared `scene-builder.js`) · export consumes `Scene.full_state()` directly · legacy `_serialize_labels()`/`parentId` label path removed
→ [Details](2026-08-17_9774152.md)

## [Since 0.9.2] — 2026-08-17
- `content` aspect for in-place entity updates · single `sceneObjects` frontend registry (legacy path removed)
→ [Details](2026-08-17_ad59e6e.md)

## [Since 0.9.2] — 2026-08-16
- Scene graph (`VizGroup`) · `VizObjectRef` · per-object transforms · aspect patches · overlay `attach_to`
→ [Details](2026-08-16_5877a61.md)

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