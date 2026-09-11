// Cone renderer — a double cone (two open cone halves) along `axis` at `vertex`.
// Phase 6: Per-entity module.

import * as THREE from 'three';
import {
    makeMaterial,
    rotationFromDirection,
    styleParam,
    parseColor,
    tagEntity,
    addWireframeOverlay,
} from './utils.js';

function resolveHeight(ent) {
    return Math.max(styleParam(ent, 'extent', 2.0), 0.001);
}

export function createCone(ent) {
    const color = parseColor(ent, '#ffaa00');
    const opacity = styleParam(ent, 'opacity', 0.9);
    const vertex = ent.vertex || [0, 0, 0];
    const axis = ent.axis || [0, 0, 1];
    const halfAngle = Math.max(ent.halfAngle || 0.3, 0.01);
    const height = resolveHeight(ent);
    const radius = height * Math.tan(halfAngle);
    const wireframe = styleParam(ent, 'wireframe', false);

    const group = new THREE.Group();
    const dir = new THREE.Vector3(axis[0], axis[1], axis[2]).normalize();

    for (const sign of [1, -1]) {
        const d = new THREE.Vector3(sign * dir.x, sign * dir.y, sign * dir.z);
        const mesh = new THREE.Mesh(
            new THREE.ConeGeometry(radius, height, 48, 1, true),
            makeMaterial(color, opacity)
        );
        // ConeGeometry apex is at +height/2 along +y; orient +y along `d` and
        // place the apex at `vertex`.
        mesh.setRotationFromQuaternion(rotationFromDirection(d.x, d.y, d.z));
        mesh.position.set(
            vertex[0] - d.x * height / 2,
            vertex[1] - d.y * height / 2,
            vertex[2] - d.z * height / 2,
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
