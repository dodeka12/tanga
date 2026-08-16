# Phase 4 — Apply Texture Labels in Renderers

**Prerequisites:** Phase 3 (`createTextureLabel()` exists in `utils.js`)

**Goal:** Apply texture labels in `sphere.js` and `plane.js` by reading
`ent.style.texture_label` and calling `createTextureLabel()`. Handle the `align`
property for planes. Mark renderers as `async` to await texture creation.

---

## 1. Changes to `sphere.js`

### 1.1 Import `createTextureLabel`

Add to the import block:

```js
import {
    makeMaterial,
    styleParam,
    parseColor,
    tagEntity,
    addWireframeOverlay,
    createTextureLabel,
} from './utils.js';
```

### 1.2 Make `createSphere` async and apply texture label

```js
export async function createSphere(ent) {
    const color = parseColor(ent, '#ffaa00');
    const opacity = styleParam(ent, 'opacity', 0.4);
    const center = ent.center || [0, 0, 0];
    const radius = Math.max(ent.radius || 1.0, 0.001);

    const geometry = new THREE.SphereGeometry(radius, 32, 32);
    const material = makeMaterial(color, opacity);
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(center[0], center[1], center[2]);

    // ── Texture label ──
    const texLabel = ent.style?.texture_label;
    if (texLabel && texLabel.text) {
        // Sphere defaults: center label at equator
        if (texLabel.offset_v === undefined) texLabel.offset_v = 0.25;
        const texture = await createTextureLabel(texLabel.text, texLabel);
        if (texture) {
            material.map = texture;
            material.needsUpdate = true;
        }
    }

    // Wireframe overlay
    const wireframe = styleParam(ent, 'wireframe', false);
    if (wireframe) {
        const wfColor = styleParam(ent, 'wireframe_color', null) || color;
        const wfOpacity = styleParam(ent, 'wireframe_opacity', 1.0);
        const dash = styleParam(ent, 'wireframe_dash', null);
        addWireframeOverlay(
            mesh,
            new THREE.SphereGeometry(radius * 1.005, 24, 24),
            wfColor,
            dash,
            wfOpacity
        );
    }

    tagEntity(mesh, ent);
    return mesh;
}
```

Key design points:
- `texLabel.offset_v` defaults to `0.25` (equator) for spheres. This is a **renderer-side default** — the Python `TextureLabelStyle` keeps `offset_v` as `None`, and the renderer provides the sensible geometry-specific fallback.
- The texture is applied to `material.map`. No additional blending is done.
- When `texture` is `null` (KaTeX unavailable, render error), the mesh renders with the solid material color.

---

## 2. Changes to `plane.js`

### 2.1 Import `createTextureLabel`

Add to the import block:

```js
import {
    makeMaterial,
    rotationFromNormal,
    styleParam,
    parseColor,
    tagEntity,
    addWireframeOverlay,
    createTextureLabel,
} from './utils.js';
```

### 2.2 Make `createPlane` async and apply texture label with align

```js
export async function createPlane(ent) {
    const color = parseColor(ent, '#4488ff');
    const opacity = styleParam(ent, 'opacity', 0.3);
    const extent = styleParam(ent, 'extent', 10.0);
    const point = ent.point || [0, 0, 0];
    const normal = ent.normal || [0, 0, 1];

    const geometry = new THREE.PlaneGeometry(extent * 2, extent * 2);
    const material = makeMaterial(color, opacity, true);
    const mesh = new THREE.Mesh(geometry, material);

    mesh.position.set(point[0], point[1], point[2]);
    mesh.setRotationFromQuaternion(rotationFromNormal(normal[0], normal[1], normal[2]));

    // ── Texture label ──
    const texLabel = ent.style?.texture_label;
    if (texLabel && texLabel.text) {
        // Plane defaults: no offset
        if (texLabel.offset_v === undefined) texLabel.offset_v = 0.0;

        const texture = await createTextureLabel(texLabel.text, texLabel);
        if (texture) {
            // Apply align mode
            const align = texLabel.align || 'stretch';
            switch (align) {
                case 'fit':
                    texture.wrapS = THREE.ClampToEdgeWrapping;
                    texture.wrapT = THREE.ClampToEdgeWrapping;
                    texture.repeat.set(1, 1);
                    break;
                case 'repeat':
                    texture.wrapS = THREE.RepeatWrapping;
                    texture.wrapT = THREE.RepeatWrapping;
                    texture.repeat.set(texLabel.repeat_u || 1, texLabel.repeat_v || 1);
                    break;
                case 'stretch':
                default:
                    texture.wrapS = THREE.ClampToEdgeWrapping;
                    texture.wrapT = THREE.ClampToEdgeWrapping;
                    texture.repeat.set(1, 1);
                    break;
            }
            material.map = texture;
            material.needsUpdate = true;
        }
    }

    // Wireframe overlay
    const wireframe = styleParam(ent, 'wireframe', false);
    if (wireframe) {
        const wfColor = styleParam(ent, 'wireframe_color', null) || color;
        const wfOpacity = styleParam(ent, 'wireframe_opacity', 1.0);
        const dash = styleParam(ent, 'wireframe_dash', null);
        addWireframeOverlay(
            mesh,
            new THREE.PlaneGeometry(extent * 2, extent * 2),
            wfColor,
            dash,
            wfOpacity
        );
    }

    tagEntity(mesh, ent);
    return mesh;
}
```

Align mode behavior:

| `align` | Wrapping | Repeat |
|---------|----------|--------|
| `"stretch"` (default) | `ClampToEdgeWrapping` | `(1, 1)` — fills entire quad |
| `"fit"` | `ClampToEdgeWrapping` | `(1, 1)` — centered, letterboxed |
| `"repeat"` | `RepeatWrapping` | `(repeat_u, repeat_v)` from style |

---

## 3. Changes to `factory.js`

### 3.1 Make `createEntityMesh` async

Only `createSphere` and `createPlane` need `await`. Other renderers remain
synchronous — `await` on a non-Promise just wraps the value in a resolved
Promise, so no change in behavior.

```js
export async function createEntityMesh(ent) {
    let mesh;

    switch (ent.kind) {
        case 'Point':
        case 'HPoint':
            if (ent.style?.style_type === 'CrossHairPointStyle') {
                mesh = createCrossHairPoint(ent);
            } else {
                mesh = createPoint(ent);
            }
            break;
        case 'Direction':
            mesh = createDirection(ent);
            break;
        case 'Line':
            mesh = createLine(ent);
            break;
        case 'Plane':
            mesh = await createPlane(ent);
            break;
        case 'Circle':
            mesh = createCircle(ent);
            break;
        case 'Sphere':
            mesh = await createSphere(ent);
            break;
        // ... all other cases unchanged ...
    }

    if (mesh) {
        tagEntity(mesh, ent);
    }
    return mesh;
}
```

---

## 4. Changes to `viewer.js`

Find the call site where `createEntityMesh(ent)` is called (likely in
`upsertObject` or a scene loading function) and add `await`:

```js
// Before:
const mesh = createEntityMesh(ent);

// After:
const mesh = await createEntityMesh(ent);
```

If the calling function is not already `async`, mark it `async`.

---

## 5. Implementation Checklist

- [ ] Import `createTextureLabel` in `sphere.js`
- [ ] Make `createSphere` async; apply texture label with default `offset_v=0.25`
- [ ] Import `createTextureLabel` in `plane.js`
- [ ] Make `createPlane` async; apply texture label with default `offset_v=0.0`; handle `align`
- [ ] Make `createEntityMesh` async in `factory.js`; `await` `createSphere` and `createPlane`
- [ ] Update `createEntityMesh` call site in `viewer.js` to `await`
- [ ] Verify all other renderers still work

---

## 6. Verification

- [ ] Sphere without `texture_label` renders with solid wireframe color (no change)
- [ ] Sphere with `text: "S₁"` → plain text on equator, tiled per `repeat_u`
- [ ] Sphere with `text: "E=mc^2", math_mode: true` → KaTeX formula on equator
- [ ] Plane without `texture_label` renders as translucent quad (no change)
- [ ] Plane with `text: "z=3", align: "stretch"` → text fills quad
- [ ] Plane with `text: "z=3", align: "fit"` → text centered, aspect preserved
- [ ] Plane with `text: "Tile", align: "repeat", repeat_u: 3, repeat_v: 3` → 3×3 grid
- [ ] Scene with multiple textured entities loads without errors
- [ ] `katex` unavailable → graceful fallback (console warning, plain material)
- [ ] Browser console has no errors during normal operation