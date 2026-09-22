// Cylinder renderer — renders a solid cylinder along the canonical +Y axis,
// spanning `length` with cross-section `radius`.  Placement (origin + axis +
// `alignCenter` offset) rides on the node transform.
// Phase 4: Per-entity module.

import * as THREE from 'three';
import {
    makeMaterial,
    styleParam,
    parseColor,
    tagEntity,
    applyStyleUpdate,
    approxEqual,
    addWireframeOverlay,
} from './utils.js';
import { styleNeedsRebuild } from './style-diff.js';

function resolveCylinderLength(ent) {
    return Math.max(ent.length || 1.0, 0.001);
}

function resolveCylinderRadius(ent) {
    return Math.max(ent.radius || 0.1, 0.001);
}

export function createCylinder(ent) {
    const color = parseColor(ent, '#44aaff');
    const opacity = styleParam(ent, 'opacity', 0.9);
    const radius = resolveCylinderRadius(ent);
    const length = resolveCylinderLength(ent);

    // CylinderGeometry is centered at its own origin along +Y.
    const geometry = new THREE.CylinderGeometry(radius, radius, length, 24, 1);
    const mesh = new THREE.Mesh(geometry, makeMaterial(color, opacity));

    const wireframe = styleParam(ent, 'wireframe', false);
    if (wireframe) {
        const wfColor = styleParam(ent, 'wireframe_color', null) || color;
        const wfOpacity = styleParam(ent, 'wireframe_opacity', 1.0);
        const dash = styleParam(ent, 'wireframe_dash', null);
        addWireframeOverlay(
            mesh,
            new THREE.CylinderGeometry(radius * 1.005, radius * 1.005, length, 24, 1),
            wfColor,
            dash,
            wfOpacity
        );
    }

    tagEntity(mesh, ent);
    return mesh;
}

export function updateCylinder(mesh, ent, prev) {
    // A radius/length change alters the geometry; cheaper to rebuild.
    if (prev && !approxEqual(resolveCylinderLength(ent), resolveCylinderLength(prev))) return false;
    if (prev && !approxEqual(resolveCylinderRadius(ent), resolveCylinderRadius(prev))) return false;
    if (styleNeedsRebuild(ent, prev)) return false;

    applyStyleUpdate(mesh, ent);
    return true;
}
