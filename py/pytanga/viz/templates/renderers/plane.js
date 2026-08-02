// Plane renderer — rendered as a double-sided translucent quad
// with optional wireframe overlay.
// Phase 5: Per-entity module.

import * as THREE from 'three';
import {
    makeMaterial,
    rotationFromNormal,
    styleParam,
    parseColor,
    tagEntity,
    addWireframeOverlay,
} from './utils.js';

export function createPlane(ent) {
    const color = parseColor(ent, '#4488ff');
    const opacity = styleParam(ent, 'opacity', 0.3);
    const extent = styleParam(ent, 'extent', 10.0);
    const point = ent.point || [0, 0, 0];
    const normal = ent.normal || [0, 0, 1];

    const geometry = new THREE.PlaneGeometry(extent * 2, extent * 2);
    const material = makeMaterial(color, opacity, true);
    const mesh = new THREE.Mesh(geometry, material);

    mesh.position.set(point[0], point[1], point[2]);
    mesh.setRotationFromQuaternion(rotationFromNormal(normal[0], normal[1], normal[2]));

    // Wireframe overlay
    const wireframe = styleParam(ent, 'wireframe', false);
    if (wireframe) {
        const wfColor = styleParam(ent, 'wireframe_color', null) || color;
        const wfOpacity = styleParam(ent, 'wireframe_opacity', 1.0);
        const dash = styleParam(ent, 'wireframe_dash', null);
        addWireframeOverlay(
            mesh,
            new THREE.PlaneGeometry(extent * 2, extent * 2),
            wfColor,
            dash,
            wfOpacity
        );
    }

    tagEntity(mesh, ent);
    return mesh;
}