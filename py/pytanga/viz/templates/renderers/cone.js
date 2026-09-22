// Cone renderer — a double cone (two open cone halves) along the canonical +Y
// axis with its apex at the origin.  Placement (vertex + axis) rides on the
// node transform.
// Phase 6: Per-entity module.

import * as THREE from 'three';
import {
    makeMaterial,
    rotationFromDirection,
    styleParam,
    parseColor,
    tagEntity,
    addWireframeOverlay,
    applyStyleUpdate,
    contentChanged,
} from './utils.js';
import { styleNeedsRebuild } from './style-diff.js';

function resolveHeight(ent) {
    return Math.max(styleParam(ent, 'extent', 2.0), 0.001);
}

export function createCone(ent) {
    const color = parseColor(ent, '#ffaa00');
    const opacity = styleParam(ent, 'opacity', 0.9);
    const halfAngle = Math.max(ent.halfAngle || 0.3, 0.01);
    const height = resolveHeight(ent);
    const radius = height * Math.tan(halfAngle);
    const wireframe = styleParam(ent, 'wireframe', false);

    const group = new THREE.Group();

    for (const sign of [1, -1]) {
        const d = new THREE.Vector3(0, sign, 0);
        const mesh = new THREE.Mesh(
            new THREE.ConeGeometry(radius, height, 48, 1, true),
            makeMaterial(color, opacity)
        );
        // ConeGeometry apex is at +height/2 along +y; orient +y along `d` and
        // place the apex at the origin.
        mesh.setRotationFromQuaternion(rotationFromDirection(d.x, d.y, d.z));
        mesh.position.set(
            -d.x * height / 2,
            -d.y * height / 2,
            -d.z * height / 2,
        );
        group.add(mesh);

        if (wireframe) {
            const wfColor = styleParam(ent, 'wireframe_color', null) || color;
            const wfOpacity = styleParam(ent, 'wireframe_opacity', 1.0);
            const dash = styleParam(ent, 'wireframe_dash', null);
            addWireframeOverlay(
                mesh,
                new THREE.ConeGeometry(radius * 1.005, height, 24, 1, true),
                wfColor,
                dash,
                wfOpacity
            );
        }
    }

    tagEntity(group, ent);
    return group;
}

export function updateCone(mesh, ent, prev) {
    if (contentChanged(ent, prev, ['halfAngle'])) return false;
    if (styleNeedsRebuild(ent, prev)) return false;
    applyStyleUpdate(mesh, ent);
    return true;
}
