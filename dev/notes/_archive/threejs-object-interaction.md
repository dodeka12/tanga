# Three.js Object Interaction Options

Three.js offers several built-in and addon-based mechanisms for interacting with 3D objects. Below is a comprehensive overview, organized from simplest to most advanced.

---

## 1. OrbitControls (Camera Interaction — Most Common)

This is the primary way users interact with a scene. It's not "object" interaction per se, but camera manipulation around the scene:

- **Rotate**: Left-click + drag (orbits camera around a target point)
- **Pan**: Middle-click + drag (slides the camera along the screen plane)
- **Zoom**: Right-click + drag or scroll wheel (dolly in/out)
- **Damping/Inertia**: Smooth deceleration after releasing the mouse
- Configurable via `controls.target`, `controls.minDistance`, `controls.maxDistance`, `controls.enableRotate`, etc.

```js
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.mouseButtons = {
  LEFT: THREE.MOUSE.ROTATE,
  MIDDLE: THREE.MOUSE.PAN,
  RIGHT: THREE.MOUSE.ZOOM
};
controls.screenSpacePanning = true;
```

### Other Camera Controls in the Three.js Addons

| Control | Description |
|---------|-------------|
| **TrackballControls** | Free 6-DOF rotation (no up-vector constraint) |
| **FlyControls** | First-person flight-style movement |
| **PointerLockControls** | FPS-style mouse-look |
| **ArcballControls** | Modern alternative to OrbitControls with better touch support |
| **FirstPersonControls** | Alternative first-person navigation |
| **MapControls** | Map-like pan and zoom (suitable for 2D planes in 3D) |

---

## 2. Raycasting (Object Picking/Selection)

Three.js provides `THREE.Raycaster` for detecting which object the mouse is hovering over or clicking:

```js
const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();

window.addEventListener('click', (event) => {
  mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
  mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

  raycaster.setFromCamera(mouse, camera);
  const intersects = raycaster.intersectObjects(scene.children, true);

  if (intersects.length > 0) {
    const clickedObject = intersects[0].object;
    // Highlight, select, or show info for the clicked object
  }
});
```

### Raycaster Features

- **`intersectObjects(array, recursive)`** — with recursive flag for nested scene graphs
- **`intersectOctree()`** — optimized raycasting against large point sets
- **Face/uv/normal information** in intersection results (`intersect.face`, `intersect.uv`, `intersect.faceNormal`)
- **Threshold** — `raycaster.params.Points.threshold` for point cloud hit testing
- **Line threshold** — `raycaster.params.Line.threshold` for line hit testing precision

---

## 3. DragControls (Drag & Drop Objects)

From the Three.js addons, `DragControls` lets users click and drag 3D objects around the scene:

```js
import { DragControls } from 'three/addons/controls/DragControls.js';

const dragControls = new DragControls(draggableObjects, camera, renderer.domElement);

dragControls.addEventListener('dragstart', (event) => {
  event.object.material.emissive.set(0xaaaaaa); // highlight on grab
  controls.enabled = false; // disable orbit while dragging
});

dragControls.addEventListener('drag', (event) => {
  // Real-time position update — event.object.position is already updated
});

dragControls.addEventListener('dragend', (event) => {
  event.object.material.emissive.set(0x000000); // reset highlight
  controls.enabled = true;
});
```

---

## 4. TransformControls (Gizmo-Based Manipulation)

More advanced than DragControls — adds visual gizmos for translate/rotate/scale, similar to 3D editors like Blender or Unity:

```js
import { TransformControls } from 'three/addons/controls/TransformControls.js';

const transformControls = new TransformControls(camera, renderer.domElement);
transformControls.attach(targetMesh);
transformControls.setMode('translate'); // or 'rotate' or 'scale'
transformControls.setSize(0.7);          // gizmo size
transformControls.setSpace('world');     // or 'local'

// Keyboard shortcuts (built-in):
// W = translate, E = rotate, R = scale
// Shift+W/E/R = toggle world/local space
// X, Y, Z = constrain to axis
// Shift+X/Y/Z = constrain to plane (YZ, XZ, XY)
```

TransformControls also supports:
- **Snapping** — `transformControls.setTranslationSnap(1)` to snap to grid
- **Rotation snap** — `transformControls.setRotationSnap(Math.PI / 4)` for 45° increments
- **Scale snap** — `transformControls.setScaleSnap(0.5)`
- **Events** — `objectChange`, `mouseDown`, `mouseUp`, `change`

---

## 5. Hover Effects (CSS-Style Hover)

Using raycaster in the `mousemove` event, you can implement hover highlighting:

```js
let hoveredObject = null;

window.addEventListener('mousemove', (event) => {
  mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
  mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

  raycaster.setFromCamera(mouse, camera);
  const intersects = raycaster.intersectObjects(scene.children, true);

  if (intersects.length > 0) {
    const obj = intersects[0].object;
    if (hoveredObject !== obj) {
      // Reset previous hover
      if (hoveredObject) hoveredObject.material.emissive.set(0x000000);
      // Set new hover
      hoveredObject = obj;
      hoveredObject.material.emissive.set(0x333333);
      document.body.style.cursor = 'pointer';
    }
  } else {
    if (hoveredObject) {
      hoveredObject.material.emissive.set(0x000000);
      hoveredObject = null;
      document.body.style.cursor = 'default';
    }
  }
});
```

Common hover effects:
- Change material `emissive` color (glow highlight)
- Scale object up slightly (`mesh.scale.set(1.1, 1.1, 1.1)`)
- Change material `color` or `opacity`
- Show a tooltip (HTML overlay positioned via CSS)
- Change cursor style

---

## 6. Selection/Highlighting Techniques

Once an object is picked, there are several ways to visually indicate selection:

| Technique | How | Pros/Cons |
|-----------|-----|-----------|
| **Outline effect** | `OutlinePass` from post-processing addons (EffectComposer + OutlinePass) | Visually clean, no geometry needed; requires full post-processing pipeline |
| **Emissive glow** | Set `material.emissive` to a bright color | Simple, no extra objects; only works on MeshStandardMaterial/MeshPhongMaterial |
| **Wireframe overlay** | Add a second mesh with the same geometry but `material.wireframe = true` | Clear indication; doubles geometry count |
| **Bounding box** | `THREE.BoxHelper` — toggle visibility on selection | Easy to add/remove; can be slightly imprecise for rotated objects |
| **Selection box** | `SelectionBox` / `SelectionHelper` addons for rectangular marquee selection | Good for multi-select; GPU-based selection |

### BoxHelper Example

```js
const boxHelper = new THREE.BoxHelper(selectedMesh, 0xffff00);
scene.add(boxHelper);
// When deselected:
scene.remove(boxHelper);
```

### OutlinePass Example

```js
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { OutlinePass } from 'three/addons/postprocessing/OutlinePass.js';

const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));

const outlinePass = new OutlinePass(
  new THREE.Vector2(window.innerWidth, window.innerHeight), scene, camera
);
outlinePass.edgeStrength = 3;
outlinePass.edgeGlow = 1;
outlinePass.visibleEdgeColor.set('#ffff00');
outlinePass.hiddenEdgeColor.set('#190a05');
outlinePass.selectedObjects = [targetMesh]; // array of selected objects
composer.addPass(outlinePass);

// In render loop:
composer.render(); // instead of renderer.render(scene, camera)
```

---

## 7. Interactive Mesh Properties

Three.js materials support making objects interactive beyond picking:

| Property | Effect |
|----------|--------|
| `material.opacity` / `material.transparent` | Fade objects on hover/selection |
| `MeshStandardMaterial.roughness` | Change surface roughness dynamically |
| `MeshStandardMaterial.metalness` | Change metallic appearance |
| `LineBasicMaterial` / `LineDashedMaterial` | Dashed lines for selected wireframes |
| `material.wireframe` | Toggle wireframe mode |
| `material.color` | Change base color |
| `material.emissive` | Self-illumination for glow effects |
| `Sprite` objects | Billboarded labels that always face the camera (useful for annotations) |

---

## 8. GUI Integration

You can overlay HTML-based UI controls for manipulating objects:

### lil-gui (dat.gui Successor)

Auto-generates sliders, color pickers, checkboxes, and dropdowns:

```js
import GUI from 'lil-gui';

const gui = new GUI();
const objFolder = gui.addFolder('Selected Object');
objFolder.add(selectedMesh.position, 'x', -10, 10).name('Position X');
objFolder.add(selectedMesh.position, 'y', -10, 10).name('Position Y');
objFolder.add(selectedMesh.position, 'z', -10, 10).name('Position Z');
objFolder.add(selectedMesh.material, 'opacity', 0, 1).name('Opacity');
objFolder.addColor(selectedMesh.material, 'color').name('Color');
```

### CSS3DRenderer

Renders DOM elements in 3D space — useful for labels, info cards that live "on" objects:

```js
import { CSS3DRenderer, CSS3DObject } from 'three/addons/renderers/CSS3DRenderer.js';

const labelDiv = document.createElement('div');
labelDiv.textContent = 'Point A';
labelDiv.style.color = 'white';
labelDiv.style.fontSize = '14px';

const label = new CSS3DObject(labelDiv);
label.position.copy(objectWorldPosition);
scene.add(label);
```

### HTML Overlays (2D Screen Space)

Compute 3D→2D projection and position HTML divs over the canvas:

```js
const vector = objectWorldPosition.clone().project(camera);
const x = (vector.x * 0.5 + 0.5) * window.innerWidth;
const y = (-vector.y * 0.5 + 0.5) * window.innerHeight;

tooltipDiv.style.left = `${x}px`;
tooltipDiv.style.top = `${y}px`;
tooltipDiv.style.display = vector.z < 1 ? 'block' : 'none'; // hide if behind camera
```

---

## 9. Touch & Multi-Touch (Mobile)

OrbitControls supports touch gestures natively:

| Gesture | Action |
|---------|--------|
| One finger | Rotate |
| Two finger pinch | Zoom |
| Two finger swipe | Pan |
| Three fingers | Pan |

For custom touch interactions, use `event.touches` in pointer events:

```js
renderer.domElement.addEventListener('touchstart', (event) => {
  for (const touch of event.touches) {
    // touch.clientX, touch.clientY, touch.identifier
  }
});
```

---

## 10. Advanced: Instanced Mesh Interaction

For scenes with thousands of identical objects (e.g., point clouds, particles), use `THREE.InstancedMesh` for performance, and interact via:

- **Custom shader-based picking** — encode instance IDs in a render target
- **GPU picking** — render instance IDs as colors to a framebuffer, read back on click
- **Approximate spatial queries** — use bounding spheres/octree for fast pre-filtering before precise raycasting

---

## Summary Table

| Interaction Type | Three.js Mechanism | Typical Use Case |
|---|---|---|
| Look around scene | OrbitControls / TrackballControls | General navigation |
| Pick/select objects | Raycaster + click handler | Click to inspect |
| Drag objects | DragControls | Reposition entities |
| Manipulate with gizmos | TransformControls | 3D editor-style transforms |
| Hover effects | Raycaster + mousemove | Visual feedback |
| Outline selection | OutlinePass (post-processing) | Clean visual selection indicator |
| Bounding box selection | BoxHelper | Simple selection highlight |
| Box/region selection | SelectionBox / SelectionHelper | Select multiple objects |
| Emissive highlight | material.emissive | Quick glow on hover/select |
| Wireframe overlay | Duplicate mesh + wireframe | Geometric emphasis |
| Annotate objects | CSS3DRenderer / Sprites | Labels, tooltips |
| HTML overlay tooltips | vector.project() + CSS | 2D labels in screen space |
| GUI parameter editing | lil-gui | Color/size/opacity controls |
| Touch navigation | OrbitControls (built-in) | Mobile support |
| GPU picking | Custom shader framebuffer | High-performance selection for thousands of objects |