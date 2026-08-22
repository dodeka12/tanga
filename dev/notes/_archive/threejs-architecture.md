# Three.js Visualization Architecture for Tanga

## How Three.js Works

Three.js is **not a single JS file** — it's a modular library. You have three options for using it:

### Option A: CDN Import Map (Recommended — Zero Build Tools)

The simplest way for a standalone HTML page. No npm, no bundler, no install step. Just an HTML file that loads Three.js from a CDN:

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <script type="importmap">
  {
    "imports": {
      "three": "https://unpkg.com/three@0.168.0/build/three.module.js",
      "three/addons/": "https://unpkg.com/three@0.168.0/examples/jsm/"
    }
  }
  </script>
</head>
<body>
  <script type="module">
    import * as THREE from 'three';
    import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

    // Your code here — no build step needed
    const scene = new THREE.Scene();
    // ...
  </script>
</body>
</html>
```

This uses ES modules from the browser via `importmap`. No install, no bundler, no `node_modules`. Just serve the HTML file and it works. The browser caches the CDN files.

### Option B: npm + Bundler (Vite/Webpack)

```bash
npm install three
```

Then use a bundler. This is overkill for our use case but gives tree-shaking and smaller builds.

### Option C: Single-file build (legacy)

Three.js does provide a monolithic `three.min.js` but this is the legacy UMD build and doesn't include the addons (OrbitControls etc.). Not recommended.

**For Tanga, Option A (CDN import map) is ideal.** No build step, no npm, just a static HTML file we serve alongside the WebSocket server.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     User's Python Script                     │
│  from pytanga.geometry import Point, Line, Plane, ...       │
│  from pytanga.viz import Visualizer                         │
│                                                             │
│  viz = Visualizer()                                         │
│  viz.scene.add(Point(1, 2, 3), color="red")                │
│  viz.scene.add(Plane(...), opacity=0.3)                    │
│  viz.run()   # starts server, opens browser                 │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                 Python: tanga-viz Server                     │
│                                                             │
│  ┌─────────────────┐    ┌──────────────────────┐           │
│  │  WebSocket Server│◄───│  Scene State Manager  │           │
│  │  (aiohttp/       │    │  - keeps current     │           │
│  │   websockets)    │    │    list of entities   │           │
│  │                  │    │  - diffs on update    │           │
│  │  Port 8765       │    │  - JSON serialization │           │
│  └────────┬─────────┘    └──────────────────────┘           │
│           │                                                 │
│           │  Also serves static HTML/JS on another port     │
│           │  (or same port via HTTP upgrade)                │
│           ▼                                                 │
│  ┌─────────────────────────────────────────────┐           │
│  │         Entity → JSON Serializer             │           │
│  │  Point → {"type":"Point","x":1,"y":2,"z":3} │           │
│  │  Line  → {"type":"Line","origin":...,       │           │
│  │           "direction":...}                   │           │
│  │  Plane → {"type":"Plane","point":...,        │           │
│  │           "normal":..., "clipExtent":10.0}   │           │
│  │  ...                                         │           │
│  └─────────────────────────────────────────────┘           │
└──────────────────────────┬──────────────────────────────────┘
                           │ WebSocket (JSON messages)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│           Browser: Three.js Frontend (static HTML/JS)        │
│                                                             │
│  ┌─────────────────┐    ┌──────────────────────┐           │
│  │  WebSocket Client│───►│  Scene Controller     │           │
│  │  (native JS)     │    │  - parses JSON        │           │
│  │                  │    │  - creates/destroys   │           │
│  │                  │    │    Three.js meshes    │           │
│  │                  │    │  - updates transforms │           │
│  └─────────────────┘    └──────────┬───────────┘           │
│                                    │                        │
│                                    ▼                        │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              Entity Renderer Factory                     ││
│  │  Point   → THREE.SphereGeometry + MeshPhongMaterial     ││
│  │  Plane   → THREE.PlaneGeometry + translucent material   ││
│  │  Line    → THREE.CylinderGeometry (thin tube)           ││
│  │  Sphere  → THREE.SphereGeometry + wireframe             ││
│  │  Circle  → THREE.TorusGeometry                          ││
│  │  Direction → Arrow (cone + cylinder)                    ││
│  └─────────────────────────────────────────────────────────┘│
│                                    │                        │
│                                    ▼                        │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              THREE.Scene + OrbitControls                 ││
│  │  - Grid helper, Axes helper                             ││
│  │  - Ambient + directional lighting                       ││
│  │  - Translucent rendering via opacity + depthWrite       ││
│  │  - Automatic camera tracking of scene bounds            ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
py/pytanga/viz/                  # New Python package
├── __init__.py
├── visualizer.py                 # Main Visualizer class (user-facing API)
├── server.py                     # aiohttp WebSocket + static file server
├── serializer.py                 # Entity → JSON serialization
├── templates/
│   └── viewer.html               # Three.js frontend (CDN import map)
│   └── viewer.js                 # Main JS module
│   └── renderers/
│       ├── point.js
│       ├── line.js
│       ├── plane.js
│       ├── circle.js
│       ├── sphere.js
│       ├── direction.js
│       └── space.js
```

---

## WebSocket Protocol

Simple JSON-based protocol. Messages from Python → Browser:

```json
{
  "type": "scene_update",
  "entities": [
    {
      "id": "abc123",
      "kind": "Point",
      "color": "#ff4444",
      "opacity": 1.0,
      "position": [1.0, 2.0, 3.0],
      "size": 0.1
    },
    {
      "id": "def456",
      "kind": "Plane",
      "color": "#4488ff",
      "opacity": 0.3,
      "point": [0, 0, 3],
      "normal": [0, 0, 1],
      "extent": 10.0
    },
    {
      "id": "ghi789",
      "kind": "Line",
      "color": "#44ff44",
      "opacity": 0.8,
      "origin": [0, 0, 0],
      "direction": [1, 0, 0],
      "length": 20.0,
      "thickness": 0.03
    },
    {
      "id": "jkl012",
      "kind": "Sphere",
      "color": "#ffaa00",
      "opacity": 0.4,
      "center": [0, 0, 0],
      "radius": 2.5,
      "wireframe": true
    },
    {
      "id": "mno345",
      "kind": "Circle",
      "color": "#ff44ff",
      "opacity": 0.7,
      "center": [0, 0, 0],
      "normal": [0, 0, 1],
      "radius": 3.0
    },
    {
      "id": "pqr678",
      "kind": "Direction",
      "color": "#ffffff",
      "opacity": 0.9,
      "vector": [1, 0, 0],
      "length": 2.0,
      "origin": [0, 0, 0]
    }
  ],
  "removed": []   # IDs of entities to remove
}
```

Browser can also send back basic events (optional):
```json
{"type": "ready"}           # Client connected and rendered
{"type": "click", "id": "abc123"}  # User clicked an entity
```

---

## Python API Design

```python
from pytanga.viz import Visualizer

# Create and configure
viz = Visualizer(port=8765, open_browser=True)

# Add entities directly
viz.add(Point(1, 2, 3), color="#ff4444", size=0.1)
viz.add(Plane(point=Point(0,0,3), normal=Direction(0,0,1)), 
        opacity=0.3)
viz.add(Sphere(Point(0,0,0), radius=2.5), 
        wireframe=True, opacity=0.4)
viz.add(Line(origin=Point(0,0,0), direction=Direction(1,0,0)),
        color="#44ff44")

# Auto-convert multivectors to entities
from pytanga.algebra import Algebra
pga = Algebra.from_name("PGA3")
mv = pga.plane(0, 0, 1, 3)  # plane at z=3
viz.add_mv(mv, opacity=0.3)   # goes through analyze() automatically

# Start the server (blocks until window is closed)
viz.run()

# Or: non-blocking mode
viz.start()           # starts server in background thread
# ... more code ...
viz.update()          # sends current scene state
viz.stop()
```

---

## Dependencies

Python side (add to `pyproject.toml`):
- `aiohttp` — WebSocket + HTTP static file serving
- Nothing else needed (serializer is pure Python, no heavy deps)

Browser side:
- Three.js from CDN (`unpkg.com/three@0.168.0`)
- OrbitControls from CDN (same)
- No npm, no bundler, no TypeScript compilation

---

## Key Implementation Details

### Translucent rendering in Three.js

```js
const material = new THREE.MeshPhongMaterial({
  color: 0x4488ff,
  opacity: 0.3,
  transparent: true,
  depthWrite: false,  // Important: allows seeing through to other objects
  side: THREE.DoubleSide,  // See plane from both sides
});
```

The `depthWrite: false` is critical — without it, translucent objects occlude objects behind them incorrectly.

### Infinite Planes/Lines

Planes and lines in GA are infinite, but Three.js needs finite geometry. Strategy:
- Render planes as large quads (e.g., 20×20 units), large enough to fill the viewport at typical zoom levels
- Render lines as long thin cylinders
- Use a grid texture or dashed pattern to convey "this extends infinitely"

### OrbitControls Setup

```js
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;     // Smooth inertia
controls.dampingFactor = 0.08;
controls.mouseButtons = {
  LEFT: THREE.MOUSE.ROTATE,
  MIDDLE: THREE.MOUSE.PAN,
  RIGHT: THREE.MOUSE.ZOOM
};
controls.screenSpacePanning = true;  // Pan along screen plane
```

### Colored Axes & Grid

```js
scene.add(new THREE.AxesHelper(5));   // RGB axes, 5 units long
const grid = new THREE.GridHelper(20, 20);  // 20x20 grid with 1-unit cells
scene.add(grid);
```

---

## Animations

Yes, animations work perfectly with the CDN + WebSocket approach. There are two strategies, depending on what kind of animation you need.

### Strategy 1: Frame Streaming (Python-controlled, real-time)

Python computes every frame and pushes updates over WebSocket. The browser renders each frame as it arrives. This is ideal when the animation logic lives in Python (e.g., animating a rotor by varying its angle, or stepping through a geometric construction).

**Python side:**

```python
import time
import math
from pytanga.viz import Visualizer
from pytanga.geometry import Point, Sphere, Rotor, Direction

viz = Visualizer()
viz.start()  # non-blocking — server runs in background thread

sphere_id = viz.add(Sphere(Point(0, 0, 0), radius=2.0), wireframe=True, opacity=0.4)

# Pre-create a Rotor and animate its angle
for t in range(600):
    angle = t * 0.05  # slowly rotate over time
    rotor = Rotor(angle=angle, axis=Direction(0, 0, 1))
    viz.update_entity(sphere_id, rotor=rotor)  # sends new transform
    time.sleep(1/60)  # ~60 FPS

viz.stop()
```

**WebSocket message (per frame):**

```json
{
  "type": "frame",
  "entities": [
    {
      "id": "sphere_1",
      "position": [0, 0, 0],       // optional — only include changed fields
      "rotation": [0, 0, 0.314],   // axis-angle or quaternion
      "color": "#ffaa00",
      "opacity": 0.4
    }
  ],
  "removed": []
}
```

**Three.js side** already runs a `requestAnimationFrame` render loop. On each WebSocket message it updates mesh transforms directly — no extra work needed. The browser's native 60 FPS loop handles smooth rendering automatically.

**Performance:** At 60 FPS, you're sending ~60 small JSON messages per second. Each is a few hundred bytes. WebSocket handles this easily. For heavy scenes with many entities, send only changed fields (the JS side keeps the last known state and applies delta updates).

### Strategy 2: Keyframe + Interpolation (Browser-tweened)

Python sends a target state and the browser smoothly interpolates (tweens) from the current state to the target. This is ideal for "go from A to B" animations, object morphing, or smooth transitions — no per-frame Python involvement.

**Python side:**

```python
viz.animate_to(entity_id, 
    target_position=(5, 0, 0),       # move point from current → (5,0,0)
    target_rotation=math.pi/2,       # rotate to 90°
    target_opacity=0.1,              # fade to near-transparent
    duration=2.0,                    # over 2 seconds
    easing="ease-in-out"             # smooth acceleration + deceleration
)
```

**WebSocket message:**

```json
{
  "type": "animate",
  "animations": [
    {
      "id": "sphere_1",
      "target": {
        "position": [5.0, 0.0, 0.0],
        "rotation": [0.0, 0.0, 1.571],
        "opacity": 0.1
      },
      "duration": 2.0,
      "easing": "ease-in-out"
    }
  ]
}
```

**Three.js side** implements this in the render loop:

```js
// Simplified interpolation logic
const animations = new Map();  // id → { start, target, startTime, duration, easing }

function updateAnimations(now) {
  for (const [id, anim] of animations) {
    const elapsed = (now - anim.startTime) / 1000;  // seconds
    let t = Math.min(elapsed / anim.duration, 1.0);
    t = applyEasing(t, anim.easing);  // ease-in-out, linear, etc.

    const mesh = entityMeshes.get(id);
    mesh.position.lerpVectors(anim.start.position, anim.target.position, t);
    mesh.rotation.setFromVector3(
      anim.start.rotation.clone().lerp(anim.target.rotation, t)
    );
    mesh.material.opacity = lerp(anim.start.opacity, anim.target.opacity, t);

    if (elapsed >= anim.duration) animations.delete(id);  // done
  }
}

function renderLoop(timestamp) {
  updateAnimations(timestamp);
  renderer.render(scene, camera);
  requestAnimationFrame(renderLoop);
}
```

### Use Case Examples

| Animation | Strategy | How |
|-----------|----------|-----|
| **Rotating a rotor** — show the axis of rotation spinning | Frame Streaming | Python loops the angle, pushes updated Rotor each frame |
| **Translating a point along a path** | Frame Streaming | Python steps along a parametric curve |
| **Fading in a plane** — plane materializes | Keyframe | Python sends `animate_to(opacity: 0→0.3, duration: 1s)` |
| **Morphing a sphere** — radius changes smoothly | Keyframe | `animate_to(target_radius=5.0, duration: 1.5s)` |
| **Building up a geometric construction** — entities appear one by one | Keyframe | Add entities with `opacity: 0`, then animate each to `opacity: 1` with staggered delays |
| **Applying a Motor** — combined rotate + translate | Frame Streaming | Python computes the animated motor, sends updated transforms each frame |
| **Wireframe ↔ solid toggle** | Keyframe | Change material wireframe + opacity in one smooth transition |

### Adding a Timeline (Optional)

For more complex animations, you can add a simple timeline/sequencer:

```python
viz.timeline()
    .wait(0.5)
    .animate_to(point_id, position=(3, 0, 0), duration=1.0)
    .wait(0.2)
    .animate_to(plane_id, opacity=0.3, duration=0.5)
    .animate_to(circle_id, rotation=math.pi, duration=2.0, parallel=True)
    .play()
```

This sends a batch of timed animation commands over WebSocket in one message:

```json
{
  "type": "timeline",
  "steps": [
    {"at": 0.0, "animate": {"id": "pt", "position": [3,0,0], "duration": 1.0}},
    {"at": 1.2, "animate": {"id": "pl", "opacity": 0.3, "duration": 0.5}},
    {"at": 1.2, "animate": {"id": "ci", "rotation": 3.1416, "duration": 2.0}}
  ]
}
```

The JS side runs a lightweight sequencer that fires each step at its scheduled time.

### Performance Considerations

| Concern | Mitigation |
|---------|-----------|
| **Frame streaming at 60 FPS** | Only send changed fields (delta updates). The JS side already has the entity state; it patches in what changed. Typical frame message is 50–150 bytes per moving entity. |
| **Many entities animating** | Batch all frame updates into a single WebSocket message per frame. One message with 20 entities is still <5 KB. |
| **WebSocket latency** | All communication is localhost → negligible latency (<1ms). Frame streaming works smoothly at 60 FPS. |
| **Browser render performance** | Three.js handles hundreds of meshes at 60 FPS. Translucent objects have higher GPU cost; use `depthWrite: false` and limit translucent count. |
| **Interpolation precision** | For numeric precision (GA calculations), Strategy 1 is preferred — Python computes exact values each frame. Strategy 2 is for visual smoothness, not sub-millimeter accuracy. |

---

## Summary

| Layer | Technology | Effort |
|-------|-----------|--------|
| Server | Python `aiohttp` (WebSocket + static files) | ~100 lines |
| Serializer | Pure Python dataclass → dict → JSON | ~80 lines |
| Frontend HTML | Single static HTML with CDN import map | ~30 lines |
| Frontend JS Renderers | Three.js mesh factory for each entity type | ~200 lines |
| Frontend JS Animations | requestAnimationFrame tween loop | ~80 lines |
| Integration | `pytanga.viz.Visualizer` class | ~120 lines |

The whole system is ~600 lines of code, no build tools, no npm. It runs with just `uv run python my_script.py` and the browser opens automatically showing an interactive 3D scene with orbit controls and full animation support.
