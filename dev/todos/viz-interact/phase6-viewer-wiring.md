# Phase 6 — Viewer & Controls Wiring

**Prerequisites:** Phase 5 (interaction.js exists)

**Goal:** Wire `interaction.js` into `viewer.js` (entity lifecycle) and expose
`controls.enabled` from `controls.js` for drag conflict resolution.

---

## 1. Motivation

The `interaction.js` module needs to be imported and initialized from
`viewer.js`, and must be notified whenever entities are created, updated,
or removed. The `controls.js` module needs to expose its `controls.enabled`
property so interaction.js can toggle it during drags.

---

## 2. Modified File: `py/pytanga/viz/templates/controls.js`

### 2.1 Current State

`controls.js` exports `setupControls()` which creates an `OrbitControls`
instance and returns it. There is no external access to `controls.enabled`.

### 2.2 Required Change

No change needed — `viewer.js` already stores the controls reference in the
module-level `controls` variable. The `interaction.js` module receives it via
`initInteraction()` and can directly set `controls.enabled`. This works
because controls is a plain Three.js object with an `enabled` property.

If `controls.js` needs an explicit getter (unlikely), simply re-export the
controls instance. But the existing pattern of passing it to
`initInteraction()` is sufficient.

---

## 3. Modified File: `py/pytanga/viz/templates/viewer.js`

### 3.1 Import

Add at top of `viewer.js`:

```js
import {
    initInteraction,
    registerInteractive,
    unregisterInteractive,
    clearAllInteractive,
    setWebSocket as setInteractionWebSocket,
} from './interaction.js';
```

### 3.2 Initialization

In `initScene()`, after controls are created:

```js
if (webglOk && renderer) {
    controls = setupControls(camera, renderer);
    // Initialize interaction system
    initInteraction(camera, renderer.domElement, controls, ws);
    // ... existing keyboard shortcut code ...
}
```

### 3.3 WebSocket Reconnection

In `connectWebSocket()` → `ws.onopen`:

```js
ws.onopen = () => {
    // ... existing reconnection code ...
    setWebSocket(ws);
    setInteractionWebSocket(ws);  // ← NEW: update interaction module
    // ... existing ready payload ...
};
```

### 3.4 Entity Lifecycle Integration

The `viewer.js` module already has `handleMessage()` → `scene_update` handling
which calls `createEntityMesh()` and adds meshes to `entityMeshes` map.

**On entity creation** (in `upsertObject()` and `updateEntity()` after mesh is created):

```js
// After entityMeshes.set(id, mesh) and scene.add(mesh):
if (msg.interaction) {
    registerInteractive(msg.id, mesh, msg.interaction);
}
```

This needs access to the raw entity data (`msg`). In `upsertObject()`, the
`msg` object already contains the full entity data including the
`interaction` field. In `updateEntity()`, the merged entity data
(`{...existing, ...ent}`) should be used.

**On entity removal** (in `handleMessage()` → `scene_update` → `msg.removed`):

```js
if (msg.removed) {
    for (const id of msg.removed) {
        unregisterInteractive(id);  // ← NEW
        // ... existing removal code ...
    }
}
```

**On `clear_all`** (in `handleMessage()` → `clear_all`):

```js
if (msg.type === 'clear_all') {
    clearAllInteractive();  // ← NEW
    // ... existing clear_all code ...
}
```

### 3.5 Specific Integration Points

In `upsertObject()`:

```js
async function upsertObject(msg) {
    // ... existing code to remove old object ...
    if (msg.layer === 'scene') {
        const mesh = await createEntityMesh(msg);
        if (mesh) {
            // ... existing position + scene.add code ...
            sceneObjects.set(msg.id, { obj: mesh, layer: 'scene' });
            entityMeshes.set(msg.id, mesh);
            entityData.set(msg.id, { ...msg });

            // ── Interaction ──
            if (msg.interaction) {
                registerInteractive(msg.id, mesh, msg.interaction);
            }
        }
    }
    // ... overlay handling ...
}
```

In `updateEntity()`:

```js
async function updateEntity(ent) {
    // ... existing code ...
    const mesh = await createEntityMesh({ ...existing, ...ent });
    if (mesh) {
        // ... existing scene.add + set code ...
        entityData.set(id, { ...existing, ...ent });

        // ── Interaction ──
        const merged = { ...existing, ...ent };
        if (merged.interaction) {
            registerInteractive(id, mesh, merged.interaction);
        }
    }
}
```

---

## 4. Thread Safety / Event Loop Considerations

All `interaction.js` functions are synchronous DOM operations and WebSocket
sends. They run on the browser's main thread (the event loop). Three.js
rendering also runs on the main thread. No threading issues.

The only concern is that `registerInteractive()` stores a reference to a
`THREE.Mesh`. If the mesh is later disposed without calling
`unregisterInteractive()`, the raycaster will hit-test a disposed mesh
(which Three.js handles gracefully — no crash, but the hit test may return
unexpected results or nothing). The cleanup in `msg.removed` and `clear_all`
should prevent this.

---

## 5. Implementation Checklist

- [ ] Import `interaction.js` functions in `viewer.js`
- [ ] Call `initInteraction(camera, renderer.domElement, controls, ws)` after controls setup
- [ ] Call `setInteractionWebSocket(ws)` on WebSocket reconnection
- [ ] Call `registerInteractive(id, mesh, config)` after mesh creation in `upsertObject()`
- [ ] Call `registerInteractive(id, mesh, config)` after mesh creation in `updateEntity()`
- [ ] Call `unregisterInteractive(id)` for each removed entity in `msg.removed`
- [ ] Call `clearAllInteractive()` in `clear_all` message handler
- [ ] Verify controls is accessible for `controls.enabled` toggling (already passed to `initInteraction`)

---

## 6. Verification

- [ ] Entity added with `"interaction"` field → `interaction.js` tracks it
- [ ] Entity removed → `interaction.js` stops tracking it
- [ ] `clear_all` → all interactive objects unregistered
- [ ] `update_entity()` updates interaction config (if new config sent)
- [ ] WebSocket reconnect → interaction module uses new WebSocket
- [ ] Drag on interactive object → OrbitControls disabled during drag