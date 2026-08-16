# Phase 5 — Frontend `interaction.js`

**Prerequisites:** Phase 1 (interaction config field exists in entity JSON)

**Goal:** Create `py/pytanga/viz/templates/interaction.js` — the Three.js
frontend module that captures pointer events on interactive objects, applies
throttling, and sends JSON messages to the Python backend over WebSocket.

---

## 1. New File: `py/pytanga/viz/templates/interaction.js`

### 1.1 Module Overview

```js
// Tanga Interaction — Pointer event capture for interactive 3D objects.
//
// Responsibilities:
//   - Track which meshes are interactive (per their entity JSON "interaction" field)
//   - Raycaster on pointermove to detect hover + scroll targets
//   - Throttle events per (object_id, event_type) using config.throttle_ms
//   - Drag with setPointerCapture + OrbitControls conflict resolution
//   - Click / double-click detection (distance + time threshold)
//   - Scroll wheel capture (non-passive, only when hovering interactive object)
//   - Compute delta_transform 4×4 matrix per drag event
//   - Construct JSON messages and send via WebSocket

import * as THREE from 'three';

// ── State ──

const interactiveObjects = new Map();  // objectId → { mesh, config }
let ws = null;
let raycaster = new THREE.Raycaster();
let mouse = new THREE.Vector2();
let camera = null;
let rendererDomElement = null;
let controls = null;

// Throttling state: "objectId:eventType" → { lastSent, pendingTimer, pendingData }
const _throttles = new Map();

// Drag state
let _activeDrag = null;  // { objectId, button, modifiers, startPos, lastPos, pointerId }
let _dragStarted = false;  // true once we've sent drag_start

// Click detection state
const _clickState = new Map();  // objectId → { pointerDownPos, pointerDownTime, button, modifiers }

// Double-click timeout (ms)
const DBLCLICK_TIMEOUT = 300;
// Click movement threshold (pixels)
const CLICK_THRESHOLD = 3;
```

### 1.2 Initialization

```js
export function initInteraction(_camera, _rendererDomElement, _controls, websocket) {
    camera = _camera;
    rendererDomElement = _rendererDomElement;
    controls = _controls;
    ws = websocket;

    // Pointer events on the canvas
    rendererDomElement.addEventListener('pointerdown', onPointerDown);
    rendererDomElement.addEventListener('pointermove', onPointerMove);
    rendererDomElement.addEventListener('pointerup', onPointerUp);
    // Pointer capture events (for tracking lost capture)
    rendererDomElement.addEventListener('lostpointercapture', onLostCapture);

    // Scroll wheel (non-passive to prevent default)
    rendererDomElement.addEventListener('wheel', onWheel, { passive: false });

    // Double-click (uses browser dblclick event but also manual detection)
    rendererDomElement.addEventListener('dblclick', onDblClick);
}
```

### 1.3 Object Registration

```js
export function registerInteractive(objectId, mesh, config) {
    // config is the parsed "interaction" field from entity JSON
    if (!config || !config.enabled) return;
    interactiveObjects.set(objectId, { mesh, config });
}

export function unregisterInteractive(objectId) {
    interactiveObjects.delete(objectId);
    // Clean up throttles
    for (const key of _throttles.keys()) {
        if (key.startsWith(objectId + ':')) {
            const entry = _throttles.get(key);
            if (entry.pendingTimer) clearTimeout(entry.pendingTimer);
            _throttles.delete(key);
        }
    }
    // Clean up click state
    _clickState.delete(objectId);
    // If this object is being dragged, cancel
    if (_activeDrag && _activeDrag.objectId === objectId) {
        cancelDrag();
    }
}

export function clearAllInteractive() {
    interactiveObjects.clear();
    for (const entry of _throttles.values()) {
        if (entry.pendingTimer) clearTimeout(entry.pendingTimer);
    }
    _throttles.clear();
    _clickState.clear();
    cancelDrag();
}
```

### 1.4 Trigger Matching

```js
function findMatchingTriggers(objectId, eventType, button, modifiers) {
    const obj = interactiveObjects.get(objectId);
    if (!obj) return [];
    return obj.config.triggers.filter(t => {
        if (t.event_type !== eventType) return false;
        if (t.mouse_button != null && t.mouse_button !== button) return false;
        // Check modifiers: all required modifiers must be present
        const reqMods = t.modifiers || [];
        if (reqMods.length > 0) {
            for (const m of reqMods) {
                if (!modifiers.has(m)) return false;
            }
            // Also check: no extra modifiers? (strict match)
            // For now: allow extra modifiers (be permissive)
        }
        return true;
    });
}

function getActiveModifiers(event) {
    const mods = new Set();
    if (event.ctrlKey || event.metaKey) mods.add('ctrl');
    if (event.shiftKey) mods.add('shift');
    if (event.altKey) mods.add('alt');
    return mods;
}

function mouseButtonFromEvent(event) {
    // PointerEvent.button: 0=left, 1=middle, 2=right
    switch (event.button) {
        case 0: return 'left';
        case 1: return 'middle';
        case 2: return 'right';
        default: return 'left';
    }
}
```

### 1.5 Raycasting

```js
function getInteractiveHit(event) {
    // Build list of interactive meshes
    const meshes = [];
    for (const [id, obj] of interactiveObjects) {
        meshes.push(obj.mesh);
    }
    if (meshes.length === 0) return null;

    // Update mouse NDC from pointer event
    const rect = rendererDomElement.getBoundingClientRect();
    mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    raycaster.setFromCamera(mouse, camera);
    const intersects = raycaster.intersectObjects(meshes, true);

    if (intersects.length === 0) return null;

    // Find which registered object the hit mesh belongs to
    const hitMesh = intersects[0].object;
    for (const [id, obj] of interactiveObjects) {
        if (obj.mesh === hitMesh || isDescendantOf(hitMesh, obj.mesh)) {
            return {
                objectId: id,
                intersect: intersects[0],
            };
        }
    }
    return null;
}

function isDescendantOf(child, ancestor) {
    let cur = child;
    while (cur) {
        if (cur === ancestor) return true;
        cur = cur.parent;
    }
    return false;
}
```

### 1.6 Throttling

```js
function getInteractionEventTypes() {
    // Map our internal event type strings to the JSON "event_type" values
    return {
        click: 'click',
        dblclick: 'dblclick',
        drag_start: 'drag_start',
        drag_move: 'drag_move',
        drag_end: 'drag_end',
        scroll: 'scroll',
    };
}

function throttledSend(objectId, eventType, buildPayload) {
    const obj = interactiveObjects.get(objectId);
    if (!obj) return;
    const throttleMs = obj.config.throttle_ms || 0;
    const key = objectId + ':' + eventType;

    if (throttleMs <= 0) {
        // No throttling — send immediately
        ws.send(JSON.stringify(buildPayload()));
        return;
    }

    const now = performance.now();
    const entry = _throttles.get(key);

    if (entry && entry.lastSent && (now - entry.lastSent) < throttleMs) {
        // Within throttle window — save as pending, overwriting previous
        entry.pendingData = buildPayload;
        if (!entry.pendingTimer) {
            const remaining = throttleMs - (now - entry.lastSent);
            entry.pendingTimer = setTimeout(() => {
                flushThrottle(key);
            }, remaining);
        }
    } else {
        // Outside throttle window — send immediately
        if (entry && entry.pendingTimer) {
            clearTimeout(entry.pendingTimer);
            entry.pendingTimer = null;
        }
        _throttles.set(key, { lastSent: now, pendingTimer: null, pendingData: null });
        ws.send(JSON.stringify(buildPayload()));
    }
}

function flushThrottle(key) {
    const entry = _throttles.get(key);
    if (!entry || !entry.pendingData) return;
    ws.send(JSON.stringify(entry.pendingData()));
    entry.lastSent = performance.now();
    entry.pendingData = null;
    entry.pendingTimer = null;
}
```

### 1.7 Delta Transform Computation

```js
function computeDeltaTransform(intersectPoint) {
    // Compute the 4×4 row-major matrix mapping pixel deltas → world-space deltas
    // at the depth of the intersection point.
    //
    // screen_scale = 2 * dist * tan(fov/2) / viewport_height_px
    // row_0 = right * scale   (screen +X → world)
    // row_1 = up * scale      (screen -Y → world)
    // row_2 = forward * scale (depth    → world)
    // row_3 = [0, 0, 0, 1]

    const dist = intersectPoint.distanceTo(camera.position);
    const vFov = camera.fov * Math.PI / 180;
    const viewportHeight = rendererDomElement.clientHeight;
    const scale = 2 * dist * Math.tan(vFov / 2) / viewportHeight;

    // Camera basis vectors in world space
    const right = new THREE.Vector3();
    const up = new THREE.Vector3();
    const forward = new THREE.Vector3();
    camera.matrixWorld.extractBasis(right, up, forward);
    // In Three.js, camera looks along -Z in local space, so the world forward
    // direction from extractBasis is actually the camera's -Z axis.
    // We want the view direction (toward the scene), which is -forward
    // (or equivalently, we compute from camera to point).
    const viewDir = new THREE.Vector3().subVectors(intersectPoint, camera.position).normalize();

    right.normalize().multiplyScalar(scale);
    up.normalize().multiplyScalar(scale);
    const depthVec = viewDir.clone().multiplyScalar(scale);

    return [
        right.x, right.y, right.z, 0,
        -up.x, -up.y, -up.z, 0,    // screen -Y → world
        depthVec.x, depthVec.y, depthVec.z, 0,
        0, 0, 0, 1,
    ];
}
```

### 1.8 Pointer Event Handlers

```js
function onPointerDown(event) {
    const hit = getInteractiveHit(event);
    if (!hit) return;

    const modifiers = getActiveModifiers(event);
    const button = mouseButtonFromEvent(event);

    // Check for drag triggers
    const dragTriggers = findMatchingTriggers(hit.objectId, 'drag', button, modifiers);

    if (dragTriggers.length > 0) {
        // Initiate drag with pointer capture
        _activeDrag = {
            objectId: hit.objectId,
            button: button,
            modifiers: modifiers,
            startPos: { x: event.clientX, y: event.clientY },
            lastPos: { x: event.clientX, y: event.clientY },
            pointerId: event.pointerId,
        };
        _dragStarted = false;
        rendererDomElement.setPointerCapture(event.pointerId);
        // Disable OrbitControls during drag
        if (controls) controls.enabled = false;
        event.preventDefault();
        event.stopPropagation();
    }

    // Track for click detection
    _clickState.set(hit.objectId, {
        pointerDownPos: { x: event.clientX, y: event.clientY },
        pointerDownTime: performance.now(),
        button: button,
        modifiers: modifiers,
    });
}

function onPointerMove(event) {
    // If dragging, handle drag move
    if (_activeDrag) {
        const dx = event.clientX - _activeDrag.lastPos.x;
        const dy = event.clientY - _activeDrag.lastPos.y;
        _activeDrag.lastPos = { x: event.clientX, y: event.clientY };

        // Re-cast raycaster to get current world position under the pointer
        const hit = getInteractiveHit(event);
        if (!hit || hit.objectId !== _activeDrag.objectId) {
            // Mouse moved off the object — still report drag (pointer is captured)
            // Use last known world position, or don't update world_position
        }

        const worldPos = hit ? hit.intersect.point : null;
        const deltaTransform = hit ? computeDeltaTransform(worldPos) : null;

        const eventType = _dragStarted ? 'drag_move' : 'drag_start';

        const payload = () => ({
            type: 'interaction:' + eventType,
            event_type: eventType,
            object_id: _activeDrag.objectId,
            mouse_button: _activeDrag.button,
            modifiers: Array.from(_activeDrag.modifiers),
            screen_position: [event.clientX, event.clientY],
            delta_pixels: [dx, dy],
            world_position: worldPos ? [worldPos.x, worldPos.y, worldPos.z] : [0, 0, 0],
            delta_transform: deltaTransform || [],
        });

        throttledSend(_activeDrag.objectId, eventType, payload);

        if (!_dragStarted) {
            _dragStarted = true;
        }
        event.preventDefault();
        return;
    }

    // Not dragging — update hover (for scroll target detection)
    // This is handled implicitly by getInteractiveHit on wheel events
}

function onPointerUp(event) {
    const hit = getInteractiveHit(event);
    const objectId = hit ? hit.objectId : (_activeDrag ? _activeDrag.objectId : null);

    // Handle drag end
    if (_activeDrag && _activeDrag.pointerId === event.pointerId) {
        // Send drag_end
        const hit2 = getInteractiveHit(event);
        const worldPos = hit2 ? hit2.intersect.point : null;
        const deltaTransform = hit2 ? computeDeltaTransform(worldPos) : null;

        const payload = {
            type: 'interaction:drag_end',
            event_type: 'drag_end',
            object_id: _activeDrag.objectId,
            mouse_button: _activeDrag.button,
            modifiers: Array.from(_activeDrag.modifiers),
            screen_position: [event.clientX, event.clientY],
            delta_pixels: [event.clientX - _activeDrag.startPos.x, event.clientY - _activeDrag.startPos.y],
            world_position: worldPos ? [worldPos.x, worldPos.y, worldPos.z] : [0, 0, 0],
            delta_transform: deltaTransform || [],
        };
        ws.send(JSON.stringify(payload));

        // Release capture and re-enable controls
        rendererDomElement.releasePointerCapture(event.pointerId);
        if (controls) controls.enabled = true;
        _activeDrag = null;
        _dragStarted = false;
        return;
    }

    // Handle click
    if (objectId) {
        const state = _clickState.get(objectId);
        if (state) {
            const dx = event.clientX - state.pointerDownPos.x;
            const dy = event.clientY - state.pointerDownPos.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            const elapsed = performance.now() - state.pointerDownTime;

            if (dist < CLICK_THRESHOLD && elapsed < DBLCLICK_TIMEOUT) {
                // Check for click triggers
                const button = mouseButtonFromEvent(event);
                const modifiers = getActiveModifiers(event);
                const triggers = findMatchingTriggers(objectId, 'click', button, modifiers);

                if (triggers.length > 0 && hit) {
                    const worldPos = hit.intersect.point;
                    const normal = hit.intersect.face ? hit.intersect.face.normal : new THREE.Vector3(0, 0, 1);
                    const payload = {
                        type: 'interaction:click',
                        event_type: 'click',
                        object_id: objectId,
                        mouse_button: button,
                        modifiers: Array.from(modifiers),
                        screen_position: [event.clientX, event.clientY],
                        world_position: [worldPos.x, worldPos.y, worldPos.z],
                        world_normal: [normal.x, normal.y, normal.z],
                    };
                    ws.send(JSON.stringify(payload));
                }
            }
            _clickState.delete(objectId);
        }
    }

    if (_activeDrag) {
        cancelDrag();
    }
}

function onDblClick(event) {
    const hit = getInteractiveHit(event);
    if (!hit) return;

    const button = mouseButtonFromEvent(event);
    const modifiers = getActiveModifiers(event);
    const triggers = findMatchingTriggers(hit.objectId, 'dblclick', button, modifiers);

    if (triggers.length > 0) {
        const worldPos = hit.intersect.point;
        const normal = hit.intersect.face ? hit.intersect.face.normal : new THREE.Vector3(0, 0, 1);
        const payload = {
            type: 'interaction:dblclick',
            event_type: 'dblclick',
            object_id: hit.objectId,
            mouse_button: button,
            modifiers: Array.from(modifiers),
            screen_position: [event.clientX, event.clientY],
            world_position: [worldPos.x, worldPos.y, worldPos.z],
            world_normal: [normal.x, normal.y, normal.z],
        };
        ws.send(JSON.stringify(payload));
    }
}

function onWheel(event) {
    // Check if hovering an interactive object
    const hit = getInteractiveHit(event);
    if (!hit) return;

    const modifiers = getActiveModifiers(event);
    const triggers = findMatchingTriggers(hit.objectId, 'scroll', null, modifiers);

    if (triggers.length > 0) {
        event.preventDefault();
        const payload = () => ({
            type: 'interaction:scroll',
            event_type: 'scroll',
            object_id: hit.objectId,
            modifiers: Array.from(modifiers),
            screen_position: [event.clientX, event.clientY],
            delta_xy: [event.deltaX, event.deltaY],
        });
        throttledSend(hit.objectId, 'scroll', payload);
    }
}

function onLostCapture(event) {
    if (_activeDrag) {
        cancelDrag();
    }
}

function cancelDrag() {
    if (_activeDrag) {
        // Send drag_end if we started
        if (_dragStarted) {
            const payload = {
                type: 'interaction:drag_end',
                event_type: 'drag_end',
                object_id: _activeDrag.objectId,
                mouse_button: _activeDrag.button,
                modifiers: Array.from(_activeDrag.modifiers),
                screen_position: [_activeDrag.lastPos.x, _activeDrag.lastPos.y],
                delta_pixels: [0, 0],
                world_position: [0, 0, 0],
                delta_transform: [],
            };
            try { ws.send(JSON.stringify(payload)); } catch (e) {}
        }
        if (controls) controls.enabled = true;
        _activeDrag = null;
        _dragStarted = false;
    }
}
```

### 1.9 Export

```js
export function setWebSocket(websocket) {
    ws = websocket;
}
```

The module also needs to track the current hovered object so that `onWheel`
works without a `pointermove` immediately before. This can be done by storing
the last hit result in a global variable updated on each `pointermove`.

---

## 2. Hovered Object Tracking (Addition)

Add to the state section:

```js
let _hoveredObjectId = null;
```

In `onPointerMove` (non-drag case), update:

```js
function onPointerMove(event) {
    if (_activeDrag) {
        // ... drag handling ...
        return;
    }

    const hit = getInteractiveHit(event);
    _hoveredObjectId = hit ? hit.objectId : null;
}
```

Then `onWheel` can also check `_hoveredObjectId` if `getInteractiveHit(event)`
doesn't find a hit (some browsers fire wheel without a corresponding
pointermove on the canvas).

---

## 3. Implementation Checklist

- [ ] Create `py/pytanga/viz/templates/interaction.js`
- [ ] Implement `initInteraction()` with event listener setup
- [ ] Implement `registerInteractive()` / `unregisterInteractive()` / `clearAllInteractive()`
- [ ] Implement trigger matching (`findMatchingTriggers`, `getActiveModifiers`, `mouseButtonFromEvent`)
- [ ] Implement raycaster helper (`getInteractiveHit`, `isDescendantOf`)
- [ ] Implement throttling (`throttledSend`, `flushThrottle`)
- [ ] Implement `computeDeltaTransform()` 4×4 matrix
- [ ] Implement `onPointerDown` — detect drag start, begin pointer capture
- [ ] Implement `onPointerMove` — drag move with delta + re-raycast; hover tracking
- [ ] Implement `onPointerUp` — drag end, click detection
- [ ] Implement `onDblClick` — double-click handler
- [ ] Implement `onWheel` — scroll capture (non-passive)
- [ ] Implement `onLostCapture` — cleanup if capture is lost
- [ ] Implement `cancelDrag()` — clean release
- [ ] Export `setWebSocket` for reconnection support

---

## 4. Verification

- [ ] Drag on interactive object with matching triggers → `interaction:drag_start`, `interaction:drag_move`, `interaction:drag_end` messages sent
- [ ] Drag outside browser window → events continue (pointer capture)
- [ ] OrbitControls disabled during drag, re-enabled on drag end
- [ ] Click on interactive object → `interaction:click` sent (only if no significant movement)
- [ ] Double-click → `interaction:dblclick` sent
- [ ] Scroll while hovering → `interaction:scroll` sent (non-passive, default prevented)
- [ ] Throttling: rapid events → only sent at throttle_ms interval
- [ ] `delta_transform` contains correct 4×4 matrix (16 floats)
- [ ] `unregisterInteractive()` cleans up throttles and state
- [ ] `clearAllInteractive()` resets everything