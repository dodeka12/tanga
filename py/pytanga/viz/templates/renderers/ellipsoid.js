// Ellipsoid renderer — a unit sphere scaled by per-axis radii.
// Phase 4: Per-entity module.

import * as THREE from 'three';
import {
    makeMaterial,
    styleParam,
    parseColor,
    tagEntity,
    addWireframeOverlay,
} from './utils.js';

export function createEllipsoid(ent) {
    const color = parseColor(ent, '#ffaa00');
    const opacity = styleParam(ent, 'opacity', 0.9);
    const radii = ent.radii || [1, 1, 1];

    // Canonical: a unit sphere scaled by per-axis radii at the origin;
    // placement (center + rotation quaternion) rides on the node transform.
    const geometry = new THREE.SphereGeometry(1, 32, 32);
    const mesh = new THREE.Mesh(geometry, makeMaterial(color, opacity));
    mesh.scale.set(radii[0], radii[1], radii[2]);

    const wireframe = styleParam(ent, 'wireframe', false);
    if (wireframe) {
        const wfColor = styleParam(ent, 'wireframe_color', null) || color;
        const wfOpacity = styleParam(ent, 'wireframe_opacity', 1.0);
        const dash = styleParam(ent, 'wireframe_dash', null);
        const wfGeo = new THREE.SphereGeometry(1.005, 24, 24);
        wfGeo.scale(radii[0], radii[1], radii[2]);
        addWireframeOverlay(mesh, wfGeo, wfColor, dash, wfOpacity);
    }

    tagEntity(mesh, ent);
    return mesh;
}
