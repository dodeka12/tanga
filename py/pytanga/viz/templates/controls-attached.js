// Tanga 3D Viewer — Attachable Controls
// CSS2DRenderer-based controls that attach to 3D scene objects (same
// mechanism as labels).  Control groups with a parentId are rendered as
// CSS2DObjects parented to the referenced entity mesh.
//
// Imports control factories from controls-panel.js.

import * as THREE from 'three';
import { CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';

// ── Module state ─────────────────────────────────────────────
const _attachedGroups = new Map();  // groupId → { css2d, parentMesh }

// ── Public API ──────────────────────────────────────────────

/**
 * Attach an already-built `GroupView` to a 3D entity as a CSS2DObject.
 *
 * @param {Object} groupView  - `GroupView` instance (its `.el` is attached)
 * @param {Object} parentMesh - THREE.Object3D to parent the CSS2DObject to
 */
export function attachGroupView(groupView, parentMesh) {
    const el = groupView.el;
    el.classList.add('tanga-attached-group');
    el.style.pointerEvents = 'auto';

    el.addEventListener('pointerdown', (e) => e.stopPropagation());
    el.addEventListener('pointermove', (e) => e.stopPropagation());

    const css2d = new CSS2DObject(el);
    // Position 1 unit above the entity center by default
    css2d.position.set(0, 1.0, 0);
    parentMesh.add(css2d);

    const groupId = groupView.groupId || 'unknown';
    _attachedGroups.set(groupId, { css2d, parentMesh });

    parentMesh.userData._attachedGroups = parentMesh.userData._attachedGroups || [];
    parentMesh.userData._attachedGroups.push(groupId);
}

/**
 * Detach and remove a single attached control group by its ID.
 */
export function detachGroup(groupId) {
    const entry = _attachedGroups.get(groupId);
    if (!entry) return;
    entry.css2d.removeFromParent();
    if (entry.css2d.element) entry.css2d.element.remove();
    _attachedGroups.delete(groupId);
}

/**
 * Detach and remove all attached control groups.
 */
export function detachAll() {
    for (const [groupId] of _attachedGroups) {
        detachGroup(groupId);
    }
}
