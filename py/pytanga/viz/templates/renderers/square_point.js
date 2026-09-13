// SquarePointStyle renderer — renders a flat square marker instead of a sphere.
// Phase: interactive rectangles (square ActPoint handles).

import * as THREE from 'three';
import { makeMaterial, styleParam, parseColor, tagEntity } from './utils.js';

export function createSquarePoint(ent) {
    const color = parseColor(ent, '#ffffff');
    const opacity = styleParam(ent, 'opacity', 1.0);
    const size = styleParam(ent, 'size', 0.08);
    const thickness = styleParam(ent, 'thickness', Math.max(size * 0.2, 0.001));
    const pos = ent.position || [0, 0, 0];

    // A thin square slab facing +z: a square in the xy-plane (visible in a 2D
    // top-down view and on the xy-plane in 3D), with a small depth so it is
    // pickable from shallow 3D angles.
    const geometry = new THREE.BoxGeometry(size * 2, size * 2, thickness);
    const mesh = new THREE.Mesh(geometry, makeMaterial(color, opacity));
    mesh.position.set(pos[0], pos[1], pos[2]);
    tagEntity(mesh, ent);
    return mesh;
}
