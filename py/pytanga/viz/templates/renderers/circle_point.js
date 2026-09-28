// CirclePointStyle renderer — a flat circle marker (filled disc or outline
// ring) instead of a sphere.

import * as THREE from 'three';
import { makeMaterial, styleParam, parseColor, tagEntity } from './utils.js';

const CIRCLE_POINT_SEGMENTS = 64;

export function createCirclePoint(ent) {
    const color = parseColor(ent, '#ffffff');
    const opacity = styleParam(ent, 'opacity', 1.0);
    const size = styleParam(ent, 'size', 0.08); // circle radius (world units)
    const thickness = styleParam(ent, 'thickness', Math.max(size * 0.2, 0.001));
    const filled = styleParam(ent, 'filled', true);
    const pos = ent.position || [0, 0, 0];

    let mesh;
    if (filled) {
        // Filled disc; its opacity is `fill_opacity` (defaulting to `opacity`).
        const fillOpacity = styleParam(ent, 'fill_opacity', opacity);
        mesh = new THREE.Mesh(
            new THREE.CircleGeometry(size, CIRCLE_POINT_SEGMENTS),
            makeMaterial(color, fillOpacity, true)
        );
        mesh.userData.isFillQuad = true;
    } else {
        // Outline ring: a flat annulus whose radial width is `thickness`.
        const inner = Math.max(size - thickness, 0.0005);
        mesh = new THREE.Mesh(
            new THREE.RingGeometry(inner, size, CIRCLE_POINT_SEGMENTS),
            makeMaterial(color, opacity, true)
        );
    }

    mesh.position.set(pos[0], pos[1], pos[2]);
    tagEntity(mesh, ent);
    return mesh;
}
