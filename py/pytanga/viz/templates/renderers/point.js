// Point / HPoint renderer — renders as a small sphere.
// Phase 5: Per-entity module, reads from ent.style.* via styleParam().

import * as THREE from 'three';
import { makeMaterial, styleParam, parseColor, tagEntity } from './utils.js';

export function createPoint(ent) {
    const color = parseColor(ent, '#ff4444');
    const opacity = styleParam(ent, 'opacity', 1.0);
    const size = styleParam(ent, 'size', 0.08);
    const pos = ent.position || [0, 0, 0];

    const geometry = new THREE.SphereGeometry(size, 16, 16);
    const material = makeMaterial(color, opacity);
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(pos[0], pos[1], pos[2]);
    tagEntity(mesh, ent);
    return mesh;
}