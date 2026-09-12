// Hyperbola renderer — samples both branches as a fat-line curve.
import * as THREE from 'three';
import { makeFatLine, styleParam, parseColor, tagEntity, applyStyleUpdate, contentChanged } from './utils.js';

export function createHyperbola(ent) {
    const color = parseColor(ent, '#ff44ff');
    const opacity = styleParam(ent, 'opacity', 0.9);
    const thickness = styleParam(ent, 'thickness', 1.0);
    const center = ent.center || [0, 0, 0];
    const d1 = new THREE.Vector3(...(ent.dir1 || [1, 0, 0])).normalize();
    const d2 = new THREE.Vector3(...(ent.dir2 || [0, 1, 0])).normalize();
    const a = Math.max(ent.a || 1.0, 0.001);
    const b = Math.max(ent.b || 1.0, 0.001);
    // `extent` is a spatial half-size; stop sampling once a branch leaves it.
    const extent = Math.max(styleParam(ent, 'extent', 5.0), 0.001);
    const segments = 128;

    // Bound the parameter so both branches stay within the extent box.
    // acosh needs its argument >= 1; asinh needs it >= 0.
    const tMax = Math.min(
        Math.acosh(Math.max(1.0, extent / a)),
        Math.asinh(Math.max(0.0, extent / b)),
    );

    const group = new THREE.Group();
    for (const sign of [1, -1]) {
        const points = [];
        for (let i = 0; i <= segments; i++) {
            const t = -tMax + (2 * tMax * i) / segments;
            points.push(
                new THREE.Vector3(center[0], center[1], center[2])
                    .addScaledVector(d1, sign * a * Math.cosh(t))
                    .addScaledVector(d2, b * Math.sinh(t)),
            );
        }
        group.add(makeFatLine(points, color, opacity, thickness));
    }

    tagEntity(group, ent);
    return group;
}

export function updateHyperbola(mesh, ent, prev) {
    if (contentChanged(ent, prev, ['a', 'b', 'dir1', 'dir2', 'center'])) return false;
    applyStyleUpdate(mesh, ent);
    return true;
}
