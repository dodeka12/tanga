# Phase 3 — JS Frontend: Attachable Controls

CSS2DRenderer-based controls that can be attached to 3D scene objects, similar
to the existing label system. When a control group has a `parentId`, its title
bar is rendered as a CSS2DObject child of the referenced 3D mesh. The controls
expand/collapse in a popup-like panel relative to the title bar.

References: [Overview](./README.md) | [Phase 1](./phase1-protocol-and-data-model.md) | [Phase 2](./phase2-frontend-control-panel.md)

---

## 3.1 Architecture

```
viewer.js entityMeshes Map
    │
    ├── mesh for entity "sphere_b"
    │       │
    │       └── CSS2DObject (control group title bar)
    │               │
    │               ├── <div class="tanga-attached-group">
    │               │       <div class="tanga-attached-title">Sphere B ▸</div>
    │               │       <div class="tanga-attached-controls hidden">
    │               │           <!-- sliders, dropdowns, buttons -->
    │               │       </div>
    │               │   </div>
    │               │
    │               └── CSS2DRenderer positions this in 3D space
    │
    └── CSS2DRenderer (existing window._labelRenderer) renders all CSS2DObjects
```

Attached controls reuse the **existing CSS2DRenderer** (`window._labelRenderer`)
that is already set up in `viewer.js`. No new renderer is needed.

A new file: `py/pytanga/viz/templates/controls-attached.js`.

## 3.2 Title Bar as CSS2DObject

When a group has `parentId` set to an entity ID, the control group is NOT
rendered in the fixed-position control panel from Phase 2. Instead:

1. The group's title bar is wrapped in a CSS2DObject and added as a child of
   the parent mesh (the 3D entity).
2. The title bar is always visible and follows the 3D object in screen space
   (via CSS2DRenderer).
3. Clicking the title bar toggles an expandable panel that shows the controls.
   The expanded panel is also a CSS2DObject child, positioned slightly below
   the title bar.

### DOM Structure for Attached Group

```html
<!-- Container (CSS2DObject element) -->
<div class="tanga-attached-group" data-group-id="sphere_b_group">
    <!-- Always-visible title bar (acts as label) -->
    <div class="tanga-attached-title">
        <span class="tanga-attached-title-text">Sphere B</span>
        <span class="tanga-attached-toggle">▸</span>
    </div>
    <!-- Expandable controls (hidden when collapsed) -->
    <div class="tanga-attached-controls tanga-collapsed">
        <div class="tanga-control tanga-slider">
            <label>Radius <span class="tanga-value">1.2</span></label>
            <input type="range" min="0.5" max="5.0" step="0.1" value="1.2">
        </div>
        <div class="tanga-control tanga-dropdown">
            <label>Mode</label>
            <select>...</select>
        </div>
        <div class="tanga-control tanga-button">
            <button>Reset</button>
        </div>
    </div>
</div>
```

### CSS for Attached Controls

```css
.tanga-attached-group {
    font-family: sans-serif;
    font-size: 12px;
    color: #fff;
    pointer-events: auto;
    user-select: none;
}
.tanga-attached-title {
    display: flex;
    align-items: center;
    gap: 4px;
    background: rgba(20, 20, 40, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 4px;
    padding: 3px 8px;
    cursor: pointer;
    white-space: nowrap;
}
.tanga-attached-title:hover {
    background: rgba(40, 40, 80, 0.9);
}
.tanga-attached-toggle {
    font-size: 10px;
    transition: transform 0.2s;
}
.tanga-attached-toggle.expanded {
    transform: rotate(90deg);
}
.tanga-attached-controls {
    margin-top: 4px;
    background: rgba(20, 20, 40, 0.92);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 6px;
    padding: 8px 10px;
    min-width: 200px;
    max-width: 280px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5);
    transition: opacity 0.15s, max-height 0.2s;
    overflow: hidden;
}
.tanga-attached-controls.tanga-collapsed {
    display: none;
}
```

## 3.3 Integration with `controls-panel.js`

The attached controls share the control creation logic from Phase 2
(`createSlider`, `createDropdown`, `createButton`). These functions should be
exported from `controls-panel.js` or factored into a shared utility module.

Option A: Export from `controls-panel.js`:
```js
// controls-panel.js
export { createSlider, createDropdown, createButton };
```

Option B: Extract shared utilities to `controls-utils.js`:
```js
// controls-utils.js — shared between panel and attached
export function createSlider(ctrl) { ... }
export function createDropdown(ctrl) { ... }
export function createButton(ctrl) { ... }
export function sendControlEvent(ws, type, controlId, value) { ... }
```

**Recommendation:** Option A initially (simpler, fewer files). If the shared
surface grows, refactor to Option B later.

### `controls-attached.js` Module

```js
import { createSlider, createDropdown, createButton } from './controls-panel.js';

let _ws = null;
let _attachedGroups = new Map();  // groupId → { css2d, parentMesh }

export function setWebSocket(ws) { _ws = ws; }

export function attachGroup(group, controls, entityMeshes, labelRenderer) {
    const parentMesh = entityMeshes.get(group.parentId);
    if (!parentMesh) {
        console.warn(`Cannot attach group "${group.id}": parent entity "${group.parentId}" not found`);
        return;
    }

    // Build DOM
    const container = document.createElement('div');
    container.className = 'tanga-attached-group';
    container.setAttribute('data-group-id', group.id);

    // Title bar
    const titleBar = document.createElement('div');
    titleBar.className = 'tanga-attached-title';
    titleBar.innerHTML = `<span class="tanga-attached-title-text">${escapeHtml(group.title)}</span>
                          <span class="tanga-attached-toggle${group.collapsed ? '' : ' expanded'}">▸</span>`;

    // Controls container
    const controlsDiv = document.createElement('div');
    controlsDiv.className = 'tanga-attached-controls' + (group.collapsed ? ' tanga-collapsed' : '');
    for (const ctrlId of group.controls) {
        const ctrl = controls.find(c => c.id === ctrlId);
        if (!ctrl) continue;
        let el = null;
        if (ctrl.kind === 'slider') el = createSlider(ctrl);
        else if (ctrl.kind === 'dropdown') el = createDropdown(ctrl);
        else if (ctrl.kind === 'button') el = createButton(ctrl);
        if (el) controlsDiv.appendChild(el);
    }

    container.appendChild(titleBar);
    container.appendChild(controlsDiv);

    // Toggle expand/collapse on title click
    titleBar.addEventListener('click', (e) => {
        e.stopPropagation();
        const isCollapsed = controlsDiv.classList.toggle('tanga-collapsed');
        const toggle = titleBar.querySelector('.tanga-attached-toggle');
        if (toggle) toggle.classList.toggle('expanded', !isCollapsed);
    });

    // CSS2DObject
    const css2d = new THREE.CSS2DObject(container);
    // Position the group above the entity by an offset
    // (depends on the entity type — use a default offset that can be overridden)
    const pos = group.position_offset || [0, 0, 0];
    css2d.position.set(pos[0], pos[1], pos[2]);

    parentMesh.add(css2d);

    // Track for cleanup
    _attachedGroups.set(group.id, { css2d, parentMesh });

    // Track on parent so cleanup on entity removal works
    parentMesh.userData._attachedGroups = parentMesh.userData._attachedGroups || [];
    parentMesh.userData._attachedGroups.push(group.id);
}

export function detachGroup(groupId) {
    const entry = _attachedGroups.get(groupId);
    if (!entry) return;
    entry.css2d.removeFromParent();
    if (entry.css2d.element) entry.css2d.element.remove();
    _attachedGroups.delete(groupId);
}

export function detachAll() {
    for (const [groupId] of _attachedGroups) {
        detachGroup(groupId);
    }
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
```

## 3.4 Positioning Offset

The CSS2DObject is positioned relative to the parent mesh. The default offset
places the title bar above the entity's bounding box. Phase 4 can add a
configurable `offset` parameter to the Python `ControlGroup` data class.

For now, a sensible default: `[0, 1.0, 0]` (1 unit above the entity center).
For spheres, this is above the north pole (center Y + radius + offset). The JS
can compute the entity's bounding box to auto-position, but a fixed offset is
simpler and sufficient for the initial implementation.

## 3.5 Interaction with Entity Removal

When an entity is removed from the scene, its attached controls must also be
cleaned up. The existing `removeEntityMesh` path in `viewer.js` already cleans
up labels. Extend it to also clean up attached groups.

In `viewer.js`, the `msg.removed` handling in `handleMessage`:

```js
for (const id of msg.removed) {
    // ... existing label cleanup ...
    
    // Clean up attached control groups
    const mesh = entityMeshes.get(id);
    if (mesh && mesh.userData._attachedGroups) {
        for (const groupId of mesh.userData._attachedGroups) {
            detachGroup(groupId);
        }
    }
}
```

## 3.6 Interaction with OrbitControls

CSS2DObject elements have `pointer-events: auto` by default. When the user
clicks a control title bar or expands the panel, click events must NOT
propagate to the OrbitControls canvas (which would initiate a pan or rotate).

All control DOM elements must call `e.stopPropagation()` on `mousedown`,
`click`, and `pointerdown` events. The CSS2DRenderer's DOM element already has
`pointer-events: none` set in `viewer.js`, but the individual control elements
must explicitly block propagation.

This is handled by the individual control factories in Phase 2 (adding
`e.stopPropagation()` in event listeners).

---

## 3.7 Implementation Checklist

- [ ] 3.1 Create `py/pytanga/viz/templates/controls-attached.js`
- [ ] 3.2 Implement `attachGroup(group, controls, entityMeshes, labelRenderer)`
- [ ] 3.3 Implement `detachGroup(groupId)` and `detachAll()`
- [ ] 3.4 Implement title bar with expand/collapse toggle in CSS2DRenderer
- [ ] 3.5 Reuse `createSlider`/`createDropdown`/`createButton` from Phase 2 (export from `controls-panel.js`)
- [ ] 3.6 Add `stopPropagation` on all control DOM events to prevent orbit control interference
- [ ] 3.7 Position title bar above parent entity with sensible default offset
- [ ] 3.8 Extend `viewer.js` entity removal to clean up attached groups via `userData._attachedGroups`
- [ ] 3.9 Add `handleControlsDefine` logic to route groups with `parentId` to `attachGroup()` instead of the fixed panel
- [ ] 3.10 Inject attached-controls CSS via `<style>` element
- [ ] 3.11 Manual test: attach a group to a sphere, verify title follows sphere on rotate/pan
- [ ] 3.12 Manual test: expand/collapse controls, verify slider changes send WebSocket events
- [ ] 3.13 Manual test: remove the parent entity, verify attached controls are cleaned up