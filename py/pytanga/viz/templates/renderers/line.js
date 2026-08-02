// Line renderer — renders as a cylinder along the direction vector
// with optional wireframe overlay.
// Phase 5: Per-entity module.

import * as THREE from 'three';
import {
    makeMaterial,
    rotationFromDirection,
    styleParam,
    parseColor,
    tagEntity,
    addWireframeOverlay,
} from './utils.js';

export function createLine(ent) {
    const color = parseColor(ent, '#44ff44');
    const opacity = styleParam(ent, 'opacity', 0.8);
    const thickness = styleParam(ent, 'thickness', 0.03);
    const length = styleParam(ent, 'length', 20.0);
    const origin = ent.origin || [0, 0, 0];
    const dir = ent.direction || [1, 0, 0];

    const geometry = new THREE.CylinderGeometry(thickness, thickness, length, 8, 1);
    const material = makeMaterial(color, opacity);
    const mesh = new THREE.Mesh(geometry, material);

    mesh.setRotationFromQuaternion(rotationFromDirection(dir[0], dir[1], dir[2]));

    const d = new THREE.Vector3(dir[0], dir[1], dir[2]).normalize();
    mesh.position.set(
        origin[0] + d.x * length / 2,
        origin[1] + d.y * length / 2,
        origin[2] + d.z * length / 2
    );

    // Wireframe overlay
    const wireframe = styleParam(ent, 'wireframe', false);
    if (wireframe) {
        const wfColor = styleParam(ent, 'wireframe_color', null) || color;
        const wfOpacity = styleParam(ent, 'wireframe_opacity', 1.0);
        const dash = styleParam(ent, 'wireframe_dash', null);
        addWireframeOverlay(
            mesh,
            new THREE.CylinderGeometry(thickness, thickness, length, 8, 1),
            wfColor,
            dash,
            wfOpacity
        );
    }

    tagEntity(mesh, ent);
    return mesh;
}