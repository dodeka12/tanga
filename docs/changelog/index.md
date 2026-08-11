# Changelog

## [0.5.3] — 2026-08-10

### New Features
- `Circle.normal` now optional, defaults to `Direction(0, 0, 1)`

### Bug Fixes
- Unified WebSocket startup/reconnect flow across all entry points
- Export 2D views as orthographic in standalone HTML
- Render title overlays with KaTeX in HTML exports and live viewer
- Include `PointPath` renderer in HTML/glTF exports

### Doc Changes
- Added `viz-websocket-startup-fix.md` planning document

→ [Full changelog](2026-08-10_4c556d3.md)

## [0.5.2] — 2026-08-10

### New Features
- `ControlEvent` dataclass for extensible control handler metadata
- `get_label_ids(entity_id) → list[str]` for label lookup
- `flush(fit_camera=True)` for explicit camera auto-fit

### Bug Fixes
- Unified browser connection detection across all startup paths
- Fixed browser timeout when GPU crashes during WebGL init
- Fixed orbit target drifting away from world origin
- Fixed sphere flickering in animations (float epsilon rebuilds)
- Added missing `reflection_point.js` renderer
- `add()` return type simplified to `str | list[str]`

### Doc Changes
- Updated `visualizer.md` and `interactive.md` for new APIs
- Replaced bare style parameters with style classes in examples
- Replaced unicode subscripts with KaTeX math in example labels

→ [Full changelog](2026-08-10_d9ffba4.md)