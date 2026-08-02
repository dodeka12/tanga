# Phase 5: Per-Entity JS Renderer Modules

**Files:** `py/pytanga/viz/templates/renderers/point.js`, `line.js`, `plane.js`, `circle.js`, `sphere.js`, `direction.js`, `space.js`, `factory.js` (refactored)

**Goal:** Split the monolithic `factory.js` from Phase 4 into clean, single-responsibility
renderer modules — one per entity kind — with a thin factory dispatcher.

**Prerequisites:** Phase 4 (working monolithic factory.js)

---

## 1. Refactored Factory (`factory.js`)

The factory becomes a thin dispatcher that imports from per-entity modules:

```js
// py/pytanga/viz/templates/renderers/factory.js

import * as THREE from 'three';
import { CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
import { createPoint } from './point.js';
import { createLine } from './line.js';
import { createPlane } from './plane.js';
import { createCircle } from './circle.js';
import { createSphere } from './sphere.js';
import { createDirection } from './direction.js';
import { createSpace } from './space.js';

/**
 * Create a Three.js Object3D for a given entity JSON object.
 * Dispatches to the appropriate per-entity renderer.
 */
export function createEntityMesh(ent) {
  let mesh;

  switch (ent.kind) {
    case 'Point':
    case 'HPoint':
      mesh = createPoint(ent);
      break;
    case 'Direction':
      mesh = createDirection(ent);
      break;
    case 'Line':
      mesh = createLine(ent);
      break;
    case 'Plane':
      mesh = createPlane(ent);
      break;
    case 'Circle':
      mesh = createCircle(ent);
      break;
    case 'Sphere':
      mesh = createSphere(ent);
      break;
    case 'Space':
      mesh = createSpace(ent);
      break;
    default:
      console.warn(`Unknown entity kind: ${ent.kind}`);
      return null;
  }

  // Attach label if present
  if (mesh && ent.label) {
    import('./utils.js').then(({ createLabel }) => {
      const labelObj = createLabel(ent.label, ent);
      if (labelObj) mesh.add(labelObj);
    });
  }

  return mesh;
}

export function removeEntityMesh(mesh) {
  if (!mesh) return;
  if (mesh.parent) {
    mesh.parent.remove(mesh);
  }
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
```

---

## 2. Shared Utilities (`renderers/utils.js`)

Common functions extracted from the Phase 4 monolithic factory:

```js
// py/pytanga/viz/templates/renderers/utils.js

import * as THREE from 'three';

/**
 * Create a MeshPhongMaterial with sensible defaults for Tanga entities.
 *
 * Critical: depthWrite is disabled for translucent materials (opacity < 0.99)
 * to prevent depth-sorting artifacts.
 */
export function makeMaterial(color, opacity = 1.0, doubleSided = false) {
  return new THREE.MeshPhongMaterial({
    color: new THREE.Color(color),
    opacity,
    transparent: opacity < 1.0,
    depthWrite: opacity >= 0.99,
    side: doubleSided ? THREE.DoubleSide : THREE.FrontSide,
  });
}

/**
 * Create a quaternion that rotates the Y-axis to point along the given direction.
 * Used to orient cylinders (lines), cones (direction arrows), and planes.
 */
export function rotationFromDirection(dx, dy, dz) {
  const dir = new THREE.Vector3(dx, dy, dz).normalize();
  const up = new THREE.Vector3(0, 1, 0);
  return new THREE.Quaternion().setFromUnitVectors(up, dir);
}

/**
 * Create a quaternion that rotates the Z-axis to point along the given normal.
 * Used to orient toruses (circles) and planes.
 */
export function rotationFromNormal(nx, ny, nz) {
  const normal = new THREE.Vector3(nx, ny, nz).normalize();
  return new THREE.Quaternion().setFromUnitVectors(
    new THREE.Vector3(0, 0, 1), normal
  );
}

/**
 * Tag a mesh with entity metadata for click detection and debugging.
 */
export function tagEntity(mesh, ent) {
  mesh.userData = { entityId: ent.id, kind: ent.kind, data: ent };
}

/**
 * Parse a color string or use a fallback.
 */
export function parseColor(ent, fallback = '#ffffff') {
  return ent.color || fallback;
}

/**
 * Create a CSS2D label for an entity.
 *
 * The label is a DOM <div> positioned above the entity center using
 * CSS2DRenderer. It always faces the camera and renders as crisp HTML text.
 *
 * @param {string} text - The label text.
 * @param {object} ent - The entity JSON data (for optional label styling overrides).
 * @returns {THREE.CSS2DObject} or null if text is empty/falsy.
 */
export function createLabel(text, ent) {
  if (!text) return null;

  const div = document.createElement('div');
  div.textContent = text;
  div.style.fontFamily = 'monospace';
  div.style.fontSize = (ent.labelFontSize || 14) + 'px';
  div.style.color = ent.labelColor || '#ffffff';
  div.style.backgroundColor = ent.labelBackground || 'rgba(0, 0, 0, 0.6)';
  div.style.padding = '2px 6px';
  div.style.borderRadius = '3px';
  div.style.pointerEvents = 'none';
  div.style.userSelect = 'none';
  div.style.whiteSpace = 'nowrap';

  const label = new CSS2DObject(div);
  label.position.set(0, ent.labelOffsetY || 0.3, 0);
  label.name = 'entity-label';
  return label;
}
```

The CSS2DObject is imported in the factory/dispatcher (or each renderer module).

---

## 3. Per-Entity Renderers

### 3.1 `renderers/point.js`

```js
import * as THREE from 'three';
import { makeMaterial, tagEntity, parseColor } from './utils.js';

export function createPoint(ent) {
  const color = parseColor(ent, '#ff4444');
  const opacity = ent.opacity ?? 1.0;
  const size = ent.size || 0.08;
  const pos = ent.position || [0, 0, 0];

  const geometry = new THREE.SphereGeometry(size, 16, 16);
  const material = makeMaterial(color, opacity);
  const mesh = new THREE.Mesh(geometry, material);
  mesh.position.set(pos[0], pos[1], pos[2]);
  tagEntity(mesh, ent);
  return mesh;
}
```

### 3.2 `renderers/direction.js`

```js
import * as THREE from 'three';
import { makeMaterial, rotationFromDirection, tagEntity, parseColor } from './utils.js';

export function createDirection(ent) {
  const color = parseColor(ent, '#ffffff');
  const opacity = ent.opacity ?? 0.9;
  const vec = ent.vector || [0, 0, 1];
  const length = ent.length || 2.0;
  const origin = ent.origin || [0, 0, 0];

  const group = new THREE.Group();

  // Arrow shaft (cylinder)
  const shaftLength = length * 0.75;
  const shaftRadius = 0.04;
  const shaftGeo = new THREE.CylinderGeometry(shaftRadius, shaftRadius, shaftLength, 8, 1);
  const shaftMat = makeMaterial(color, opacity);
  const shaft = new THREE.Mesh(shaftGeo, shaftMat);
  shaft.position.y = shaftLength / 2;
  group.add(shaft);

  // Arrow head (cone)
  const headLength = length * 0.25;
  const headRadius = 0.10;
  const headGeo = new THREE.ConeGeometry(headRadius, headLength, 8, 1);
  const headMat = makeMaterial(color, opacity);
  const head = new THREE.Mesh(headGeo, headMat);
  head.position.y = shaftLength + headLength / 2;
  group.add(head);

  // Orient the arrow
  group.setRotationFromQuaternion(rotationFromDirection(vec[0], vec[1], vec[2]));

  // Position at origin
  group.position.set(origin[0], origin[1], origin[2]);

  tagEntity(group, ent);
  return group;
}
```

### 3.3 `renderers/line.js`

```js
import * as THREE from 'three';
import { makeMaterial, rotationFromDirection, tagEntity, parseColor } from './utils.js';

export function createLine(ent) {
  const color = parseColor(ent, '#44ff44');
  const opacity = ent.opacity ?? 0.8;
  const thickness = ent.thickness || 0.03;
  const length = ent.length || 20.0;
  const origin = ent.origin || [0, 0, 0];
  const dir = ent.direction || [1, 0, 0];

  const geometry = new THREE.CylinderGeometry(thickness, thickness, length, 8, 1);
  const material = makeMaterial(color, opacity);
  const mesh = new THREE.Mesh(geometry, material);

  // Center the cylinder along the line direction
  // (Cylinder is Y-up by default; rotate to the line direction)
  mesh.setRotationFromQuaternion(rotationFromDirection(dir[0], dir[1], dir[2]));

  // Position at midpoint so the cylinder extends symmetrically
  const lengthScale = length / Math.sqrt(dir[0] ** 2 + dir[1] ** 2 + dir[2] ** 2 || 1);
  const dNorm = [dir[0] * lengthScale, dir[1] * lengthScale, dir[2] * lengthScale];
  // Normalize dir for midpoint calculation
  const dLen = Math.sqrt(dNorm[0] ** 2 + dNorm[1] ** 2 + dNorm[2] ** 2) || 1;
  const mid = [
    origin[0] + dNorm[0] / dLen * length / 2,
    origin[1] + dNorm[1] / dLen * length / 2,
    origin[2] + dNorm[2] / dLen * length / 2,
  ];
  mesh.position.set(mid[0], mid[1], mid[2]);

  tagEntity(mesh, ent);
  return mesh;
}
```

### 3.4 `renderers/plane.js`

```js
import * as THREE from 'three';
import { makeMaterial, rotationFromNormal, tagEntity, parseColor } from './utils.js';

export function createPlane(ent) {
  const color = parseColor(ent, '#4488ff');
  const opacity = ent.opacity ?? 0.3;
  const extent = ent.extent || 10.0;
  const point = ent.point || [0, 0, 0];
  const normal = ent.normal || [0, 0, 1];

  const geometry = new THREE.PlaneGeometry(extent * 2, extent * 2);
  const material = makeMaterial(color, opacity, true);  // double-sided for planes
  const mesh = new THREE.Mesh(geometry, material);

  mesh.position.set(point[0], point[1], point[2]);
  mesh.setRotationFromQuaternion(rotationFromNormal(normal[0], normal[1], normal[2]));

  tagEntity(mesh, ent);
  return mesh;
}
```

### 3.5 `renderers/circle.js`

```js
import * as THREE from 'three';
import { makeMaterial, rotationFromNormal, tagEntity, parseColor } from './utils.js';

export function createCircle(ent) {
  const color = parseColor(ent, '#ff44ff');
  const opacity = ent.opacity ?? 0.7;
  const center = ent.center || [0, 0, 0];
  const radius = Math.max(ent.radius || 1.0, 0.001);
  const tubeRadius = ent.tubeRadius || 0.03;

  const geometry = new THREE.TorusGeometry(radius, tubeRadius, 16, 64);
  const material = makeMaterial(color, opacity);
  const mesh = new THREE.Mesh(geometry, material);

  mesh.position.set(center[0], center[1], center[2]);

  if (ent.normal) {
    mesh.setRotationFromQuaternion(
      rotationFromNormal(ent.normal[0], ent.normal[1], ent.normal[2])
    );
  }

  tagEntity(mesh, ent);
  return mesh;
}
```

### 3.6 `renderers/sphere.js`

```js
import * as THREE from 'three';
import { makeMaterial, tagEntity, parseColor } from './utils.js';

export function createSphere(ent) {
  const color = parseColor(ent, '#ffaa00');
  const opacity = ent.opacity ?? 0.4;
  const center = ent.center || [0, 0, 0];
  const radius = Math.max(ent.radius || 1.0, 0.001);

  const geometry = new THREE.SphereGeometry(radius, 32, 32);
  const material = makeMaterial(color, opacity);
  const mesh = new THREE.Mesh(geometry, material);
  mesh.position.set(center[0], center[1], center[2]);

  // Wireframe overlay
  if (ent.wireframe !== false) {  // default: true
    const wireGeo = new THREE.SphereGeometry(radius * 1.005, 24, 24);
    const wireMat = new THREE.MeshBasicMaterial({
      color: new THREE.Color(color),
      wireframe: true,
      opacity: Math.min(opacity * 0.6, 1.0),
      transparent: true,
    });
    mesh.add(new THREE.Mesh(wireGeo, wireMat));
  }

  tagEntity(mesh, ent);
  return mesh;
}
```

### 3.7 `renderers/space.js`

```js
import * as THREE from 'three';
import { tagEntity, parseColor } from './utils.js';

export function createSpace(ent) {
  const color = parseColor(ent, '#888888');
  const opacity = ent.opacity ?? 0.15;
  const extent = ent.extent || 10.0;

  const geometry = new THREE.BoxGeometry(extent * 2, extent * 2, extent * 2);
  const edges = new THREE.EdgesGeometry(geometry);
  const material = new THREE.LineBasicMaterial({
    color: new THREE.Color(color),
    opacity,
    transparent: true,
  });
  const box = new THREE.LineSegments(edges, material);

  tagEntity(box, ent);
  return box;
}
```

---

### 4.1 `utils.js` (new)

- [x] **S1:** Create `py/pytanga/viz/templates/renderers/utils.js`
- [x] **S2:** Export `makeMaterial()` — MeshPhongMaterial with opacity/depthWrite handling
- [x] **S3:** Export `rotationFromDirection()` — quaternion from Y-axis to target direction
- [x] **S4:** Export `rotationFromNormal()` — quaternion from Z-axis to target normal
- [x] **S5:** Export `tagEntity()` — `userData` with entity ID, kind, and data
- [x] **S6:** Export `parseColor()` — color string with fallback
- [x] **S7:** Export `styleParam()` — reads from `ent.style.*` (Phase 4c) with fallback to flat `ent.*`
- [x] **S7b:** Export `createArrow()` — 3D arrow helper (cylinder + cone)
- [x] **S7c:** Export `createDilatorRings()` — concentric torus rings

### 4.2 Per-Entity Renderer Modules

- [x] **S8:** Create `renderers/point.js` — `createPoint()` with SphereGeometry
- [x] **S9:** Create `renderers/direction.js` — `createDirection()` with Cylinder + Cone arrow
- [x] **S10:** Create `renderers/line.js` — `createLine()` with CylinderGeometry oriented to direction
- [x] **S11:** Create `renderers/plane.js` — `createPlane()` with double-sided PlaneGeometry + normal orientation
- [x] **S12:** Create `renderers/circle.js` — `createCircle()` with TorusGeometry + normal orientation
- [x] **S13:** Create `renderers/sphere.js` — `createSphere()` with SphereGeometry + wireframe overlay
- [x] **S14:** Create `renderers/space.js` — `createSpace()` with BoxGeometry edges (LineSegments)
- [x] **S15:** Each module exports exactly one `create*` function
- [x] **S16:** Each module imports shared utilities from `./utils.js`

### 4.3 `factory.js` Refactor

- [x] **S17:** Replace monolithic `factory.js` with thin dispatcher using ES module imports
- [x] **S18:** `createEntityMesh()` dispatches on `ent.kind` to per-entity `create*()` for Point, HPoint, Direction, Line, Plane, Circle, Sphere, Space
- [x] **S19:** `removeEntityMesh()` properly disposes geometries and materials recursively
- [x] **S20:** Operator renderers remain inline in factory.js (to be refactored in Phase 6)
- [x] **S20b:** `tagEntity()` called after mesh creation (in factory, not in renderers)

### 4.4 Manual Verification

- [ ] **S21:** Manual test: Each entity kind renders identically to Phase 4
- [ ] **S22:** Manual test: Browser console has no import errors or missing module warnings

- [ ] **S21:** Manual test: Each entity kind (Point, Direction, Line, Plane, Circle, Sphere, Space) renders identically to Phase 4
- [ ] **S22:** Manual test: Browser console has no import errors or missing module warnings

## 5. Verification Checklist

- [ ] `factory.js` imports all per-entity modules without errors.
- [ ] `createEntityMesh()` dispatches all entity kinds correctly.
- [ ] `utils.js` exports `makeMaterial`, `rotationFromDirection`, `rotationFromNormal`, `tagEntity`, `parseColor`.
- [ ] Each renderer module exports exactly one `create*` function.
- [ ] All Three.js primitives render correctly (spheres, cylinders, planes, tori, boxes, cones, lines).
- [ ] Direction arrows have shaft + cone head.
- [ ] Sphere wireframe renders as slightly larger wireframe overlay.
- [ ] Space renders as box edges (not solid).
- [ ] Translucency works correctly for all entity kinds.
- [ ] `removeEntityMesh()` properly disposes all geometries and materials.