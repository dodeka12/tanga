# Interactive Controls for Tanga 3D Viewer — Implementation Plan

## Overview

Add interactive UI controls (sliders, dropdowns, buttons) to the Tanga 3D
viewer. Controls are defined in Python with async handler callbacks, rendered
as DOM overlays in the Three.js frontend, and communicate via the existing
WebSocket channel.

Controls can be **standalone** (positioned in the viewport) or **attached** to
3D scene objects via CSS2DRenderer (same mechanism as labels). Control groups
provide grouping with a title bar, minimize/restore toggle, and optional
attachment to a 3D object (where the group title doubles as a label).

Controls are **server-only** — they require a running WebSocket server and are
not included in standalone HTML or figure exports.

---

## Implementation Phases

| Phase | Title | Description |
|-------|-------|-------------|
| 1 | WebSocket Protocol & Python Data Model | Define JSON protocol messages and Python data classes for controls, groups, and events. | ✅ Done |
| 2 | JS Frontend — Control Panel | DOM-based control panel with drag, hide/restore, group expand/collapse. | ✅ Done |
| 3 | JS Frontend — Attachable Controls | CSS2DRenderer integration for controls attached to 3D objects. | ✅ Done |
| 4 | Python API — Visualizer Integration | Wire `Visualizer` methods, async handler registry, server message dispatch. | ✅ Done |
| 5 | Example — Two Spheres Intersection | Demo script: two spheres, their intersection, slider to move one sphere. | ✅ Done |

### Phase Dependency Graph

```
Phase 1 ──► Phase 2 ──► Phase 4 ──► Phase 5
               │
Phase 1 ──► Phase 3 ──┘
```

Phases 2 and 3 are independent and can be worked on in parallel after Phase 1.
Phase 4 integrates both JS subsystems into the Python API. Phase 5 is a
validation/integration test.

---

## Detailed Plans

- [Phase 1 — WebSocket Protocol & Python Data Model](./phase1-protocol-and-data-model.md)
- [Phase 2 — JS Frontend: Control Panel](./phase2-frontend-control-panel.md)
- [Phase 3 — JS Frontend: Attachable Controls](./phase3-frontend-attachable-controls.md)
- [Phase 4 — Python API: Visualizer Integration](./phase4-python-api-integration.md)
- [Phase 5 — Example: Two Spheres Intersection](./phase5-example-two-spheres.md)

---

## Key Design Decisions

1. **Custom HTML/CSS overlay** (no external GUI library). Controls are plain
   DOM elements styled to match the existing dark theme. Zero new CDN
   dependencies.

2. **JSON over WebSocket** for both control definition (Python → JS) and
   control events (JS → Python), using the same infrastructure as entity scene
   updates.

3. **Async handler pattern**: Control interaction handlers registered from
   Python are `async def` callables dispatched on the server's asyncio event
   loop, allowing scene modifications.

4. **Attachable controls via CSS2DRenderer**: Controls and groups can be
   parented to 3D objects, just like the existing label system. The frontend
   reuses the CSS2DObject wrapping pattern from `viewer.js`.

5. **Server-only**: Controls are not included in HTML/figure exports. The
   export bootstrap code skips the `controls` layer explicitly.

---

## Files to Create/Modify

### New Files
| File | Phase | Purpose |
|------|-------|---------|
| `py/pytanga/viz/_controls.py` | 1 | Python data classes: `Control`, `ControlGroup`, event types |
| `py/pytanga/viz/templates/controls-panel.js` | 2 | JS module: DOM control panel rendering and event dispatch |
| `py/pytanga/viz/templates/controls-attached.js` | 3 | JS module: CSS2D-attached controls |
| `py/examples/viz/two_spheres_interact.py` | 5 | Example script |

### Modified Files
| File | Phase | Changes |
|------|-------|---------|
| `py/pytanga/viz/templates/viewer.html` | 2 | Import `controls-panel.js` module |
| `py/pytanga/viz/templates/viewer.js` | 2,3 | Wire control messages, call control module init |
| `py/pytanga/viz/server.py` | 4 | Dispatch `control:change`/`control:click` to Python handlers |
| `py/pytanga/viz/visualizer.py` | 4 | Add `add_slider`, `add_dropdown`, `add_button`, `add_group` methods |
| `py/pytanga/viz/serializer.py` | 1 | Add `serialize_controls` function |
| `py/pytanga/viz/__init__.py` | 4 | Export new types |
| `py/pytanga/viz/export/_bootstrap/_overlays.py` | 4 | Skip control layer in exports |