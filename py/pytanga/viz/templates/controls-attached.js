// Tanga 3D Viewer — Attachable Controls
// CSS2DRenderer-based controls that attach to 3D scene objects (same
// mechanism as labels).  Control groups with a parentId are rendered as
// CSS2DObjects parented to the referenced entity mesh.
//
// Imports control factories from controls-panel.js.

import * as THREE from 'three';
import { CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
import { createSlider, createDropdown, createButton, sendControlEvent, throttledSend, throttledFlush } from './controls-panel.js';

// ── Module state ─────────────────────────────────────────────
const _attachedGroups = new Map();  // groupId → { css2d, parentMesh }

// ── Public API ──────────────────────────────────────────────

/**
 * Create and attach a control group to a 3D entity as a CSS2DObject.
 *
 * @param {Object} group     - Group definition from controls_define message
 * @param {Array}  controls  - Array of control definitions for this group
 * @param {Map}    sceneObjects - viewer.js sceneObjects Map
 */
export function attachGroup(group, controls, sceneObjects) {
    const parentMesh = sceneObjects.get(group.parentId)?.obj;
    if (!parentMesh) {
        console.warn('Cannot attach group "' + group.id + '": parent entity "' + group.parentId + '" not found');
        return;
    }

    // Build DOM container
    const container = document.createElement('div');
    container.className = 'tanga-attached-group';
    container.setAttribute('data-group-id', group.id);
    container.style.pointerEvents = 'auto';

    // ── Title bar (always visible, acts as persistent label) ──
    const titleBar = document.createElement('div');
    titleBar.className = 'tanga-attached-title';

    const titleText = document.createElement('span');
    titleText.className = 'tanga-attached-title-text';
    titleText.textContent = group.title || 'Controls';

    const toggleArrow = document.createElement('span');
    toggleArrow.className = 'tanga-attached-toggle';
    if (!group.collapsed) toggleArrow.classList.add('expanded');
    toggleArrow.textContent = '\u25B8'; // ▸ (rotates 90° when expanded)

    titleBar.appendChild(titleText);
    titleBar.appendChild(toggleArrow);
    container.appendChild(titleBar);

    // ── Controls panel (hidden when collapsed) ──
    const controlsDiv = document.createElement('div');
    controlsDiv.className = 'tanga-attached-controls';
    if (group.collapsed) controlsDiv.classList.add('tanga-collapsed');

    for (const ctrlId of (group.controls || [])) {
        const ctrl = controls.find(c => c.id === ctrlId);
        if (!ctrl) continue;
        let el = null;
        if (ctrl.kind === 'slider') el = createSlider(ctrl);
        else if (ctrl.kind === 'dropdown') el = createDropdown(ctrl);
        else if (ctrl.kind === 'button') el = createButton(ctrl);
        if (el) controlsDiv.appendChild(el);
    }
    container.appendChild(controlsDiv);

    // ── Expand/collapse toggle ──
    let collapsed = !!group.collapsed;
    titleBar.addEventListener('click', (e) => {
        e.stopPropagation();
        collapsed = !collapsed;
        if (collapsed) {
            controlsDiv.classList.add('tanga-collapsed');
            toggleArrow.classList.remove('expanded');
        } else {
            controlsDiv.classList.remove('tanga-collapsed');
            toggleArrow.classList.add('expanded');
        }
    });

    // ── Prevent pointer events from reaching the Three.js canvas ──
    container.addEventListener('pointerdown', (e) => e.stopPropagation());
    container.addEventListener('pointermove', (e) => e.stopPropagation());

    // ── CSS2DObject ──
    const css2d = new CSS2DObject(container);
    // Position 1 unit above the entity center by default
    css2d.position.set(0, 1.0, 0);

    parentMesh.add(css2d);

    // ── Track for cleanup ──
    _attachedGroups.set(group.id, { css2d, parentMesh });

    // Track on parent so cleanup on entity removal works
    parentMesh.userData._attachedGroups = parentMesh.userData._attachedGroups || [];
    parentMesh.userData._attachedGroups.push(group.id);
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
    `;
    document.head.appendChild(style);
}

// ── Initialize on import ────────────────────────────────────
_injectStyles();