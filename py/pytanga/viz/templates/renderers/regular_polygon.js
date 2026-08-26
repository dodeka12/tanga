// RegularPolygon renderer — a flat, regular n-gon prism oriented along `normal`.
// Phase 4: Per-entity module.

import * as THREE from 'three';
import {
    makeMaterial,
    rotationFromDirection,
    styleParam,
    parseColor,
    tagEntity,
    addWireframeOverlay,
} from './utils.js';

export function createRegularPolygon(ent) {
    const color = parseColor(ent, '#44ffaa');
    const opacity = styleParam(ent, 'opacity', 0.9);
    const center = ent.center || [0, 0, 0];
    const radius = Math.max(ent.radius || 1.0, 0.001);
    const sides = Math.max(Math.floor(ent.sides || 6), 3);
    const thickness = Math.max(styleParam(ent, 'thickness', 0.02), 0.001);
    const normal = ent.normal || [0, 0, 1];
    const angle = ent.angle || 0.0;

    // CylinderGeometry with `radialSegments = sides` yields a regular n-gon.
    const geometry = new THREE.CylinderGeometry(radius, radius, thickness, sides, 1);
    const mesh = new THREE.Mesh(geometry, makeMaterial(color, opacity));
    mesh.position.set(center[0], center[1], center[2]);
    mesh.setRotationFromQuaternion(
        rotationFromDirection(normal[0], normal[1], normal[2])
    );
    if (angle) {
        mesh.rotateY(angle);
    }

    const wireframe = styleParam(ent, 'wireframe', false);
    if (wireframe) {
        const wfColor = styleParam(ent, 'wireframe_color', null) || color;
        const wfOpacity = styleParam(ent, 'wireframe_opacity', 1.0);
        const dash = styleParam(ent, 'wireframe_dash', null);
        addWireframeOverlay(
            mesh,
            new THREE.CylinderGeometry(radius * 1.005, radius * 1.005, thickness, sides, 1),
            wfColor,
            dash,
            wfOpacity
        );
    }

    tagEntity(mesh, ent);
    return mesh;
}
