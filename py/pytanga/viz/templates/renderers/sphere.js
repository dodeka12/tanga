// Sphere renderer — rendered as a sphere with optional wireframe overlay.
// Phase 5: Per-entity module.

import * as THREE from 'three';
import {
    makeMaterial,
    styleParam,
    parseColor,
    tagEntity,
    addWireframeOverlay,
} from './utils.js';

export function createSphere(ent) {
    const color = parseColor(ent, '#ffaa00');
    const opacity = styleParam(ent, 'opacity', 0.4);
    const center = ent.center || [0, 0, 0];
    const radius = Math.max(ent.radius || 1.0, 0.001);

    const geometry = new THREE.SphereGeometry(radius, 32, 32);
    const material = makeMaterial(color, opacity);
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(center[0], center[1], center[2]);

    // Wireframe overlay
    const wireframe = styleParam(ent, 'wireframe', false);
    if (wireframe) {
        const wfColor = styleParam(ent, 'wireframe_color', null) || color;
        const wfOpacity = styleParam(ent, 'wireframe_opacity', 1.0);
        const dash = styleParam(ent, 'wireframe_dash', null);
        addWireframeOverlay(
            mesh,
            new THREE.SphereGeometry(radius * 1.005, 24, 24),
            wfColor,
            dash,
            wfOpacity
        );
    }

    tagEntity(mesh, ent);
    return mesh;
}