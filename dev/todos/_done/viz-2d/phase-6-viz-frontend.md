# Phase 6 — Viz Frontend

Add 2D rendering support to the Three.js viewer. When `space_dim == 2`, the
frontend uses an orthographic top‑down camera, pan‑zoom controls, and a planar
grid and axes. All renderers work unchanged — full 3D entities (e.g. `Sphere`
with non‑zero `z`, tilted `Plane`) also render correctly in 2D mode from the
top‑down perspective with no additional code.

## Files to Modify

### `py/pytanga/viz/templates/viewer.js`

The main JavaScript entry point. Changes needed in three areas:

#### A. Camera Setup (`initScene()` → camera creation)

Currently creates a `PerspectiveCamera`. Replace with conditional:

```javascript
// Camera setup
if (sceneConfig && sceneConfig.space_dim === 2) {
    // 2D: orthographic camera, top-down view
    const frustumSize = (sceneConfig.space_extent || 10) * 2;
    const aspect = window.innerWidth / window.innerHeight;
    camera = new THREE.OrthographicCamera(
        frustumSize * aspect / -2,
        frustumSize * aspect / 2,
        frustumSize / 2,
        frustumSize / -2,
        0.1,
        1000
    );
    camera.position.set(0, 0, 20);       // top‑down
    camera.lookAt(0, 0, 0);
} else {
    camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.set(8, 6, 10);       // angled 3D default
    camera.lookAt(0, 0, 0);
}
```

⚠ **Timing issue:** `sceneConfig` arrives after `initScene()` is called
(during the WebSocket handshake). Options:
1. Initialize camera with placeholder, update in `applySceneConfig()`
2. Default to 3D, switch in `applySceneConfig()` when space_dim=2

**Recommended approach (2):** Switch camera type in `applySceneConfig()` when
`space_dim` changes. This avoids the timing problem and supports scene switches.

#### B. Grid Setup (`applySceneConfig()` → grid)

```javascript
if (config.space_dim === 2) {
    // 2D: planar grid in XZ or XY plane, oriented for top‑down view
    const gs = extent * 2;
    // Use GridHelper (creates grid in XZ plane, visible from top‑down)
    window._gridHelper = new THREE.GridHelper(gs, Math.max(gs, 20), 0x444466, 0x222244);
} else {
    // 3D: existing behavior
    window._gridHelper = new THREE.GridHelper(gs, Math.max(gs, 20), 0x444466, 0x222244);
}
```

In 2D mode the standard `GridHelper` (XZ plane + Y up) works perfectly with a
top‑down orthographic camera.

#### C. Axes Setup (`applySceneConfig()` → axes)

```javascript
if (config.space_dim === 2) {
    // 2D: show only X and Y axes, no Z helper
    if (window._axesHelper) { ... dispose ... }
    window._axesHelper = new THREE.AxesHelper(extent);
    // Optionally hide the Z‑axis line. AxesHelper creates 3 lines (RGB→XYZ).
    // For simplicity, use it as‑is (Z‑axis appears as a dot in ortho).
} else {
    // 3D: existing behavior
    window._axesHelper = new THREE.AxesHelper(extent);
}
```

#### D. Camera Auto‑Fit (`fitCameraToScene()`)

When `space_dim == 2`, the camera auto‑fit should use orthographic bounds:

```javascript
function fitCameraToScene() {
    if (entityMeshes.size === 0) return;
    const box = new THREE.Box3();
    entityMeshes.forEach(m => box.expandByObject(m));
    const center = new THREE.Vector3();
    box.getCenter(center);
    const size = new THREE.Vector3();
    box.getSize(size);

    if (sceneConfig && sceneConfig.space_dim === 2) {
        // Orthographic: fit all objects
        const frustumSize = Math.max(size.x, size.y, 1) * 1.2;
        const aspect = window.innerWidth / window.innerHeight;
        camera.left   = frustumSize * aspect / -2;
        camera.right  = frustumSize * aspect / 2;
        camera.top    = frustumSize / 2;
        camera.bottom = frustumSize / -2;
        camera.position.set(center.x, center.y, 20);
        camera.lookAt(center.x, center.y, 0);
        camera.updateProjectionMatrix();
        controls.target.set(center.x, center.y, 0);
    } else {
        // 3D: existing behavior
        const maxDim = Math.max(size.x, size.y, size.z, 1);
        const distance = maxDim * 1.5 + 2;
        camera.position.set(
            center.x + distance * 0.6,
            center.y + distance * 0.5,
            center.z + distance * 0.7
        );
        camera.lookAt(controls.target);
        camera.near = Math.max(0.01, distance * 0.001);
        camera.far = distance * 10;
        camera.updateProjectionMatrix();
    }
    controls.update();
}
```

#### E. Resize Handler (`onResize()`)

When `space_dim == 2`, update orthographic camera frustum:

```javascript
function onResize() {
    if (sceneConfig && sceneConfig.space_dim === 2) {
        const frustumSize = (Math.abs(camera.right - camera.left) + Math.abs(camera.top - camera.bottom)) / 2;
        const aspect = window.innerWidth / window.innerHeight;
        camera.left   = frustumSize * aspect / -2;
        camera.right  = frustumSize * aspect / 2;
        camera.top    = frustumSize / 2;
        camera.bottom = frustumSize / -2;
    }
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
    if (window._labelRenderer) {
        window._labelRenderer.setSize(window.innerWidth, window.innerHeight);
    }
    if (window._viewerContainer) {
        window._viewerContainer.style.width = '100%';
        window._viewerContainer.style.height = '100%';
    }
}
```

### `py/pytanga/viz/templates/controls.js`

Add 2D pan/zoom controls that lock orbit rotation.

```javascript
export function setupControls(camera, renderer) {
    const config = window._sceneConfig;  // available after applySceneConfig

    if (config && config.space_dim === 2) {
        // 2D: enable only pan (right‑click drag) and zoom (scroll)
        const controls = new OrbitControls(camera, renderer.domElement);
        controls.enableRotate = false;       // no orbit rotation
        controls.enableDamping = true;
        controls.dampingFactor = 0.1;
        controls.mouseButtons = {
            LEFT: null,            // no rotation
            MIDDLE: THREE.MOUSE.DOLLY,  // zoom
            RIGHT: THREE.MOUSE.PAN      // pan
        };
        // Alternative: use MapControls which are already pan‑focused
        // const controls = new MapControls(camera, renderer.domElement);
        return controls;
    }

    // 3D: existing OrbitControls setup
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.1;
    // ... existing 3D setup
    return controls;
}
```

⚠ **Timing issue:** `setupControls()` is called from `initScene()` before
`applySceneConfig()` runs. The `controls` reference is already stored, but we
need to adjust its behavior after config arrives.

**Solution:** In `applySceneConfig()`, after setting `sceneConfig`, configure
the controls:

```javascript
function applySceneConfig(config) {
    sceneConfig = config;  // store for use elsewhere
    // ... existing setup ...

    // Adjust controls based on space_dim
    if (config.space_dim === 2) {
        controls.enableRotate = false;
        controls.mouseButtons.LEFT = null;
        controls.mouseButtons.RIGHT = THREE.MOUSE.PAN;
    }
    // ... rest of config application ...
}
```

This approach modifies the existing `OrbitControls` instance rather than
creating a new one, which avoids breaking references held by other code.

### `py/pytanga/viz/templates/controls-attached.js`

No changes needed. Attached controls (sliders, buttons) render the same.

### `py/pytanga/viz/templates/viewer.js` — Overlay Draw Order

When `space_dim == 2`, the `z` coordinate determines stack order (not camera
depth in the projective sense). The frontend must:

```javascript
function applySceneConfig(config) {
    // ... existing setup ...
    if (config.space_dim === 2) {
        // Disable automatic depth testing: entities render in order of
        // their z coordinate, with higher z on top of lower z.
        renderer.sortObjects = false;          // manual render order
        // Each object's renderOrder is set to Math.floor(z * 100) in
        // createEntityMesh or inPlaceUpdate — see entity rendering loop.
    }
    // ... rest of config application ...
}
```

In the entity creation / update path (`createEntityMesh`, `inPlaceUpdate`),
each mesh should have its `renderOrder` set based on position `z`:

```javascript
// In createEntityMesh / inPlaceUpdate, when space_dim == 2:
if (sceneConfig && sceneConfig.space_dim === 2) {
    const z = ent.position ? ent.position[2] : 0;
    // Normalize z to a renderOrder range (e.g. 0–10000)
    mesh.renderOrder = Math.round(z * 100);
    // Disable depthTest so z doesn't cull objects behind each other
    mesh.traverse(child => {
        if (child.material) {
            child.material.depthTest = false;
            child.material.depthWrite = false;
        }
    });
}
```

This ensures:
- `Point(3, 4, 10)` always renders on top of `Point(3, 4, 5)` (visually higher)
- `Point(3, 4, 0)` renders at the base layer
- Users control layering via the `z` field of entity dataclasses

### `py/pytanga/viz/templates/renderers/factory.js`

No changes needed. All entity renderers dispatch on `ent.kind`, which is
the same for 2D entities.

### `py/pytanga/viz/templates/renderers/` (individual renderers)

No changes. All renderers already handle `[x, y, z]` position/vector arrays —
with `z=0` from 2D algebras, the geometry simply lies flat in the Z=0 plane.

### HTML Template (`py/pytanga/viz/templates/viewer.html`)

No changes needed. The viewport layout, CSS, and scripts are the same.

## Implementation Checklist

- [ ] 6.1  Add 2D orthographic camera switch in `applySceneConfig()` (viewer.js)
- [ ] 6.2  Add 2D grid setup in `applySceneConfig()` (viewer.js)
- [ ] 6.3  Add 2D axes setup in `applySceneConfig()` (viewer.js)
- [ ] 6.4  Add orthographic auto‑fit logic in `fitCameraToScene()` (viewer.js)
- [ ] 6.5  Add orthographic resize logic in `onResize()` (viewer.js)
- [ ] 6.6  Disable orbit rotation for 2D mode in `applySceneConfig()` (viewer.js)
- [ ] 6.7  Map RIGHT mouse button to pan in 2D mode (viewer.js)
- [ ] 6.8  Verify: 3D viewer unchanged when `space_dim` is absent or 3
- [ ] 6.9  Verify: 2D viewer shows orthographic top‑down view
- [ ] 6.10 Verify: 2D viewer pan (right‑click drag) works
- [ ] 6.11 Verify: 2D viewer zoom (scroll wheel) works
- [ ] 6.12 Verify: 2D viewer rotation (left‑click drag) does NOT orbit
- [ ] 6.13 Verify: entities render correctly in 2D (e.g. `Point(3, 4, 0)` appears on grid)
- [ ] 6.14 Verify: grid and axes display correctly in orthographic view
- [ ] 6.15 Verify: screenshot capture works in 2D mode (`Ctrl+S`)
- [ ] 6.16 Verify: resize behavior correct for 2D orthographic camera