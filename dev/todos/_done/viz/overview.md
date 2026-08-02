# Visualization Submodule — Overview Plan

**Goal:** Create a new `py/pytanga/viz/` submodule that provides an interactive 3D
visualization of `pytanga.geometry` entities in a web browser using **Three.js**.
Users can rotate, pan, zoom, and toggle translucency. The architecture uses a
lightweight Python WebSocket server pushing JSON scene updates to a static
HTML/JS frontend that loads Three.js via CDN import maps — zero npm, zero build tools.

**Reference:** [`dev/notes/threejs-architecture.md`](../../notes/threejs-architecture.md)

---

## 1. Submodule Structure

```
py/pytanga/viz/
├── __init__.py              # Re-exports Visualizer, public symbols
├── visualizer.py            # Main Visualizer class (user-facing API)
├── scene.py                 # Scene state manager (entity list, diffs, IDs)
├── server.py                # aiohttp HTTP + WebSocket server
├── serializer.py            # Entity/Operator → JSON-compatible dicts
├── templates/
│   ├── viewer.html           # Three.js frontend (CDN import map, fullscreen canvas)
│   └── viewer.js             # Main JS entry: scene setup, WS client, render loop
│   └── renderers/
│       ├── point.js          # Point → small sphere
│       ├── line.js           # Line → thin cylinder tube
│       ├── plane.js          # Plane → translucent quad (+ wireframe grid)
│       ├── circle.js         # Circle → thin torus
│       ├── sphere.js         # Sphere → wireframe + translucent shell
│       ├── direction.js      # Direction → arrow (cone + cylinder)
│       └── space.js          # Space → faint bounding outline
│   └── controls.js           # OrbitControls + camera management
│   └── animator.js           # requestAnimationFrame tween system
│   └── renderers/
│       ├── operators/
│       │   ├── rotor.js          # Rotor → disc arc + axis
│       │   ├── translator.js     # Translator → 3D arrow
│       │   ├── motor.js          # Motor → helix/screw
│       │   ├── reflection.js     # Reflection → mirror plane + normal
│       │   ├── inversion.js      # Inversion → wireframe sphere
│       │   ├── dilator.js        # Dilator → expanding rings
│       │   ├── general_rotor.js  # GeneralRotor → combined bivector planes
│       │   └── general_dilator.js # GeneralDilator → directed expanding rings
│       └── entity_to_kind.py     # Maps operator types to kind strings
```

---

## 2. Design Principles

1. **Zero frontend build step:** Three.js loaded via CDN import maps. No npm,
   no bundler, no TypeScript compilation. Just plain HTML + ES modules.

2. **Python-first API:** Users create a `Visualizer`, add `pytanga.geometry`
   entity objects, and call `viz.run()`. Everything else is internal.

3. **WebSocket for real-time updates:** JSON messages over a single WebSocket
   connection. Scene diffs keep bandwidth minimal — only changed properties
   are sent each frame.

4. **Two animation strategies:**
   - **Frame streaming:** Python pushes per-frame state (for GA-driven animation)
   - **Keyframe tweening:** Browser interpolates between states (for smooth transitions)

5. **No Python visualization dependencies:** Only `aiohttp` is needed for the
   server. The serializer is pure Python. No matplotlib, no PyVista, no VTK.

6. **Progressive enhancement:** Phase 1-4 deliver a static scene viewer.
   Phase 5 adds entity-specific renderers. Phase 6 adds animation.
   Each phase produces a working (if limited) product.

7. **Configurable camera and space:** Users can explicitly set the 3D space
   extent, camera focal length (FOV), position, orientation, and look-at target.
   When not specified, the camera is computed automatically from the set of
   entities added before the first `flush()`.

8. **Scene config sent on initial handshake:** The server sends a `scene_config`
   message before any entity data, carrying space bounds, camera settings,
   grid preferences, and background color. The JS side applies this once at
   connect time.

---

## 3. Implementation Phases

| Phase | Plan File | Description |
|-------|-----------|-------------|
| Phase 1 | [`phase1-session-scene.md`](phase1-session-scene.md) | `Visualizer` class + `Scene` state manager |
| Phase 2 | [`phase2-serializer.md`](phase2-serializer.md) | Entity → JSON serializer |
| Phase 3 | [`phase3-server.md`](phase3-server.md) | `aiohttp` HTTP + WebSocket server |
| Phase 4 | [`phase4-frontend-core.md`](phase4-frontend-core.md) | HTML/JS: Three.js scene, WS client, OrbitControls, render loop |
| Phase 4a | [`phase4a-geo-fix-sync.md`](phase4a-geo-fix-sync.md) | Update viz code for geo_fix changes (entities, operators, Geometry class) |
| Phase 5 | [`phase5-entity-renderers.md`](phase5-entity-renderers.md) | Per-entity JS renderer modules (Point, Line, Plane, Circle, Sphere, Direction, Space) |
| Phase 6 | [`phase6-operators.md`](phase6-operators.md) | Operator visualization — JS renderers for Rotor, Translator, Motor, Reflection, etc. |
| Phase 7 | [`phase7-animation.md`](phase7-animation.md) | Frame streaming + keyframe interpolation + optional timeline |
| Phase 8 | [`phase8-integration.md`](phase8-integration.md) | `__init__.py`, `pyproject.toml` deps, auto-browser-open, error handling, end-to-end wiring |
| Phase 9 | [`phase9-docs.md`](phase9-docs.md) | `docs/py/viz/` — usage guide, API reference, examples |
| Phase 10 | [`phase10-examples.md`](phase10-examples.md) | `py/examples/viz/` — runnable example scripts |
| Phase 11 | [`phase11-export.md`](phase11-export.md) | Scene export: self-contained HTML + glTF 2.0 binary (`.glb`) |
| Phase 12 | [`phase12-title-annotation.md`](phase12-title-annotation.md) | Title overlay + markdown annotation panel with LaTeX math (`marked` + KaTeX) |
| Phase 13 | [`phase13-figure-export.md`](phase13-figure-export.md) | Presentation figure export — HTML snippet with FigureStyle/FigureConfig, transparent bg, auto-rotate |
| Phase 14 | [`phase14-refactor-visualizer.md`](phase14-refactor-visualizer.md) | Refactor Visualizer — extract SceneExporter, move style factories/helpers to _style_dict.py |
| Phase 15 | [`phase15-screenshots-video.md`](phase15-screenshots-video.md) | PNG snapshots & MPEG video capture — browser shortcut (Ctrl+S), programmatic screenshot via WebSocket, animation frame capture + ffmpeg stitching |
| Phase 16 | [`phase16-offscreen-capture.md`](phase16-offscreen-capture.md) | ~~Off-screen rendering + html2canvas~~ — **NOT IMPLEMENTED**: technical difficulties (html2canvas clone failures, CSS2D positioning at non-native resolutions, DOM layout breakage) overcomplicate the code. Live-viewport capture with `preserveDrawingBuffer` + container-based alignment (from Phase 15) is sufficient. |
| Phase 17 | [`phase17-animated-export.md`](phase17-animated-export.md) | Animated HTML figure export — embed keyframe-recording in self-contained HTML with JS playback engine, controls (play/pause/scrub), no Python server needed |
| Phase 18 | [`phase18-consolidate-export.md`](phase18-consolidate-export.md) | Consolidate export bootstrap code — extract shared JS code generator (`_bootstrap_core.py`) with composable functions, eliminate ~800 lines of duplication across four export paths, fix missing title/annotation in animated figure export |
| Phase 18a | [`phase18a-animated-cleanup.md`](phase18a-animated-cleanup.md) | Animated bootstrap cleanup — move remaining inline JS templates into shared `_bootstrap/` package, eliminate cross-file duplication, split `_bootstrap_core.py` into submodules |

---

## 4. Files to Create

### New Files (all under `py/pytanga/viz/` unless noted)

| File | Phase |
|------|-------|
| `__init__.py` | 7 |
| `visualizer.py` | 1 |
| `scene.py` | 1 |
| `serializer.py` | 2 |
| `server.py` | 3 |
| `templates/viewer.html` | 4 |
| `templates/viewer.js` | 4 |
| `templates/controls.js` | 4 |
| `templates/renderers/point.js` | 5 |
| `templates/renderers/line.js` | 5 |
| `templates/renderers/plane.js` | 5 |
| `templates/renderers/circle.js` | 5 |
| `templates/renderers/sphere.js` | 5 |
| `templates/renderers/direction.js` | 5 |
| `templates/renderers/space.js` | 5 |
| `templates/animator.js` | 6 |
| `docs/py/viz/index.md` | 8 |
| `docs/py/viz/examples.md` | 8 |

### New Files (examples)

| File | Phase |
|------|-------|
| `py/examples/viz/demo_all_entities.py` | 9 |
| `py/examples/viz/demo_mv_visualization.py` | 9 |
| `py/examples/viz/demo_animation_orbit.py` | 9 |
| `py/examples/viz/demo_animation_timeline.py` | 9 |
| `py/examples/viz/demo_labels.py` | 9 |
| `py/examples/viz/demo_camera_config.py` | 9 |
| `py/examples/viz/demo_custom_defaults.py` | 9 |
| `py/examples/viz/demo_notebook.ipynb` | 9 |

### Modified Files

| File | Change | Phase |
|------|--------|-------|
| `pyproject.toml` | Add `aiohttp` dependency | 7 |
| `docs/py/index.md` | Add viz submodule link | 8 |

---

## 5. MVP Definition (Phase 1–4)

After Phase 4, the system is end-to-end functional:

```python
from pytanga.viz import Visualizer
from pytanga.geometry import Point, Sphere

viz = Visualizer()
viz.add(Point(1, 2, 3), color="#ff4444", size=0.1)
viz.add(Sphere(Point(0, 0, 0), radius=2.5), wireframe=True, opacity=0.4)
viz.run()  # starts server, opens browser, blocks until window closes
```

What works:
- Server starts on `localhost:8765`
- Browser opens automatically
- Three.js scene renders with orbit controls (rotate/pan/zoom)
- All entity types display as basic Three.js primitives
- Translucency via `opacity` + `depthWrite: false`
- Grid and axes helpers

What doesn't work yet (needs later phases):
- Entity-specific optimized renderers (Phase 5 — all entities use placeholder spheres in Phase 4)
- Animations (Phase 6)
- Documentation (Phase 8)

---

## 6. Dependencies

| Layer | Dependency | Purpose |
|-------|-----------|---------|
| Python | `aiohttp` | HTTP + WebSocket server |
| Python | `pytanga.geometry` | Entity/operator data classes (already exists) |
| Browser | `three@0.168.0` | 3D rendering (CDN, no npm) |
| Browser | `OrbitControls` | Camera interaction (CDN addon) |
| Browser | `marked` ^15.0 | Markdown → HTML rendering (CDN, no npm) |
| Browser | `KaTeX` ^0.16 | LaTeX math formula rendering (CDN, no npm) |

No other Python or JavaScript dependencies.

---

## 7. Key References

- **Architecture document:** `dev/notes/threejs-architecture.md`
- **3D library comparison:** `dev/notes/3d-visualization-options.md`
- **Entity classes:** `py/pytanga/geometry/entities.py`
- **Operator classes:** `py/pytanga/geometry/operators.py`
- **Existing plan pattern:** `dev/todos/_done/geometry/overview.md`

---

## 8. Completion Status

### Overall Progress

- [x] **Phase 1:** Visualizer + Scene ✅ (all 19 checkboxes)
- [x] **Phase 2:** Serializer ✅ (base implementation; needs Phase 4a sync for new entity/op types)
- [x] **Phase 3:** Server ✅ (all 10 checkboxes)
- [x] **Phase 4:** Frontend Core ✅ (all 18 checkboxes; needs Phase 4a sync for new renderer cases)
- [x] **Phase 4a:** Geo-fix sync ✅ (serializer.py, visualizer.py, factory.js updated; 91 tests)
- [ ] **Phase 5:** Entity Renderers (monolithic factory.js exists but not refactored into per-file modules)
- [ ] **Phase 6:** Operator Visualization (renderer cases exist in factory.js but not in separate files)
- [x] **Phase 7:** Animation ✅ (all 26 checkboxes; tween engine, frame streaming, timeline, animate_to API)
- [x] **Phase 8:** Integration (partial — __init__.py, Jupyter not done)
- [ ] **Phase 9:** Documentation (not started)
- [ ] **Phase 10:** Examples (not started)
- [x] **Phase 11:** Scene Export ✅ (HTML + glTF; `_export.py`, `_gltf.py`, 13 smoke tests)
- [x] **Phase 12:** Title & Annotation ✅ (AnnotationStyle, TitleStyle, marked+KaTeX, export support)
- [x] **Phase 13:** Figure Export ✅ (FigureStyle, FigureConfig, SceneExporter, open_figure)
- [x] **Phase 14:** Refactor Visualizer ✅ (SceneExporter extracted, default styles via factory functions; 97 tests)
- [x] **Phase 15:** PNG Snapshots & Video ✅ (screenshot, frame capture, ffmpeg; 97 tests)
- [ ] **Phase 16:** Off-Screen Capture (plan only, **NOT implemented** — technical difficulties with html2canvas/offscreen rendering overcomplicate the code; live-viewport capture in Phase 15 is sufficient)
- [x] **Phase 17:** Animated HTML Figure Export ✅ (implemented, all 57+ checkboxes)
- [x] **Phase 18:** Consolidate Export Bootstrap ✅ (shared `_bootstrap/` package, composable JS generators, ~800 lines of duplication eliminated)
- [x] **Phase 18a:** Animated Bootstrap Cleanup ✅ (inline JS templates moved to `_bootstrap/` submodules, cross-file duplication eliminated, `_bootstrap_core.py` split into 6 submodules)

### Quick Status

| Phase | Plan | Implemented | Tested |
|-------|------|-------------|--------|
| 1 | ✅ | ✅ | ✅ (59 tests) |
| 2 | ✅ | ✅ | ✅ (30 tests) — needs Phase 4a |
| 3 | ✅ | ✅ | ✅ (manual + smoke test) |
| 4 | ✅ | ✅ | ✅ (manual browser test) — needs Phase 4a |
| 4a | ✅ | ✅ | ✅ (91 tests) |
| 5 | ✅ | partial (monolithic factory.js) | ❌ |
| 6 | ✅ | partial (operator cases in factory.js) | ❌ |
| 7 | ✅ | ✅ | ✅ (90 tests + animation API) |
| 8 | ✅ | ✅ | ❌ |
| 9 | ✅ | ❌ | ❌ |
| 10 | ✅ | ❌ | ❌ |
| 12 | ✅ | ✅ | ❌ |
| 13 | ✅ | ✅ | ❌ |
| 14 | ✅ | ✅ | ✅ (97 tests) |
| 15 | ✅ | ✅ | ✅ (97 tests) |
| 16 | ✅ | ❌ (not implemented — see note) | ❌ |
| 17 | ✅ | ✅ | ✅ (57+ checkboxes) |
| 18 | ✅ | ✅ | ✅ (all checkboxes) |
| 18a | ✅ | ✅ | ✅ (all checkboxes) |
