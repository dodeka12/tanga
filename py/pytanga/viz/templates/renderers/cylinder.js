// Cylinder renderer — renders a solid cylinder oriented along `axis`, spanning
// `length` with cross-section `radius`.  `alignCenter` positions `origin` along
// the length (0 = start/base point, 0.5 = center).
// Phase 4: Per-entity module.

import * as THREE from 'three';
import {
    makeMaterial,
    rotationFromDirection,
    styleParam,
    parseColor,
    tagEntity,
    applyStyleUpdate,
    approxEqual,
    addWireframeOverlay,
} from './utils.js';

function resolveCylinderLength(ent) {
    return Math.max(ent.length || 1.0, 0.001);
}

function resolveCylinderRadius(ent) {
    return Math.max(ent.radius || 0.1, 0.001);
}

function resolveAlignCenter(ent) {
    return ent.alignCenter ?? 0.0;
}

export function createCylinder(ent) {
    const color = parseColor(ent, '#44aaff');
    const opacity = styleParam(ent, 'opacity', 0.9);
    const radius = resolveCylinderRadius(ent);
    const length = resolveCylinderLength(ent);
    const origin = ent.origin || [0, 0, 0];
    const axis = ent.axis || [0, 0, 1];
    const alignCenter = resolveAlignCenter(ent);

    const geometry = new THREE.CylinderGeometry(radius, radius, length, 24, 1);
    const mesh = new THREE.Mesh(geometry, makeMaterial(color, opacity));

    const d = new THREE.Vector3(axis[0], axis[1], axis[2]).normalize();
    mesh.setRotationFromQuaternion(rotationFromDirection(d.x, d.y, d.z));
    // CylinderGeometry is centered at its own origin.  `alignCenter` is the
    // fraction of `length` where `origin` sits (0 = start, 0.5 = center), so
    // the center is offset by (0.5 - alignCenter) * length along the axis.
    const offset = length * (0.5 - alignCenter);
    mesh.position.set(
        origin[0] + d.x * offset,
        origin[1] + d.y * offset,
        origin[2] + d.z * offset
    );

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
    // A radius/length/align change alters the geometry; cheaper to rebuild.
    if (prev && !approxEqual(resolveCylinderLength(ent), resolveCylinderLength(prev))) return false;
    if (prev && !approxEqual(resolveCylinderRadius(ent), resolveCylinderRadius(prev))) return false;
    if (prev && !approxEqual(resolveAlignCenter(ent), resolveAlignCenter(prev))) return false;

    const origin = ent.origin || prev?.origin || [0, 0, 0];
    const axis = ent.axis || prev?.axis || [0, 0, 1];
    const length = resolveCylinderLength(ent);
    const offset = length * (0.5 - resolveAlignCenter(ent));

    const d = new THREE.Vector3(axis[0], axis[1], axis[2]).normalize();
    mesh.setRotationFromQuaternion(rotationFromDirection(d.x, d.y, d.z));
    mesh.position.set(
        origin[0] + d.x * offset,
        origin[1] + d.y * offset,
        origin[2] + d.z * offset
    );

    applyStyleUpdate(mesh, ent);
    return true;
}
