// Inversion renderer — wireframe sphere at the inversion center.
// Phase 6: Moved from inline factory.js to dedicated operator module.

import * as THREE from 'three';
import { styleParam,  parseColor } from '../utils.js';


export function createInversion(ent) {
    const color = parseColor(ent, '#cc88ff');
    const opacity = styleParam(ent, 'opacity', 0.4);
    const o = ent.center || [0, 0, 0];
    const r = ent.radius || 2.0;
    const col = new THREE.Color(color);
    const mesh = new THREE.Mesh(
        new THREE.SphereGeometry(r, 32, 32),
        new THREE.MeshBasicMaterial({
            color: col,
            wireframe: true,
            opacity,
            transparent: true,
        })
    );
    mesh.position.set(o[0], o[1], o[2]);
    return mesh;
}