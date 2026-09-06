// Tanga 3D Viewer — Shared scene-graph construction (live viewer + HTML export).
// Entity node construction (transform wrap + `parent_id` parenting) and
// overlay/label creation, shared by `viewer.js` and the export bootstrap so a
// render-pipeline change is made once.

import * as THREE from 'three';
import { CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
import { createEntityMesh, removeEntityMesh } from './renderers/factory.js';
import { sendLog } from './events.js';

export function isIdentityTransform(transform) {
    if (!transform) return true;
    const p = transform.position || [0, 0, 0];
    const r = transform.rotation || [0, 0, 0];
    const s = transform.scale || [1, 1, 1];
    return p[0] === 0 && p[1] === 0 && p[2] === 0
        && r[0] === 0 && r[1] === 0 && r[2] === 0
        && s[0] === 1 && s[1] === 1 && s[2] === 1;
}

export function applyTransformToObject(obj, transform) {
    if (!transform) return;
    if (transform.position) obj.position.set(transform.position[0], transform.position[1], transform.position[2]);
    if (transform.rotation) obj.rotation.set(transform.rotation[0], transform.rotation[1], transform.rotation[2]);
    if (transform.scale) obj.scale.set(transform.scale[0], transform.scale[1], transform.scale[2]);
}

export function wrapWithNodeTransform(mesh, transform) {
    if (isIdentityTransform(transform)) return mesh;
    const node = new THREE.Group();
    node.add(mesh);
    applyTransformToObject(node, transform);
    return node;
}

// Build a scene-layer object: mesh → node transform wrap → parent under
// `parent_id` (or the scene) → register.  Returns the registry entry or null.
export async function buildSceneObject(obj, scene, registry) {
    const mesh = await createEntityMesh(obj);
    if (!mesh) return null;

    const node = wrapWithNodeTransform(mesh, obj.transform);
    const parent = obj.parent_id ? registry.get(obj.parent_id) : null;
    if (parent && parent.obj) {
        parent.obj.add(node);
    } else {
        scene.add(node);
    }
    node.userData.parentId = obj.parent_id || null;

    const entry = { obj: node, mesh, data: { ...obj }, layer: 'scene' };
    registry.set(obj.id, entry);
    return entry;
}

// Build a label overlay as a CSS2DObject, parented under `attach_to` (or the
// legacy `parentId`) with the offset/align transform applied.  Annotation and
// title overlays are host-specific and intentionally not handled here.
export function buildOverlay(obj, scene, registry) {
    if (obj.kind !== 'label') return null;
    if (!obj.text) return null;

    const div = document.createElement('div');
    div.textContent = obj.text;
    const s = obj.style || {};
    div.style.fontFamily = s.font_family || 'sans-serif';
    div.style.fontSize = (s.font_size || 14) + 'px';
    div.style.color = s.color || '#ffffff';
    div.style.backgroundColor = s.background || 'rgba(0, 0, 0, 0.6)';
    div.style.padding = '2px 6px';
    div.style.borderRadius = '3px';
    div.style.userSelect = 'none';
    div.style.whiteSpace = 'nowrap';
    if (typeof renderMathInElement !== 'undefined') {
        try {
            renderMathInElement(div, {
                delimiters: [
                    { left: '$$', right: '$$', display: true },
                    { left: '$', right: '$', display: false },
                ],
                throwOnError: false,
            });
        } catch (e) {
            console.warn('KaTeX label rendering error:', e);
            sendLog('warn', 'KaTeX label rendering error', { source: 'scene-builder.js', data: { error: String(e) } });
        }
    }

    const container = document.createElement('div');
    container.appendChild(div);
    const css2d = new CSS2DObject(container);

    const attachId = obj.attach_to ?? obj.parentId;
    if (attachId) {
        const pos = obj.position || [0, 0, 0];
        css2d.position.set(pos[0], pos[1], pos[2]);
        // CSS2DRenderer centers the container; counter that on the inner div
        // plus apply the pixel offset:
        const off2d = s.offset_2d || [0, 0];
        const align = s.align || [0.5, 0.5];
        const rotation = s.rotation || 0;
        const tx = (0.5 - align[0]) * 100;
        const ty = (0.5 - align[1]) * 100;
        div.style.transformOrigin = `${align[0] * 100}% ${align[1] * 100}%`;
        div.style.transform = `translate(${off2d[0]}px, ${off2d[1]}px) translate(${tx}%, ${ty}%) rotate(${rotation}deg)`;

        const parent = registry.get(attachId);
        if (parent && parent.obj) {
            parent.obj.add(css2d);
            parent.obj.userData._labels = parent.obj.userData._labels || [];
            parent.obj.userData._labels.push(obj.id);
            css2d.userData._parentId = attachId;
        } else {
            scene.add(css2d);
        }
    } else {
        const pos = obj.position || [0, 0, 0];
        css2d.position.set(pos[0], pos[1], pos[2]);
        scene.add(css2d);
    }

    const entry = { obj: css2d, mesh: null, data: { ...obj }, el: div, layer: 'overlay' };
    registry.set(obj.id, entry);
    return entry;
}

// Dispose and unregister: scene objects via `removeEntityMesh`; overlays via
// parent detachment + DOM removal.
export function removeObject(id, registry) {
    const entry = registry.get(id);
    if (!entry) return false;

    if (entry.layer === 'scene') {
        if (entry.obj) removeEntityMesh(entry.obj);
    } else {
        if (entry.obj && entry.obj.removeFromParent) entry.obj.removeFromParent();
        if (entry.obj && entry.obj.element) entry.obj.element.remove();
        if (entry.el) entry.el.remove();
    }
    registry.delete(id);
    return true;
}
