// Circle renderer — rendered as a torus with optional wireframe overlay.
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

export function createCircle(ent) {
    const color = parseColor(ent, '#ff44ff');
    const opacity = styleParam(ent, 'opacity', 0.7);
    const center = ent.center || [0, 0, 0];
    const radius = Math.max(ent.radius || 1.0, 0.001);
    const tubeRadius = styleParam(ent, 'tubeRadius', 0.03);
    const wireframe = styleParam(ent, 'wireframe', false);

    const wireframeOnly = wireframe && opacity === 0;

    const geometry = new THREE.TorusGeometry(radius, tubeRadius, 16, 64);
    const mesh = wireframeOnly
        ? new THREE.Group()
        : new THREE.Mesh(geometry, makeMaterial(color, opacity));

    mesh.position.set(center[0], center[1], center[2]);

    if (ent.normal) {
        mesh.setRotationFromQuaternion(
            rotationFromNormal(ent.normal[0], ent.normal[1], ent.normal[2])
        );
    }

    // Wireframe overlay
    if (wireframe) {
        const wfColor = styleParam(ent, 'wireframe_color', null) || color;
        const wfOpacity = styleParam(ent, 'wireframe_opacity', 1.0);
        const dash = styleParam(ent, 'wireframe_dash', null);
        addWireframeOverlay(
            mesh,
            new THREE.TorusGeometry(radius * 1.005, tubeRadius, 16, 64),
            wfColor,
            dash,
            wfOpacity
        );
    }

    tagEntity(mesh, ent);
    return mesh;
}