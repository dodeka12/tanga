# Phase 6: Operator Visualization

**Files:** `py/pytanga/viz/templates/renderers/operators/` — 8 JS renderer modules + factory dispatcher

**Goal:** Add dedicated Three.js renderers for all geometric operator (versor) types
from `pytanga.geometry.operators`. When a user calls `viz.add(rotor)` or passes an MV
that analyzes to a `Rotor`, the browser renders a meaningful geometric representation.

**Prerequisites:** Phase 5 (entity renderer infrastructure), Phase 2 (operator serializer)

---

## 1. Operator → Visual Mapping

Each operator type is rendered as a distinctive geometric construct:

| Operator | Three.js Geometry | What It Conveys |
|----------|-------------------|-----------------|
| **Reflection** | Mirror plane (translucent quad) + normal arrow | The plane of reflection and its normal direction |
| **Inversion** | Wireframe sphere centered at the origin point | The sphere about which inversion happens |
| **Rotor** | Partial disc arc (filled sector) + axis line | Rotation plane, rotation angle (arc length), rotation axis |
| **Translator** | 3D arrow (shaft + cone head) | Translation direction and magnitude |
| **Motor** | Helix/screw curve + axis line | Combined rotation (helix) and translation (axis) |
| **Dilator** | Concentric expanding ring pattern (3–5 nested tori) | Uniform scaling about the origin |
| **GeneralRotor** | Two perpendicular bivector discs + combined axis | Rotor + translator bivector planes (only in N3) |
| **GeneralDilator** | Expanding rings + translation arrow | Scaling with optional translation component (only in N3) |

---

## 2. JSON Serialization (Phase 2 Extension)

The Phase 2 serializer already dispatches on entity types. For operators, the dispatch
extends to `isinstance(entity, Rotor)` etc. The JSON format mirrors the operator dataclass fields:

```json
// Rotor
{
  "id": "rot_01",
  "kind": "Rotor",
  "color": "#ff8844",
  "opacity": 0.7,
  "angle": 1.5708,
  "axis": [0.0, 0.0, 1.0],
  "origin": [0.0, 0.0, 0.0],
  "discRadius": 1.5
}

// Translator
{
  "id": "transl_01",
  "kind": "Translator",
  "color": "#44aaff",
  "opacity": 0.9,
  "vector": [2.0, 0.0, 0.0],
  "length": 3.0,
  "origin": [1.0, 0.0, 0.0]
}

// Motor
{
  "id": "motor_01",
  "kind": "Motor",
  "color": "#ff66cc",
  "opacity": 0.7,
  "rotor": {
    "angle": 1.5708,
    "axis": [0.0, 0.0, 1.0]
  },
  "translator": {
    "vector": [2.0, 0.0, 0.0]
  },
  "origin": [0.0, 0.0, 0.0]
}

// Reflection
{
  "id": "refl_01",
  "kind": "Reflection",
  "color": "#88ccff",
  "opacity": 0.35,
  "normal": [0.0, 0.0, 1.0],
  "origin": [0.0, 0.0, 0.0],
  "planeExtent": 5.0
}

// Inversion
{
  "id": "inv_01",
  "kind": "Inversion",
  "color": "#cc88ff",
  "opacity": 0.4,
  "origin": [0.0, 0.0, 0.0],
  "sphereRadius": 2.0
}

// Dilator
{
  "id": "dil_01",
  "kind": "Dilator",
  "color": "#ffcc44",
  "opacity": 0.6,
  "factor": 2.0,
  "origin": [0.0, 0.0, 0.0],
  "ringCount": 4,
  "maxRadius": 3.0
}

// GeneralRotor
{
  "id": "genrot_01",
  "kind": "GeneralRotor",
  "color": "#ff9966",
  "opacity": 0.6,
  "rotor": {
    "angle": 1.5708,
    "axis": [0.0, 0.0, 1.0]
  },
  "translator": {
    "vector": [1.0, 0.0, 0.0]
  },
  "origin": [0.0, 0.0, 0.0]
}

// GeneralDilator
{
  "id": "gendil_01",
  "kind": "GeneralDilator",
  "color": "#ffcc88",
  "opacity": 0.6,
  "factor": 2.0,
  "translator": {
    "vector": [1.0, 0.0, 0.0]
  },
  "origin": [0.0, 0.0, 0.0],
  "ringCount": 4,
  "maxRadius": 3.0
}
```

---

## 3. JS Renderer Modules

### 3.1 `operators/factory.js` — Operator Dispatcher

```js
// py/pytanga/viz/templates/renderers/operators/factory.js

import { createRotor } from './rotor.js';
import { createTranslator } from './translator.js';
import { createMotor } from './motor.js';
import { createReflection } from './reflection.js';
import { createInversion } from './inversion.js';
import { createDilator } from './dilator.js';
import { createGeneralRotor } from './general_rotor.js';
import { createGeneralDilator } from './general_dilator.js';

/**
 * Create a Three.js Object3D for a given operator JSON object.
 * Returns null for unknown operator kinds.
 */
export function createOperatorMesh(ent) {
  switch (ent.kind) {
    case 'Reflection': return createReflection(ent);
    case 'Inversion':  return createInversion(ent);
    case 'Rotor':      return createRotor(ent);
    case 'Translator': return createTranslator(ent);
    case 'Dilator':    return createDilator(ent);
    case 'Motor':      return createMotor(ent);
    case 'GeneralRotor':    return createGeneralRotor(ent);
    case 'GeneralDilator':  return createGeneralDilator(ent);
    default: return null;
  }
}
```

### 3.2 `operators/rotor.js` — Rotor (Disc Arc + Axis)

A **partially filled disc** showing the rotation plane, with the arc extent
representing the rotation angle, and a line along the rotation axis.

```js
import * as THREE from 'three';
import { makeMaterial, rotationFromNormal, tagEntity, parseColor } from '../utils.js';

export function createRotor(ent) {
  const color = parseColor(ent, '#ff8844');
  const opacity = ent.opacity ?? 0.7;
  const angle = ent.angle ?? 0.0;
  const axis = ent.axis || [0, 0, 1];
  const origin = ent.origin || [0, 0, 0];
  const discRadius = ent.discRadius || 1.5;

  const group = new THREE.Group();

  // ── Rotation disc (partially filled circle) ──
  const absAngle = Math.abs(angle);
  const segments = Math.max(8, Math.ceil(absAngle / (Math.PI / 32)));
  const ringGeo = new THREE.RingGeometry(discRadius * 0.15, discRadius, segments, 1, 0, absAngle);
  const ringMat = new THREE.MeshBasicMaterial({
    color: new THREE.Color(color),
    opacity: opacity * 0.8,
    transparent: true,
    side: THREE.DoubleSide,
    depthWrite: false,
  });
  const disc = new THREE.Mesh(ringGeo, ringMat);

  // ── Outer ring (thin torus for the full circle) ──
  const torusGeo = new THREE.TorusGeometry(discRadius, 0.03, 16, 64);
  const torusMat = makeMaterial(color, opacity * 0.5);
  const torus = new THREE.Mesh(torusGeo, torusMat);
  group.add(torus);

  // ── Arc outline for the angle portion ──
  const arcPoints = [];
  const arcRes = segments + 1;
  for (let i = 0; i <= arcRes; i++) {
    const a = (absAngle / arcRes) * i;
    arcPoints.push(new THREE.Vector3(Math.cos(a) * discRadius, Math.sin(a) * discRadius, 0));
  }
  const arcGeo = new THREE.BufferGeometry().setFromPoints(arcPoints);
  const arcLine = new THREE.Line(arcGeo, new THREE.LineBasicMaterial({
    color: new THREE.Color(color), linewidth: 1,
  }));
  disc.add(arcLine);

  // ── Radial line at the start of the arc ──
  const radialGeo = new THREE.BufferGeometry().setFromPoints([
    new THREE.Vector3(0, 0, 0),
    new THREE.Vector3(discRadius, 0, 0),
  ]);
  disc.add(new THREE.Line(radialGeo, new THREE.LineBasicMaterial({
    color: new THREE.Color(color),
  })));

  group.add(disc);

  // ── Rotation axis (line through origin) ──
  const axisLen = discRadius * 1.6;
  const axisGeo = new THREE.BufferGeometry().setFromPoints([
    new THREE.Vector3(0, 0, -axisLen),
    new THREE.Vector3(0, 0, axisLen),
  ]);
  const axisLine = new THREE.Line(axisGeo, new THREE.LineBasicMaterial({
    color: new THREE.Color(color), opacity: 0.4, transparent: true,
  }));
  group.add(axisLine);

  // Orient the entire rotor to the actual rotation axis
  group.setRotationFromQuaternion(rotationFromNormal(axis[0], axis[1], axis[2]));
  group.position.set(origin[0], origin[1], origin[2]);

  tagEntity(group, ent);
  return group;
}
```

### 3.3 `operators/translator.js` — Translator (3D Arrow)

A standard 3D arrow (cylinder shaft + cone head) showing translation direction
and magnitude.

```js
import * as THREE from 'three';
import { makeMaterial, rotationFromDirection, tagEntity, parseColor } from '../utils.js';

export function createTranslator(ent) {
  const color = parseColor(ent, '#44aaff');
  const opacity = ent.opacity ?? 0.9;
  const vec = ent.vector || [1, 0, 0];
  const length = ent.length || 3.0;
  const origin = ent.origin || [0, 0, 0];

  const group = new THREE.Group();

  // Arrow shaft
  const shaftLength = length * 0.75;
  const shaftRadius = 0.06;
  const shaftGeo = new THREE.CylinderGeometry(shaftRadius, shaftRadius, shaftLength, 8, 1);
  const shaft = new THREE.Mesh(shaftGeo, makeMaterial(color, opacity));
  shaft.position.y = shaftLength / 2;
  group.add(shaft);

  // Arrow head
  const headLength = length * 0.25;
  const headRadius = 0.15;
  const headGeo = new THREE.ConeGeometry(headRadius, headLength, 8, 1);
  const head = new THREE.Mesh(headGeo, makeMaterial(color, opacity));
  head.position.y = shaftLength + headLength / 2;
  group.add(head);

  // Orientation
  group.setRotationFromQuaternion(rotationFromDirection(vec[0], vec[1], vec[2]));
  group.position.set(origin[0], origin[1], origin[2]);

  tagEntity(group, ent);
  return group;
}
```

### 3.4 `operators/motor.js` — Motor (Helix/Screw)

A **helix curve** winding around the rotation axis, showing the combined rotation +
translation. The helix pitch represents the translation component; the radius
represents the rotation component.

```js
import * as THREE from 'three';
import { rotationFromNormal, tagEntity, parseColor } from '../utils.js';

export function createMotor(ent) {
  const color = parseColor(ent, '#ff66cc');
  const opacity = ent.opacity ?? 0.7;
  const rotor = ent.rotor || {};
  const translator = ent.translator || {};
  const origin = ent.origin || [0, 0, 0];
  const axis = rotor.axis || [0, 0, 1];
  const angle = rotor.angle ?? 1.5;
  const transVec = translator.vector || [0, 0, 0];
  const transMag = Math.sqrt(transVec[0] ** 2 + transVec[1] ** 2 + transVec[2] ** 2);

  const group = new THREE.Group();

  // Helix curve
  const helixRadius = 1.0;
  const turns = Math.max(1, Math.ceil(Math.abs(angle) / (2 * Math.PI)));
  const pointsPerTurn = 64;
  const totalPoints = turns * pointsPerTurn;
  const totalAngle = angle;
  const totalHeight = transMag * 2;  // scale translation for visibility
  const helixPoints = [];

  for (let i = 0; i <= totalPoints; i++) {
    const t = i / totalPoints;
    const a = t * totalAngle;
    helixPoints.push(new THREE.Vector3(
      Math.cos(a) * helixRadius,
      t * totalHeight - totalHeight / 2,
      Math.sin(a) * helixRadius,
    ));
  }

  const helixGeo = new THREE.BufferGeometry().setFromPoints(helixPoints);
  const helixLine = new THREE.Line(helixGeo, new THREE.LineBasicMaterial({
    color: new THREE.Color(color), opacity, transparent: true,
  }));
  group.add(helixLine);

  // Axis line through center
  const axisLen = totalHeight / 2 + 1;
  const axisGeo = new THREE.BufferGeometry().setFromPoints([
    new THREE.Vector3(0, -axisLen, 0),
    new THREE.Vector3(0, axisLen, 0),
  ]);
  group.add(new THREE.Line(axisGeo, new THREE.LineBasicMaterial({
    color: new THREE.Color(color), opacity: 0.3, transparent: true,
  })));

  // Orient to the motor's rotation axis
  group.setRotationFromQuaternion(rotationFromNormal(axis[0], axis[1], axis[2]));
  group.position.set(origin[0], origin[1], origin[2]);

  tagEntity(group, ent);
  return group;
}
```

### 3.5 `operators/reflection.js` — Reflection (Mirror Plane)

A translucent quad (mirror plane) through the origin, plus a short normal arrow.

```js
import * as THREE from 'three';
import { makeMaterial, rotationFromNormal, tagEntity, parseColor } from '../utils.js';

export function createReflection(ent) {
  const color = parseColor(ent, '#88ccff');
  const opacity = ent.opacity ?? 0.35;
  const normal = ent.normal || [0, 0, 1];
  const origin = ent.origin || [0, 0, 0];
  const extent = ent.planeExtent || 5.0;

  const group = new THREE.Group();

  // Mirror plane (translucent quad)
  const planeGeo = new THREE.PlaneGeometry(extent * 2, extent * 2);
  const planeMat = new THREE.MeshPhongMaterial({
    color: new THREE.Color(color),
    opacity,
    transparent: true,
    depthWrite: false,
    side: THREE.DoubleSide,
    emissive: new THREE.Color(color),
    emissiveIntensity: 0.15,
  });
  const plane = new THREE.Mesh(planeGeo, planeMat);
  group.add(plane);

  // Normal arrow (short)
  const arrowLen = extent * 0.3;
  const shaftGeo = new THREE.CylinderGeometry(0.04, 0.04, arrowLen * 0.75, 8, 1);
  const shaft = new THREE.Mesh(shaftGeo, makeMaterial(color, 0.8));
  shaft.position.y = (arrowLen * 0.75) / 2;
  group.add(shaft);

  const headGeo = new THREE.ConeGeometry(0.1, arrowLen * 0.25, 8, 1);
  const head = new THREE.Mesh(headGeo, makeMaterial(color, 0.8));
  head.position.y = arrowLen * 0.75 + (arrowLen * 0.25) / 2;
  group.add(head);

  // Orient plane to normal
  group.setRotationFromQuaternion(rotationFromNormal(normal[0], normal[1], normal[2]));
  group.position.set(origin[0], origin[1], origin[2]);

  tagEntity(group, ent);
  return group;
}
```

### 3.6 `operators/inversion.js` — Inversion (Wireframe Sphere)

A wireframe sphere centered at the origin point, showing the sphere about which
inversion happens.

```js
import * as THREE from 'three';
import { tagEntity, parseColor } from '../utils.js';

export function createInversion(ent) {
  const color = parseColor(ent, '#cc88ff');
  const opacity = ent.opacity ?? 0.4;
  const origin = ent.origin || [0, 0, 0];
  const radius = ent.sphereRadius || 2.0;

  const geo = new THREE.SphereGeometry(radius, 32, 32);
  const mat = new THREE.MeshBasicMaterial({
    color: new THREE.Color(color),
    wireframe: true,
    opacity,
    transparent: true,
  });
  const sphere = new THREE.Mesh(geo, mat);

  // Cross-hair at center
  const crossLen = radius * 0.4;
  const crossGroup = new THREE.Group();
  for (const dir of [[1,0,0], [0,1,0], [0,0,1]]) {
    const pts = [
      new THREE.Vector3(-dir[0] * crossLen, -dir[1] * crossLen, -dir[2] * crossLen),
      new THREE.Vector3(dir[0] * crossLen, dir[1] * crossLen, dir[2] * crossLen),
    ];
    crossGroup.add(new THREE.Line(
      new THREE.BufferGeometry().setFromPoints(pts),
      new THREE.LineBasicMaterial({ color: new THREE.Color(color), opacity, transparent: true }),
    ));
  }
  sphere.add(crossGroup);

  sphere.position.set(origin[0], origin[1], origin[2]);
  tagEntity(sphere, ent);
  return sphere;
}
```

### 3.7 `operators/dilator.js` — Dilator (Concentric Rings)

Nested concentric tori (rings) expanding outward, conveying uniform scaling
about the origin. More rings = larger scaling factor range.

```js
import * as THREE from 'three';
import { makeMaterial, tagEntity, parseColor } from '../utils.js';

export function createDilator(ent) {
  const color = parseColor(ent, '#ffcc44');
  const opacity = ent.opacity ?? 0.6;
  const origin = ent.origin || [0, 0, 0];
  const ringCount = ent.ringCount || 4;
  const maxRadius = ent.maxRadius || 3.0;

  const group = new THREE.Group();

  const minRadius = 0.3;
  for (let i = 0; i < ringCount; i++) {
    const t = ringCount > 1 ? i / (ringCount - 1) : 0.5;
    const r = minRadius + t * (maxRadius - minRadius);
    const torusGeo = new THREE.TorusGeometry(r, 0.02, 8, 64);
    const torusMat = makeMaterial(color, opacity * (0.4 + 0.6 * t));
    const torus = new THREE.Mesh(torusGeo, torusMat);
    group.add(torus);

    // Alternate rings in XY and XZ planes for 3D effect
    if (i % 2 === 0) {
      torus.rotation.x = 0;           // XY plane
    } else {
      torus.rotation.x = Math.PI / 2; // XZ plane
    }
  }

  group.position.set(origin[0], origin[1], origin[2]);
  tagEntity(group, ent);
  return group;
}
```

### 3.8 `operators/general_rotor.js` — GeneralRotor (Combined Bivector Planes)

Two semi-transparent discs representing the rotor bivector plane and the
translator bivector plane, with the common axis.

```js
import * as THREE from 'three';
import { makeMaterial, rotationFromNormal, tagEntity, parseColor } from '../utils.js';

export function createGeneralRotor(ent) {
  const color = parseColor(ent, '#ff9966');
  const opacity = ent.opacity ?? 0.6;
  const rotor = ent.rotor || {};
  const translator = ent.translator || {};
  const origin = ent.origin || [0, 0, 0];
  const axis = rotor.axis || [0, 0, 1];
  const transVec = translator.vector || [1, 0, 0];

  const group = new THREE.Group();

  // Rotor disc (XY-plane by default, then oriented)
  const discGeo = new THREE.CircleGeometry(1.5, 32);
  const discMat = new THREE.MeshBasicMaterial({
    color: new THREE.Color(color),
    opacity: opacity * 0.5,
    transparent: true,
    side: THREE.DoubleSide,
    depthWrite: false,
  });
  const disc = new THREE.Mesh(discGeo, discMat);
  group.add(disc);

  // Translator bivector disc — in a plane containing the translation direction
  const bivecGroup = new THREE.Group();
  const bivecDisc = new THREE.Mesh(
    new THREE.CircleGeometry(1.0, 32),
    new THREE.MeshBasicMaterial({
      color: new THREE.Color(color),
      opacity: opacity * 0.35,
      transparent: true,
      side: THREE.DoubleSide,
      depthWrite: false,
    }),
  );
  // Orient bivector disc so its normal is the translation vector
  const transDir = new THREE.Vector3(transVec[0], transVec[1], transVec[2]).normalize();
  bivecDisc.setRotationFromQuaternion(
    new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 0, 1), transDir),
  );
  bivecGroup.add(bivecDisc);
  group.add(bivecGroup);

  // Axis line
  const axisLen = 2.0;
  const axisGeo = new THREE.BufferGeometry().setFromPoints([
    new THREE.Vector3(0, 0, -axisLen),
    new THREE.Vector3(0, 0, axisLen),
  ]);
  group.add(new THREE.Line(axisGeo, new THREE.LineBasicMaterial({
    color: new THREE.Color(color), opacity: 0.4, transparent: true,
  })));

  // Orient entire group to the rotor axis
  group.setRotationFromQuaternion(rotationFromNormal(axis[0], axis[1], axis[2]));
  group.position.set(origin[0], origin[1], origin[2]);

  tagEntity(group, ent);
  return group;
}
```

### 3.9 `operators/general_dilator.js` — GeneralDilator (Directed Rings)

Expanding rings (like dilator) plus a translation arrow through the center,
showing the combined scaling + translation.

```js
import * as THREE from 'three';
import { makeMaterial, rotationFromDirection, tagEntity, parseColor } from '../utils.js';

export function createGeneralDilator(ent) {
  const color = parseColor(ent, '#ffcc88');
  const opacity = ent.opacity ?? 0.6;
  const origin = ent.origin || [0, 0, 0];
  const ringCount = ent.ringCount || 4;
  const maxRadius = ent.maxRadius || 3.0;
  const translator = ent.translator || {};
  const transVec = translator.vector || [1, 0, 0];
  const transLen = Math.sqrt(transVec[0] ** 2 + transVec[1] ** 2 + transVec[2] ** 2) * 1.5;

  const group = new THREE.Group();

  // Concentric rings (same as Dilator, but stacked along translation direction)
  const minRadius = 0.3;
  for (let i = 0; i < ringCount; i++) {
    const t = ringCount > 1 ? i / (ringCount - 1) : 0.5;
    const r = minRadius + t * (maxRadius - minRadius);
    const torusGeo = new THREE.TorusGeometry(r, 0.02, 8, 64);
    const torusMat = makeMaterial(color, opacity * (0.4 + 0.6 * t));
    const torus = new THREE.Mesh(torusGeo, torusMat);
    // Distribute rings along the translation direction
    const offset = (t - 0.5) * transLen;
    const dir = new THREE.Vector3(transVec[0], transVec[1], transVec[2]).normalize();
    torus.position.set(dir.x * offset, dir.y * offset, dir.z * offset);
    if (i % 2 === 0) {
      torus.rotation.x = 0;
    } else {
      torus.rotation.x = Math.PI / 2;
    }
    group.add(torus);
  }

  // Translation arrow through the center
  const shaftGeo = new THREE.CylinderGeometry(0.04, 0.04, transLen * 0.75, 8, 1);
  const shaft = new THREE.Mesh(shaftGeo, makeMaterial(color, 0.7));
  shaft.position.y = (transLen * 0.75) / 2;
  group.add(shaft);

  const headGeo = new THREE.ConeGeometry(0.12, transLen * 0.25, 8, 1);
  const head = new THREE.Mesh(headGeo, makeMaterial(color, 0.7));
  head.position.y = transLen * 0.75 + (transLen * 0.25) / 2;
  group.add(head);

  // Orient arrow along translation direction
  group.setRotationFromQuaternion(rotationFromDirection(transVec[0], transVec[1], transVec[2]));
  group.position.set(origin[0], origin[1], origin[2]);

  tagEntity(group, ent);
  return group;
}
```

---

## 4. Integration with Entity Factory

The `factory.js` dispatcher in Phase 5 is extended to try operator renderers
when the entity kind doesn't match any geometric entity:

```js
// In factory.js — updated createEntityMesh():

import { createOperatorMesh } from './operators/factory.js';

export function createEntityMesh(ent) {
  // Try entity renderers first
  let mesh;

  switch (ent.kind) {
    case 'Point':
    case 'HPoint':
      mesh = createPoint(ent); break;
    case 'Direction':   mesh = createDirection(ent); break;
    case 'Line':        mesh = createLine(ent); break;
    case 'Plane':       mesh = createPlane(ent); break;
    case 'Circle':      mesh = createCircle(ent); break;
    case 'Sphere':      mesh = createSphere(ent); break;
    case 'Space':       mesh = createSpace(ent); break;

    // ── Operator kinds ──
    case 'Reflection':
    case 'Inversion':
    case 'Rotor':
    case 'Translator':
    case 'Dilator':
    case 'Motor':
    case 'GeneralRotor':
    case 'GeneralDilator':
      mesh = createOperatorMesh(ent);
      break;

    default:
      console.warn(`Unknown entity kind: ${ent.kind}`);
      return null;
  }

  // Attach label if present (same as before)
  if (mesh && ent.label) {
    import('./utils.js').then(({ createLabel }) => {
      const labelObj = createLabel(ent.label, ent);
      if (labelObj) mesh.add(labelObj);
    });
  }

  return mesh;
}
```

---

## 5. Serializer Extension (Phase 2)

The serializer's dispatch in Phase 2 adds `isinstance` checks for each operator type,
flattening the operator dataclass fields into JSON:

```python
# In serializer.py — serialize_entity() dispatch additions:

from pytanga.geometry.operators import (
    Reflection, Inversion, Rotor, Translator, Dilator,
    Motor, GeneralRotor, GeneralDilator,
)

# ... after existing entity isinstance checks ...

elif isinstance(entity, Reflection):
    result.update(_serialize_reflection(entity, props, defaults=defs))
elif isinstance(entity, Inversion):
    result.update(_serialize_inversion(entity, props, defaults=defs))
elif isinstance(entity, Rotor):
    result.update(_serialize_rotor(entity, props, defaults=defs))
elif isinstance(entity, Translator):
    result.update(_serialize_translator(entity, props, defaults=defs))
elif isinstance(entity, Dilator):
    result.update(_serialize_dilator(entity, props, defaults=defs))
elif isinstance(entity, Motor):
    result.update(_serialize_motor(entity, props, defaults=defs))
elif isinstance(entity, GeneralRotor):
    result.update(_serialize_general_rotor(entity, props, defaults=defs))
elif isinstance(entity, GeneralDilator):
    result.update(_serialize_general_dilator(entity, props, defaults=defs))
```

Each `_serialize_*` function extracts the dataclass fields into the flat JSON format
shown in Section 2, with render defaults applied for `color`, `opacity`, `discRadius`,
`planeExtent`, etc.

---

## 6. Default Colors for Operators

| Operator | Default Color | Rationale |
|----------|---------------|-----------|
| Reflection | `#88ccff` (light blue) | Mirror-like, cool reflective feel |
| Inversion | `#cc88ff` (lavender) | Spherical, ethereal |
| Rotor | `#ff8844` (orange) | Warm rotation |
| Translator | `#44aaff` (blue) | Clean directional arrow |
| Motor | `#ff66cc` (pink) | Combined warmth + movement |
| Dilator | `#ffcc44` (amber) | Bright expanding rings |
| GeneralRotor | `#ff9966` (salmon) | Between Rotor and Motor |
| GeneralDilator | `#ffcc88` (peach) | Between Dilator and Translator |

---

### 7.1 Operator Directory & Dispatcher

- [x] **O1:** Create `py/pytanga/viz/templates/renderers/operators/` directory
- [x] **O2:** Operator modules import directly into `factory.js` (no separate operator dispatcher needed — factory handles all dispatch)
- [x] **O3:** Factory returns `null` for unknown kinds (no crash)

### 7.2 Per-Operator Renderer Modules

- [x] **O4:** Created `operators/rotor.js` — `createRotor()` with disc arc (RingGeometry), outer torus, arc line, radial line, and axis line
- [x] **O5:** Created `operators/translator.js` — `createTranslator()` with cylinder shaft + cone head arrow (delegates to `createArrow()`)
- [x] **O6:** Created `operators/motor.js` — `createMotor()` with helix curve + axis line
- [x] **O7:** Created `operators/point_pair.js` — `createPointPair()` with two spheres + connector line
- [x] **O8:** Created `operators/inversion.js` — `createInversion()` with wireframe sphere at center
- [x] **O9:** Created `operators/dilator.js` — `createDilator()` with nested concentric tori (delegates to `createDilatorRings()`)
- [x] **O10:** Created `operators/general_rotor.js` — `createGeneralRotor()` with rotor disc + translator bivector disc + common axis
- [x] **O11:** Created `operators/general_dilator.js` — `createGeneralDilator()` with expanding rings + optional translation arrow
- [x] **O11b:** Created `operators/reflection_line.js` — `createReflectionLine()` with cylinder oriented along reflection direction
- [x] **O11c:** Created `operators/reflection_plane.js` — `createReflectionPlane()` with mirror plane + normal arrow
- [x] **O11d:** Created `operators/reflection_origin.js` — `createReflectionOrigin()` with 3-axis crosshair
- [x] **O12:** Each operator renderer exports exactly one `create*` function
- [x] **O13:** Each module imports shared utilities from `../utils.js`

### 7.3 Entity Factory Integration

- [x] **O14:** Updated `factory.js` — operator imports replace inline functions
- [x] **O15:** `createEntityMesh()` dispatches operator kinds via direct imports: `PointPair`, `Inversion`, `Rotor`, `Translator`, `Dilator`, `Motor`, `GeneralRotor`, `ReflectionLine`, `ReflectionPlane`, `ReflectionOrigin`, `GeneralDilator`
- [x] **O16:** Removed dead inline operator functions from `factory.js`

### 7.4 Serializer & Defaults

- [ ] **O16:** Verify operator serializer already exists in `serializer.py` (Phase 2) — `_serialize_rotor()`, `_serialize_translator()`, etc.
- [ ] **O17:** Verify `Visualizer._defaults` includes operator color keys (`color_rotor`, `color_translator`, etc.)
- [ ] **O18:** Verify `_apply_defaults()` / `_global_key()` correctly resolves operator default keys

### 7.5 Manual Verification

- [ ] **O19:** Manual test: `Rotor(angle=1.57, axis=Direction(0,0,1))` → disc arc shows correct angle and axis orientation
- [ ] **O20:** Manual test: `Rotor` with `angle=2π` → full circle
- [ ] **O21:** Manual test: `Translator(vector=Direction(2,0,0))` → arrow direction and length match
- [ ] **O22:** Manual test: `Motor` → helix pitch reflects translation magnitude
- [ ] **O23:** Manual test: `Reflection` → plane normal matches operator normal
- [ ] **O24:** Manual test: `Inversion(center=Point(0,0,0))` → wireframe sphere at origin
- [ ] **O25:** Manual test: `Dilator` → ring count and max radius configurable via props
- [ ] **O26:** Manual test: `GeneralRotor` → two bivector discs visible with common axis
- [ ] **O27:** Manual test: `GeneralDilator` → rings distributed along translation direction
- [ ] **O28:** Manual test: All operator types (11) render without browser console errors
- [ ] **O29:** Manual test: `removeEntityMesh()` properly disposes operator meshes

## 8. Verification Checklist

- [ ] `factory.js` dispatches all 8 operator kinds correctly.
- [ ] Rotor: disc arc shows correct angle and axis orientation.
- [ ] Rotor: arc extent is proportional to `angle` (full circle at 2π).
- [ ] Translator: arrow direction and length match vector.
- [ ] Motor: helix pitch reflects translation magnitude.
- [ ] Reflection: plane normal matches operator normal.
- [ ] Inversion: wireframe sphere radius matches origin distance.
- [ ] Dilator: ring count and max radius are configurable.
- [ ] GeneralRotor: two bivector discs are visible with common axis.
- [ ] GeneralDilator: rings distributed along translation direction.
- [ ] Labels attach to operator meshes.
- [ ] All operator renderers dispose correctly on removal.
- [ ] `serialize_entity()` produces correct JSON for each operator type.
- [ ] Default colors are applied correctly.