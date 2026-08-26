// Box renderer — a solid box, optionally rotated via an Euler triple.
// Phase 4: Per-entity module.

import * as THREE from 'three';
import {
    makeMaterial,
    styleParam,
    parseColor,
    tagEntity,
    addWireframeOverlay,
} from './utils.js';

export function createBox(ent) {
    const color = parseColor(ent, '#88ccff');
    const opacity = styleParam(ent, 'opacity', 0.9);
    const center = ent.center || [0, 0, 0];
    const size = ent.size || [1, 1, 1];

    const geometry = new THREE.BoxGeometry(size[0], size[1], size[2]);
    const mesh = new THREE.Mesh(geometry, makeMaterial(color, opacity));
    mesh.position.set(center[0], center[1], center[2]);
    if (ent.rotation) {
        mesh.rotation.set(ent.rotation[0], ent.rotation[1], ent.rotation[2]);
    }

    const wireframe = styleParam(ent, 'wireframe', false);
    if (wireframe) {
        const wfColor = styleParam(ent, 'wireframe_color', null) || color;
        const wfOpacity = styleParam(ent, 'wireframe_opacity', 1.0);
        const dash = styleParam(ent, 'wireframe_dash', null);
        addWireframeOverlay(
            mesh,
            new THREE.BoxGeometry(size[0] * 1.005, size[1] * 1.005, size[2] * 1.005),
            wfColor,
            dash,
            wfOpacity
        );
    }

    tagEntity(mesh, ent);
    return mesh;
}
