// Ellipse renderer — a flat, filled ellipse oriented along `normal`.
// Phase 4: Per-entity module.

import * as THREE from 'three';
import {
    makeMaterial,
    rotationFromNormal,
    styleParam,
    parseColor,
    tagEntity,
    addWireframeOverlay,
} from './utils.js';

export function createEllipse(ent) {
    const color = parseColor(ent, '#ff44ff');
    const opacity = styleParam(ent, 'opacity', 0.9);
    const center = ent.center || [0, 0, 0];
    const radiusU = Math.max(ent.radiusU || 1.0, 0.001);
    const radiusV = Math.max(ent.radiusV || 0.5, 0.001);
    const normal = ent.normal || [0, 0, 1];

    const geometry = new THREE.CircleGeometry(1, 64);
    const mesh = new THREE.Mesh(geometry, makeMaterial(color, opacity, true));
    mesh.position.set(center[0], center[1], center[2]);
    mesh.scale.set(radiusU, radiusV, 1);
    mesh.setRotationFromQuaternion(rotationFromNormal(normal[0], normal[1], normal[2]));

    const wireframe = styleParam(ent, 'wireframe', false);
    if (wireframe) {
        const wfColor = styleParam(ent, 'wireframe_color', null) || color;
        const wfOpacity = styleParam(ent, 'wireframe_opacity', 1.0);
        const dash = styleParam(ent, 'wireframe_dash', null);
        const wfGeo = new THREE.CircleGeometry(1.005, 64);
        wfGeo.scale(radiusU, radiusV, 1);
        addWireframeOverlay(mesh, wfGeo, wfColor, dash, wfOpacity);
    }

    tagEntity(mesh, ent);
    return mesh;
}
