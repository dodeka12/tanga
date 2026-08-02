# Phase 4: Frontend Core — Three.js Scene, WebSocket Client, OrbitControls

**Files:** `py/pytanga/viz/templates/viewer.html`, `py/pytanga/viz/templates/viewer.js`, `py/pytanga/viz/templates/controls.js`

**Goal:** Build the core HTML/JS frontend: a fullscreen Three.js canvas with orbit controls,
a WebSocket client that receives scene updates, and a render loop that displays entities.

**Prerequisites:** Phase 3 (server serving static files and WebSocket endpoint)

---

## 1. viewer.html

A minimal HTML shell that loads Three.js via CDN import map and bootstraps the JS modules.
The `<title>` is set dynamically from the `scene_config` message.

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Tanga 3D Viewer</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    html, body { width: 100%; height: 100%; overflow: hidden; background: #1a1a2e; }
    canvas { display: block; }
    #status {
      position: fixed; top: 16px; left: 50%; transform: translateX(-50%);
      color: #888; font-family: monospace; font-size: 13px;
      background: rgba(0,0,0,0.6); padding: 6px 16px; border-radius: 4px;
      pointer-events: none; transition: opacity 0.3s;
    }
    #status.connected { color: #4f4; }
    #status.disconnected { color: #f44; }
  </style>
</head>
<body>
  <div id="status" class="disconnected">Connecting...</div>

  <script type="importmap">
  {
    "imports": {
      "three": "https://unpkg.com/three@0.168.0/build/three.module.js",
      "three/addons/": "https://unpkg.com/three@0.168.0/examples/jsm/"
    }
  }
  </script>

  <script type="module" src="viewer.js"></script>
</body>
</html>
```

The CSS for labels is defined inline in viewer.js via the CSS2DRenderer. Labels are
DOM `<div>` elements positioned in 3D space that always face the camera. The label
styling (font-size, color, background) comes from the entity's `label_*` properties
or global defaults.
```

---

## 2. viewer.js

The main JS entry point. Sets up:
- Three.js renderer, scene, camera, lights
- WebSocket client
- Entity registry (map of ID → THREE.Object3D)
- Render loop via `requestAnimationFrame`
- Status indicator

```js
// py/pytanga/viz/templates/viewer.js

import * as THREE from 'three';
import { CSS2DRenderer } from 'three/addons/renderers/CSS2DRenderer.js';
import { setupControls } from './controls.js';
import { createEntityMesh } from './renderers/factory.js';
import { removeEntityMesh } from './renderers/factory.js';

// ── State ───────────────────────────────────────────────────
const entityMeshes = new Map();   // id → THREE.Object3D
const entityData = new Map();     // id → raw JSON entity data (for diffing)

let scene, camera, renderer, controls;
let ws = null;
let reconnectTimer = null;

// ── Scene Setup ──────────────────────────────────────────────
function initScene() {
  // WebGL Renderer
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(window.devicePixelRatio);
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.shadowMap.enabled = false;  // skip shadows for performance
  document.body.appendChild(renderer.domElement);

  // CSS2D Renderer — for entity labels (crisp HTML text in 3D space)
  window._labelRenderer = new CSS2DRenderer();
  window._labelRenderer.setSize(window.innerWidth, window.innerHeight);
  window._labelRenderer.domElement.style.position = 'absolute';
  window._labelRenderer.domElement.style.top = '0px';
  window._labelRenderer.domElement.style.pointerEvents = 'none';  // let clicks pass through
  document.body.appendChild(window._labelRenderer.domElement);

  // Scene (background color set later from scene_config)
  scene = new THREE.Scene();
  scene.fog = null;

  // Camera (default values, overridden by scene_config)
  camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.1, 1000);
  camera.position.set(8, 6, 10);
  camera.lookAt(0, 0, 0);

  // Lights (independent of scene_config)
  const ambient = new THREE.AmbientLight(0xffffff, 0.5);
  scene.add(ambient);

  const directional = new THREE.DirectionalLight(0xffffff, 0.8);
  directional.position.set(10, 20, 10);
  scene.add(directional);

  const directional2 = new THREE.DirectionalLight(0xffffff, 0.3);
  directional2.position.set(-5, -2, -8);
  scene.add(directional2);

  // Grid & Axes — created but visibility/size controlled by scene_config
  window._gridHelper = new THREE.GridHelper(20, 20, 0x444466, 0x222244);
  scene.add(window._gridHelper);

  window._axesHelper = new THREE.AxesHelper(5);
  scene.add(window._axesHelper);

  // Controls
  controls = setupControls(camera, renderer);

  // Resize handler
  window.addEventListener('resize', onResize);
}

function onResize() {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
  if (window._labelRenderer) {
    window._labelRenderer.setSize(window.innerWidth, window.innerHeight);
  }
}

// ── WebSocket Client ────────────────────────────────────────
function connectWebSocket() {
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const url = `${protocol}//${location.host}/ws`;

  ws = new WebSocket(url);

  ws.onopen = () => {
    setStatus('connected', 'Connected');
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
    // Request full state sync
    ws.send(JSON.stringify({ type: 'ready' }));
  };

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      handleMessage(msg);
    } catch (e) {
      console.error('Failed to parse WebSocket message:', e);
    }
  };

  ws.onclose = () => {
    setStatus('disconnected', 'Disconnected — reconnecting...');
    reconnectTimer = setTimeout(connectWebSocket, 2000);
  };

  ws.onerror = () => {
    // onclose will fire next; no need to handle here
  };
}

function setStatus(cls, text) {
  const el = document.getElementById('status');
  if (!el) return;
  el.className = cls;
  el.textContent = text;
}

// ── Scene Config Handler ─────────────────────────────────────

/** Scene configuration received from the server. */
let sceneConfig = null;

function applySceneConfig(config) {
  sceneConfig = config;

  // Background color
  if (config.background_color) {
    scene.background = new THREE.Color(config.background_color);
  }

  // Space extent — affects grid size
  const extent = config.space_extent || 10;

  // Rebuild grid with configured extent
  if (window._gridHelper) {
    scene.remove(window._gridHelper);
    window._gridHelper.geometry.dispose();
    window._gridHelper.material.dispose();
  }
  if (config.show_grid !== false) {
    const gridSize = extent * 2;
    const divisions = Math.max(gridSize, 20);
    window._gridHelper = new THREE.GridHelper(gridSize, divisions, 0x444466, 0x222244);
    scene.add(window._gridHelper);
  }

  // Rebuild axes with configured extent
  if (window._axesHelper) {
    scene.remove(window._axesHelper);
    window._axesHelper.geometry?.dispose();
    window._axesHelper.material?.dispose();
  }
  if (config.show_axes !== false) {
    window._axesHelper = new THREE.AxesHelper(extent);
    scene.add(window._axesHelper);
  }

  // Apply explicit camera settings if provided
  const camConfig = config.camera;
  if (camConfig) {
    if (camConfig.position) {
      camera.position.set(camConfig.position[0], camConfig.position[1], camConfig.position[2]);
    }
    if (camConfig.target) {
      controls.target.set(camConfig.target[0], camConfig.target[1], camConfig.target[2]);
    }
    if (camConfig.fov) {
      camera.fov = camConfig.fov;
      camera.updateProjectionMatrix();
    }
    if (camConfig.near) {
      camera.near = camConfig.near;
      camera.updateProjectionMatrix();
    }
    if (camConfig.far) {
      camera.far = camConfig.far;
      camera.updateProjectionMatrix();
    }
    controls.update();
  }
}

function fitCameraToScene() {
  // Only auto-fit if no explicit camera config was provided (or only partial config)
  const camConfig = sceneConfig?.camera;

  if (entityMeshes.size === 0) return;

  const box = new THREE.Box3();
  entityMeshes.forEach(mesh => {
    box.expandByObject(mesh);
  });

  const center = new THREE.Vector3();
  box.getCenter(center);
  const size = new THREE.Vector3();
  box.getSize(size);
  const maxDim = Math.max(size.x, size.y, size.z, 1);
  const distance = maxDim * 1.5 + 2;

  // Only set what wasn't explicitly configured
  if (!camConfig || !camConfig.target) {
    controls.target.copy(center);
  }
  if (!camConfig || !camConfig.position) {
    camera.position.set(
      center.x + distance * 0.6,
      center.y + distance * 0.5,
      center.z + distance * 0.7
    );
    camera.lookAt(controls.target);
  }

  // Set near/far clipping based on scene scale if not explicit
  if (!camConfig || !camConfig.near) {
    camera.near = Math.max(0.01, distance * 0.001);
  }
  if (!camConfig || !camConfig.far) {
    camera.far = distance * 10;
  }
  camera.updateProjectionMatrix();
  controls.update();
}

// ── Message Handler ─────────────────────────────────────────
function handleMessage(msg) {
  if (msg.type === 'scene_config') {
    applySceneConfig(msg);
  }
  else if (msg.type === 'scene_update') {
    // Remove deleted entities
    if (msg.removed) {
      for (const id of msg.removed) {
        removeEntityMesh(entityMeshes.get(id));
        entityMeshes.delete(id);
        entityData.delete(id);
      }
    }

    // Add / update entities
    if (msg.entities) {
      for (const ent of msg.entities) {
        updateEntity(ent);
      }
    }

    // Auto-fit camera after first scene update (if no explicit camera config)
    if (!window._cameraPositioned && entityMeshes.size > 0) {
      const camConfig = sceneConfig?.camera;
      // Only auto-fit if no explicit camera was provided at all, or only partial
      if (!camConfig || (!camConfig.position && !camConfig.target)) {
        fitCameraToScene();
      }
      window._cameraPositioned = true;
    }
  }
}

function updateEntity(ent) {
  const id = ent.id;
  const existing = entityData.get(id);

  if (!existing) {
    // New entity
    const mesh = createEntityMesh(ent);
    if (mesh) {
      scene.add(mesh);
      entityMeshes.set(id, mesh);
    }
    entityData.set(id, { ...ent });
  } else {
    // Existing entity — update if changed
    // (Phase 4: simple full replacement. Phase 6: diff-based updates for animation.)
    removeEntityMesh(entityMeshes.get(id));
    entityMeshes.delete(id);

    const mesh = createEntityMesh(ent);
    if (mesh) {
      scene.add(mesh);
      entityMeshes.set(id, mesh);
    }
    entityData.set(id, { ...ent });
  }
}

// ── Render Loop ─────────────────────────────────────────────
function animate() {
  requestAnimationFrame(animate);

  controls.update();

  renderer.render(scene, camera);
  if (window._labelRenderer) {
    window._labelRenderer.render(scene, camera);
  }
}

// ── Bootstrap ───────────────────────────────────────────────
initScene();
connectWebSocket();
animate();
```

---

## 3. controls.js

Encapsulates OrbitControls setup with Tanga-friendly defaults.

```js
// py/pytanga/viz/templates/controls.js

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

export function setupControls(camera, renderer) {
  const controls = new OrbitControls(camera, renderer.domElement);

  // Interaction mapping
  controls.mouseButtons = {
    LEFT: THREE.MOUSE.ROTATE,
    MIDDLE: THREE.MOUSE.PAN,
    RIGHT: THREE.MOUSE.ZOOM,
  };

  // Touch support (optional, Phase 7)
  controls.touches = {
    ONE: THREE.TOUCH.ROTATE,
    TWO: THREE.TOUCH.DOLLY_PAN,
  };

  // Smooth movement
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;

  // Pan parallel to screen plane (intuitive)
  controls.screenSpacePanning = true;

  // Zoom limits
  controls.minDistance = 1;
  controls.maxDistance = 100;

  // Auto-rotate (disabled by default, can be toggled)
  controls.autoRotate = false;
  controls.autoRotateSpeed = 0.5;

  // Target at origin
  controls.target.set(0, 0, 0);
  controls.update();

  return controls;
}
```

---

## 4. Renderer Factory (minimal placeholder)

Since full entity renderers come in Phase 5, Phase 4 uses a minimal factory
that renders everything as colored spheres and lines.

```js
// py/pytanga/viz/templates/renderers/factory.js

import * as THREE from 'three';

/**
 * Create a Three.js mesh for a given entity JSON object.
 * Phase 4: Minimal implementation — all entities are spheres or lines.
 * Phase 5: Replace with per-entity-kind optimized renderers.
 */
export function createEntityMesh(ent) {
  const color = ent.color ? new THREE.Color(ent.color) : new THREE.Color('#ffffff');
  const opacity = ent.opacity ?? 1.0;

  let geometry, material;

  switch (ent.kind) {
    case 'Point':
    case 'Direction':
    case 'HPoint': {
      const pos = ent.position || ent.vector || [0, 0, 0];
      const size = ent.size || 0.1;
      geometry = new THREE.SphereGeometry(size, 16, 16);
      material = makeMaterial(color, opacity, false);
      const mesh = new THREE.Mesh(geometry, material);
      mesh.position.set(pos[0], pos[1], pos[2]);
      mesh.userData = { entityId: ent.id, kind: ent.kind, data: ent };
      return mesh;
    }

    case 'PointPair': {
      const group = new THREE.Group();
      const colorA = ent.color || '#44ff44';
      const size = ent.pointSize || 0.06;
      for (const pt of [ent.pointA, ent.pointB]) {
        const geo = new THREE.SphereGeometry(size, 16, 16);
        const mat = makeMaterial(new THREE.Color(colorA), opacity, false);
        const m = new THREE.Mesh(geo, mat);
        m.position.set(pt[0], pt[1], pt[2]);
        group.add(m);
      }
      // Connect with a line
      const lineGeo = new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(...ent.pointA),
        new THREE.Vector3(...ent.pointB),
      ]);
      const lineMat = new THREE.LineBasicMaterial({ color: new THREE.Color(colorA), opacity, transparent: opacity < 1 });
      group.add(new THREE.Line(lineGeo, lineMat));
      group.userData = { entityId: ent.id, kind: ent.kind, data: ent };
      return group;
    }

    case 'Line': {
      const origin = ent.origin || [0, 0, 0];
      const dir = ent.direction || [1, 0, 0];
      const length = ent.length || 20;
      const thickness = ent.thickness || 0.03;
      // Thin cylinder along direction
      const mid = [
        origin[0] + dir[0] * length / 2,
        origin[1] + dir[1] * length / 2,
        origin[2] + dir[2] * length / 2,
      ];
      geometry = new THREE.CylinderGeometry(thickness, thickness, length, 8, 1);
      material = makeMaterial(color, opacity, false);
      const mesh = new THREE.Mesh(geometry, material);
      mesh.position.set(mid[0], mid[1], mid[2]);
      // Orient cylinder to direction vector
      const dirVec = new THREE.Vector3(dir[0], dir[1], dir[2]).normalize();
      const up = new THREE.Vector3(0, 1, 0);
      const quat = new THREE.Quaternion().setFromUnitVectors(up, dirVec);
      mesh.setRotationFromQuaternion(quat);
      mesh.userData = { entityId: ent.id, kind: ent.kind, data: ent };
      return mesh;
    }

    case 'Plane': {
      const point = ent.point || [0, 0, 0];
      const normal = ent.normal || [0, 0, 1];
      const extent = ent.extent || 10;
      geometry = new THREE.PlaneGeometry(extent * 2, extent * 2);
      material = makeMaterial(color, opacity, true);
      material.side = THREE.DoubleSide;
      const mesh = new THREE.Mesh(geometry, material);
      mesh.position.set(point[0], point[1], point[2]);
      // Orient plane to normal
      const normalVec = new THREE.Vector3(normal[0], normal[1], normal[2]).normalize();
      const quat2 = new THREE.Quaternion().setFromUnitVectors(
        new THREE.Vector3(0, 0, 1), normalVec
      );
      mesh.setRotationFromQuaternion(quat2);
      mesh.userData = { entityId: ent.id, kind: ent.kind, data: ent };
      return mesh;
    }

    case 'Circle': {
      const center = ent.center || [0, 0, 0];
      const radius = ent.radius || 1;
      const tubeRadius = ent.tubeRadius || 0.03;
      geometry = new THREE.TorusGeometry(radius, tubeRadius, 16, 64);
      material = makeMaterial(color, opacity, false);
      const mesh = new THREE.Mesh(geometry, material);
      mesh.position.set(center[0], center[1], center[2]);
      if (ent.normal) {
        const n = new THREE.Vector3(ent.normal[0], ent.normal[1], ent.normal[2]).normalize();
        const q = new THREE.Quaternion().setFromUnitVectors(
          new THREE.Vector3(0, 0, 1), n
        );
        mesh.setRotationFromQuaternion(q);
      }
      mesh.userData = { entityId: ent.id, kind: ent.kind, data: ent };
      return mesh;
    }

    case 'Sphere': {
      const center = ent.center || [0, 0, 0];
      const radius = ent.radius || 1;
      geometry = new THREE.SphereGeometry(radius, 32, 32);
      material = makeMaterial(color, opacity, false);
      const mesh = new THREE.Mesh(geometry, material);
      mesh.position.set(center[0], center[1], center[2]);

      if (ent.wireframe) {
        const wireGeo = new THREE.SphereGeometry(radius * 1.005, 24, 24);
        const wireMat = new THREE.MeshBasicMaterial({
          color, wireframe: true, opacity: opacity * 0.6, transparent: true
        });
        const wireframe = new THREE.Mesh(wireGeo, wireMat);
        mesh.add(wireframe);
      }

      mesh.userData = { entityId: ent.id, kind: ent.kind, data: ent };
      return mesh;
    }

    case 'Space': {
      const extent = ent.extent || 10;
      geometry = new THREE.BoxGeometry(extent * 2, extent * 2, extent * 2);
      const edges = new THREE.EdgesGeometry(geometry);
      const lineMat = new THREE.LineBasicMaterial({ color, opacity, transparent: true });
      const box = new THREE.LineSegments(edges, lineMat);
      box.userData = { entityId: ent.id, kind: ent.kind, data: ent };
      return box;
    }

    default:
      console.warn(`Unknown entity kind: ${ent.kind}`);
      return null;
  }
}

export function removeEntityMesh(mesh) {
  if (!mesh) return;
  if (mesh.parent) {
    mesh.parent.remove(mesh);
  }
  // Recursively dispose geometries and materials
  mesh.traverse((child) => {
    if (child.geometry) child.geometry.dispose();
    if (child.material) {
      if (Array.isArray(child.material)) {
        child.material.forEach(m => m.dispose());
      } else {
        child.material.dispose();
      }
    }
  });
}

function makeMaterial(color, opacity, doubleSided) {
  const mat = new THREE.MeshPhongMaterial({
    color,
    opacity,
    transparent: opacity < 1.0,
    depthWrite: opacity >= 0.99,  // Critical for translucent objects
    side: doubleSided ? THREE.DoubleSide : THREE.FrontSide,
  });
  return mat;
}
```

---

## 5. Design Decisions

1. **Minimal Phase 4 renderer:** The `factory.js` in Phase 4 contains all entity
   rendering logic inline. In Phase 5, this is refactored into per-entity modules
   under `renderers/`. The Phase 4 version produces correct visual output — it's
   just organized monolithically.

2. **`depthWrite: false` for translucent materials:** This is the single most
   important line for correct translucent rendering. Without it, opaque
   depth-writing translucent objects block objects behind them.

3. **Wireframe as child mesh:** Spheres render a slightly-larger wireframe sphere
   as a child of the main mesh. This way the wireframe moves with the parent
   automatically.

4. **Cylinder for lines:** Lines are rendered as thin cylinders (not `THREE.Line`
   which is always 1px wide and ignores perspective). This gives proper depth
   and perspective to lines.

5. **`userData` for entity metadata:** Each mesh stores `{ entityId, kind, data }`
   in `userData` for later use (click detection, entity info overlay, etc.).

6. **Reconnection:** On WebSocket disconnect, the client auto-reconnects after 2 seconds.
   On reconnect, it requests a full state sync.

---

## 6. Implementation Steps

1. Create `py/pytanga/viz/templates/viewer.html`.
2. Create `py/pytanga/viz/templates/viewer.js`.
3. Create `py/pytanga/viz/templates/controls.js`.
4. Create `py/pytanga/viz/templates/renderers/factory.js` (monolithic, Phase 4 version).
5. Manual E2E test: Run `Visualizer().run()` with the Phase 3 server, verify three.js
   scene loads in browser, grid + axes visible, orbit controls work.
6. Manual test: Add a few entities via Python, verify they appear in browser.
7. Manual test: Translucent plane renders correctly (objects behind are visible).
8. Manual test: Browser refresh → reconnects → full state restored.
9. Manual test: Resize browser window → scene adapts correctly.

## 7. Verification Checklist

### Basic Functionality
- [x] `viewer.html` loads Three.js from CDN import map without errors.
- [x] Canvas fills the browser window and resizes on window resize.
- [x] WebSocket connects and receives `scene_config` before `scene_update`.
- [x] Status indicator shows "Connected" / "Disconnected" correctly.
- [x] Page refresh / reconnect restores full scene state including config.

### Grid & Axes
- [x] Grid helper is visible and matches `space_extent`.
- [x] Axes helper is visible and matches `space_extent`.
- [x] Scene background color is set from `scene_config.background_color`.
- [x] Grid can be hidden via `show_grid: false`.
- [x] Axes can be hidden via `show_axes: false`.

### Orbit Controls
- [x] Left-drag rotates, middle-drag pans, scroll/wheel zooms.

### Camera Configuration
- [x] Explicit camera: `CameraConfig(position=..., target=..., fov=...)` positions exactly.
- [x] Partial explicit camera: Setting only `position` keeps auto-computed target and FOV.
- [x] Auto-fit: With `camera=None` (default), camera auto-positions from entity bounds.
- [x] Near/far clipping planes are reasonable for the scene scale.

### Rendering
- [x] All entity kinds render as correct Three.js primitives.
- [x] Translucent entities (`opacity < 1`) render without depth occlusion artifacts.
- [x] Wireframe on spheres renders correctly.
- [x] CSS2DRenderer labels display correctly for entities with `label` property.

### Geo-fix status
- [x] `factory.js` already uses `HPoint` case string (F1 done)
- [ ] ❌ Missing `isImaginary` rendering for PointPair/Circle/Sphere (F2-F4)
- [ ] ❌ Missing `ReflectionLine`, `ReflectionPlane`, `ReflectionOrigin`, `Reflector` cases (F5-F6)
- [x] `Inversion` case uses `ent.sphereRadius` (works with current serializer, will need update to `ent.radius` in F7)

### Error Handling
- [x] No console errors from missing imports or undefined references.
