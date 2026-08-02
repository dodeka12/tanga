# Phase 7: Animation Support

**Files:** `py/pytanga/viz/templates/animator.js`, updates to `viewer.js` and `visualizer.py`

**Goal:** Add two animation strategies to the visualization: **frame streaming**
(Python pushes per-frame entity updates) and **keyframe interpolation**
(browser smoothly tweens between states). Plus an optional timeline sequencer.

**Prerequisites:** Phase 4 (working end-to-end scene viewer), Phase 5 (per-entity renderers)

---

## 1. Frame Streaming (Python-Driven)

### 1.1 Python Side

The `Visualizer` already supports per-frame updates via `update_entity()`:

```python
# Animation loop in user script
viz = Visualizer()
viz.start()

point_id = viz.add(Point(0, 0, 0), color="#ff4444")

import time, math
for t in range(600):
    angle = t * 0.05
    x = 3 * math.cos(angle)
    y = 3 * math.sin(angle)
    viz.update_entity(point_id, Point(x, y, 0))
    viz.flush()  # pushes dirty entities over WebSocket
    time.sleep(1/60)

viz.stop()
```

The `Scene.flush()` already tracks dirty entities. The server's `push()` broadcasts
diffs. **No new Python code needed** — frame streaming works with the Phase 3 server
and Phase 1 scene manager as-is.

### 1.2 JavaScript Side — Efficient Diff Updates

Phase 4's `updateEntity()` does full removal and re-creation. For frame streaming
at 60 FPS, that's too slow. Phase 6 introduces in-place mesh updates:

```js
// In viewer.js — enhanced updateEntity()

function updateEntity(ent) {
  const id = ent.id;
  const mesh = entityMeshes.get(id);
  const previous = entityData.get(id);

  if (!mesh) {
    // New entity
    const newMesh = createEntityMesh(ent);
    if (newMesh) {
      scene.add(newMesh);
      entityMeshes.set(id, newMesh);
    }
    entityData.set(id, { ...ent });
    return;
  }

  // In-place update for existing entity
  if (ent.position) {
    mesh.position.set(ent.position[0], ent.position[1], ent.position[2]);
  }
  if (ent.vector) {
    // Direction vector changed — update arrow orientation
    mesh.position.set(
      (ent.origin || [0, 0, 0])[0],
      (ent.origin || [0, 0, 0])[1],
      (ent.origin || [0, 0, 0])[2]
    );
    mesh.setRotationFromQuaternion(
      rotationFromDirection(ent.vector[0], ent.vector[1], ent.vector[2])
    );
  }
  if (ent.center) {
    mesh.position.set(ent.center[0], ent.center[1], ent.center[2]);
  }
  if (ent.opacity !== undefined && mesh.material) {
    mesh.traverse(child => {
      if (child.material && child.material.opacity !== undefined) {
        child.material.opacity = ent.opacity;
        child.material.transparent = ent.opacity < 1.0;
        child.material.depthWrite = ent.opacity >= 0.99;
        child.material.needsUpdate = true;
      }
    });
  }
  if (ent.color && mesh.material) {
    const c = new THREE.Color(ent.color);
    mesh.traverse(child => {
      if (child.material && child.material.color) {
        child.material.color.copy(c);
      }
    });
  }
  // For structural changes (radius, extent, kind change): full rebuild
  if (ent.radius !== undefined || ent.extent !== undefined || ent.kind !== previous.kind) {
    removeEntityMesh(mesh);
    entityMeshes.delete(id);
    const rebuilt = createEntityMesh(ent);
    if (rebuilt) {
      scene.add(rebuilt);
      entityMeshes.set(id, rebuilt);
    }
  }

  entityData.set(id, { ...ent });
}
```

### 1.3 Frame Message Format

The serializer in Phase 2 already produces full entity dicts. For frame streaming,
Python sends **delta dicts** — only properties that changed:

```json
{
  "type": "scene_update",
  "entities": [
    {
      "id": "abc123",
      "position": [1.5, 2.3, 0.0]
    }
  ],
  "removed": []
}
```

The JS side skips absent fields — only `position` is applied, preserving color,
opacity, size, etc.

---

## 2. Keyframe Interpolation (Browser-Tweened)

### 2.1 JavaScript Animator (`animator.js`)

A lightweight tween engine that runs inside the `requestAnimationFrame` loop:

```js
// py/pytanga/viz/templates/animator.js

import * as THREE from 'three';

/**
 * Active tweens: Map<entityId, TweenState>
 */
const tweens = new Map();

/**
 * Easing functions. t is in [0, 1].
 */
const EASING = {
  linear: (t) => t,
  'ease-in': (t) => t * t,
  'ease-out': (t) => t * (2 - t),
  'ease-in-out': (t) => t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t,
};

/**
 * Start a tween for an entity.
 *
 * @param {string} id - Entity ID
 * @param {object} target - Target properties { position?, rotation?, opacity?, scale? }
 * @param {number} duration - Duration in seconds
 * @param {string} easing - Easing function name
 * @param {Map} entityMeshes - The scene's entity mesh map
 */
export function startTween(id, target, duration, easing = 'ease-in-out', entityMeshes) {
  const mesh = entityMeshes.get(id);
  if (!mesh) return;

  const start = {
    position: mesh.position.clone(),
    scale: mesh.scale.clone(),
    rotation: new THREE.Euler().setFromQuaternion(mesh.quaternion),
  };

  // Capture current opacity from material
  mesh.traverse(child => {
    if (child.material && child.material.opacity !== undefined) {
      start.opacity = child.material.opacity;
    }
  });

  tweens.set(id, {
    start,
    target: { ...target },
    duration,
    easing: EASING[easing] || EASING['ease-in-out'],
    startTime: performance.now() / 1000,
  });
}

/**
 * Update all active tweens. Call once per frame from the render loop.
 *
 * @param {Map} entityMeshes - The scene's entity mesh map
 * @returns {boolean} true if any tweens are still active
 */
export function updateTweens(entityMeshes) {
  if (tweens.size === 0) return false;

  const now = performance.now() / 1000;
  let hasActive = false;

  for (const [id, tween] of tweens) {
    const mesh = entityMeshes.get(id);
    if (!mesh) {
      tweens.delete(id);
      continue;
    }

    const elapsed = now - tween.startTime;
    let t = Math.min(elapsed / tween.duration, 1.0);
    t = tween.easing(t);

    // Interpolate position
    if (tween.target.position) {
      mesh.position.lerpVectors(
        tween.start.position,
        new THREE.Vector3(...tween.target.position),
        t
      );
    }

    // Interpolate rotation (axis-angle or Euler)
    if (tween.target.rotation) {
      const targetRot = new THREE.Euler(...tween.target.rotation);
      mesh.rotation.set(
        tween.start.rotation.x + (targetRot.x - tween.start.rotation.x) * t,
        tween.start.rotation.y + (targetRot.y - tween.start.rotation.y) * t,
        tween.start.rotation.z + (targetRot.z - tween.start.rotation.z) * t
      );
    }

    // Interpolate opacity
    if (tween.target.opacity !== undefined) {
      const from = tween.start.opacity ?? 1.0;
      const to = tween.target.opacity;
      const val = from + (to - from) * t;
      mesh.traverse(child => {
        if (child.material && child.material.opacity !== undefined) {
          child.material.opacity = val;
          child.material.transparent = val < 1.0;
          child.material.depthWrite = val >= 0.99;
          child.material.needsUpdate = true;
        }
      });
    }

    // Interpolate scale
    if (tween.target.scale) {
      const targetScale = new THREE.Vector3(...tween.target.scale);
      mesh.scale.lerpVectors(tween.start.scale, targetScale, t);
    }

    if (t >= 1.0) {
      tweens.delete(id);
    } else {
      hasActive = true;
    }
  }

  return hasActive;
}

/**
 * Cancel all tweens for an entity, or all tweens if no ID given.
 */
export function cancelTween(id) {
  if (id) {
    tweens.delete(id);
  } else {
    tweens.clear();
  }
}
```

### 2.2 Integration into `viewer.js`

The render loop calls `updateTweens()` each frame:

```js
// In viewer.js — modified animate() function:

import { updateTweens } from './animator.js';

function animate() {
  requestAnimationFrame(animate);

  controls.update();
  updateTweens(entityMeshes);  // ← added

  renderer.render(scene, camera);
}
```

### 2.3 Message Handler for Tween Commands

```js
// In viewer.js — handleMessage() extension:

function handleMessage(msg) {
  if (msg.type === 'scene_update') {
    // ... existing handling ...
  }
  else if (msg.type === 'animate') {
    handleAnimate(msg);
  }
  else if (msg.type === 'timeline') {
    handleTimeline(msg);
  }
}

function handleAnimate(msg) {
  if (!msg.animations) return;
  for (const anim of msg.animations) {
    startTween(
      anim.id,
      anim.target,
      anim.duration || 1.0,
      anim.easing || 'ease-in-out',
      entityMeshes
    );
  }
}

function handleTimeline(msg) {
  if (!msg.steps) return;
  for (const step of msg.steps) {
    const delay = (step.at || 0) * 1000; // seconds → milliseconds
    setTimeout(() => {
      handleAnimate({ animations: [step.animate] });
    }, delay);
  }
}
```

---

## 3. Python API for Animations

### 3.1 Keyframe Method

```python
# In visualizer.py

def animate_to(
    self,
    entity_id: str,
    *,
    position: tuple[float, float, float] | None = None,
    rotation: tuple[float, float, float] | None = None,  # Euler angles
    opacity: float | None = None,
    scale: tuple[float, float, float] | None = None,
    duration: float = 1.0,
    easing: str = "ease-in-out",
) -> None:
    """Animate an entity smoothly from its current state to a target state.

    The animation runs in the browser using interpolation — no Python
    per-frame loop needed. Multiple animate_to() calls on the same
    entity queue up — the last one wins (replaces any ongoing tween).
    """
    if self._server is None:
        return

    target: dict[str, Any] = {}
    if position is not None:
        target["position"] = list(position)
    if rotation is not None:
        target["rotation"] = list(rotation)
    if opacity is not None:
        target["opacity"] = float(opacity)
    if scale is not None:
        target["scale"] = list(scale)

    message = {
        "type": "animate",
        "animations": [
            {
                "id": entity_id,
                "target": target,
                "duration": duration,
                "easing": easing,
            }
        ],
    }

    # Schedule the message on the server's event loop
    if self._loop is not None:
        asyncio.run_coroutine_threadsafe(
            self._server._push_raw(json.dumps(message)), self._loop
        )
```

### 3.2 Timeline Method

```python
# In visualizer.py

class Timeline:
    """Fluent builder for sequenced animations."""

    def __init__(self, visualizer: "Visualizer") -> None:
        self._viz = visualizer
        self._steps: list[dict[str, Any]] = []
        self._current_time: float = 0.0

    def wait(self, seconds: float) -> "Timeline":
        self._current_time += seconds
        return self

    def animate_to(self, entity_id: str, **kwargs) -> "Timeline":
        duration = kwargs.pop("duration", 1.0)
        parallel = kwargs.pop("parallel", False)

        target = {}
        for key in ("position", "rotation", "opacity", "scale"):
            if key in kwargs and kwargs[key] is not None:
                target[key] = list(kwargs[key]) if isinstance(kwargs[key], tuple) else kwargs[key]

        if not parallel:
            self._current_time += 0.01  # tiny gap to avoid conflicts

        self._steps.append({
            "at": self._current_time,
            "animate": {
                "id": entity_id,
                "target": target,
                "duration": duration,
                "easing": kwargs.get("easing", "ease-in-out"),
            },
        })

        if not parallel:
            self._current_time += duration

        return self

    def play(self) -> None:
        """Send the timeline to the browser."""
        message = {
            "type": "timeline",
            "steps": self._steps,
        }
        # ... same push pattern as animate_to ...


# On Visualizer:
def timeline(self) -> Timeline:
    return Timeline(self)
```

---

### 4.1 `animator.js` — Browser Tween Engine

- [x] **A1:** Create `py/pytanga/viz/templates/animator.js`
- [x] **A2:** Implement `startTween(id, target, duration, easing, entityMeshes)` — captures start state, stores tween
- [x] **A3:** Implement `updateTweens(entityMeshes)` — interpolates position, rotation, opacity, scale per frame
- [x] **A4:** Implement `cancelTween(id)` — cancels one or all tweens
- [x] **A5:** Define easing functions: `linear`, `ease-in`, `ease-out`, `ease-in-out`
- [x] **A6:** Support interpolation of: `position`, `rotation` (Euler), `opacity`, `scale`
- [x] **A7:** Return `true` from `updateTweens()` when tweens are still active (for render loop optimization)

### 4.2 `viewer.js` — Integration

- [x] **A8:** Add `updateTweens(entityMeshes)` call to the `animate()` render loop
- [x] **A9:** Add `handleAnimate(msg)` — processes `{type: "animate", animations: [...]}` messages
- [x] **A10:** Add `handleTimeline(msg)` — processes `{type: "timeline", steps: [...]}` messages with staggered `setTimeout` calls
- [x] **A11:** Enhance `updateEntity()` for in-place position, rotation, opacity updates (no remove/recreate for simple changes)
- [x] **A12:** `updateEntity()` falls back to full rebuild for structural changes (radius, extent, kind change)

### 4.3 Python API

- [x] **A13:** Add `animate_to(entity_id, *, position, rotation, opacity, scale, duration, easing)` to `visualizer.py`
- [x] **A14:** Add `Timeline` class with `wait()`, `animate_to()`, `play()` methods
- [x] **A15:** Add `Visualizer.timeline()` factory method
- [x] **A16:** `Timeline.animate_to()` supports `parallel=True` for concurrent animations
- [x] **A17:** Add `_push_raw()` to `server.py` for sending arbitrary JSON (animations, timelines) over WebSocket

### 4.4 Manual Verification

- [x] **A18:** Manual test: Create a point, call `viz.animate_to(id, position=(5,0,0), duration=2)` → smooth movement in browser
- [x] **A19:** Manual test: Create a sphere, `animate_to(id, opacity=0.1, duration=3)` → smooth fade
- [x] **A20:** Manual test: `animate_to()` with new call replaces ongoing tween for the same entity
- [x] **A21:** Manual test: Timeline with 3+ staggered steps executes in correct sequence
- [x] **A22:** Manual test: `parallel=True` steps run concurrently
- [x] **A23:** Manual test: `cancelTween(id)` stops an animation mid-flight
- [x] **A24:** Manual test: Frame streaming at 60 FPS produces smooth motion with `update_entity()` + `flush()`
- [x] **A25:** Manual test: Browser console has no errors during animation
- [x] **A26:** Run unit tests for easing functions (mathematical correctness)

## 5. Verification Checklist

- [ ] Frame streaming: `update_entity()` + `flush()` at 60 FPS produces smooth motion.
- [x] Frame streaming: in-place mesh updates (no remove/recreate) for position/rotation/opacity changes.
- [x] Frame streaming: structural changes (radius, extent) fall back to full rebuild.
- [x] Keyframe: `animate_to()` with position target moves entity smoothly.
- [x] Keyframe: `animate_to()` with opacity target fades entity correctly.
- [x] Keyframe: easing functions produce expected curves (visual check + unit test).
- [x] Keyframe: new `animate_to()` call replaces ongoing tween for the same entity.
- [x] Timeline: steps execute at correct times with correct delays.
- [x] Timeline: `parallel=True` steps run concurrently.
- [x] Browser console has no errors during animation.
- [x] `cancelTween(id)` stops an animation mid-flight.