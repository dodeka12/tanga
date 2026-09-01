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

// ── CSS Injection (attached controls specific styles) ──────

function _injectStyles() {
    if (document.getElementById('tanga-attached-styles')) return;
    const style = document.createElement('style');
    style.id = 'tanga-attached-styles';
    style.textContent = `
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
            display: inline-block;
        }
        .tanga-attached-toggle.expanded {
            transform: rotate(90deg);
        }
        .tanga-attached-controls {
            margin-top: 4px;
            background: rgba(20, 20, 40, 0.92);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 6px;
            padding: 6px 10px;
            min-width: 200px;
            max-width: 280px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5);
            overflow: hidden;
        }
        .tanga-attached-controls.tanga-collapsed {
            display: none;
        }
        .tanga-attached-controls .tanga-control {
            margin: 4px 0;
        }
        .tanga-attached-controls .tanga-control label {
            font-size: 11px;
            color: #aaa;
        }
        .tanga-attached-controls .tanga-value {
            font-size: 11px;
        }
        .tanga-attached-controls .tanga-range-input {
            height: 3px;
        }
        .tanga-attached-controls .tanga-range-input::-webkit-slider-thumb {
            width: 12px;
            height: 12px;
        }
        .tanga-attached-controls .tanga-range-input::-moz-range-thumb {
            width: 12px;
            height: 12px;
        }
        .tanga-attached-controls .tanga-select-input {
            font-size: 11px;
            padding: 2px 4px;
        }
        .tanga-attached-controls .tanga-action-button {
            font-size: 11px;
            padding: 3px 10px;
        }
        .tanga-attached-title .material-icons {
            font-size: 13px;
        }
    `;
    document.head.appendChild(style);
}

// ── Initialize on import ────────────────────────────────────
_injectStyles();