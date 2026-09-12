// Parabola renderer — samples the curve as a fat-line polyline.
import * as THREE from 'three';
import { makeFatLine, styleParam, parseColor, tagEntity, applyStyleUpdate, contentChanged } from './utils.js';

export function createParabola(ent) {
    const color = parseColor(ent, '#ff44ff');
    const opacity = styleParam(ent, 'opacity', 0.9);
    const thickness = styleParam(ent, 'thickness', 1.0);
    const vertex = ent.vertex || [0, 0, 0];
    const dir = new THREE.Vector3(...(ent.direction || [1, 0, 0])).normalize();
    const p = Math.max(ent.p || 1.0, 0.001);
    // 2D transverse direction (the parabola lies in the xy-plane).
    const dPerp = new THREE.Vector3(-dir.y, dir.x, 0).normalize();
    // `extent` is a spatial half-size; bound the parameter so the curve stays
    // within the extent box along both the axis and the transverse direction.
    const extent = Math.max(styleParam(ent, 'extent', 5.0), 0.001);
    const tMax = Math.min(extent, Math.sqrt(2 * p * extent));
    const segments = 128;

    const points = [];
    for (let i = 0; i <= segments; i++) {
        const t = -tMax + (2 * tMax * i) / segments;
        const s = (t * t) / (2 * p);
        points.push(
            new THREE.Vector3(vertex[0], vertex[1], vertex[2])
                .addScaledVector(dir, s)
                .addScaledVector(dPerp, t),
        );
    }

    const line = makeFatLine(points, color, opacity, thickness);
    tagEntity(line, ent);
    return line;
}

export function updateParabola(mesh, ent, prev) {
    if (contentChanged(ent, prev, ['vertex', 'direction', 'p'])) return false;
    applyStyleUpdate(mesh, ent);
    return true;
}
