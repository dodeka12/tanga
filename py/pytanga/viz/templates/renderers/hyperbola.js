// Hyperbola renderer — samples both branches as a fat-line curve, in the
// canonical XY plane (transverse dir1 → +X, conjugate dir2 → +Y).
import * as THREE from 'three';
import { makeFatLine, styleParam, parseColor, tagEntity, applyStyleUpdate, contentChanged } from './utils.js';
import { styleNeedsRebuild } from './style-diff.js';

export function createHyperbola(ent) {
    const color = parseColor(ent, '#ff44ff');
    const opacity = styleParam(ent, 'opacity', 0.9);
    const thickness = styleParam(ent, 'thickness', 1.0);
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
                new THREE.Vector3(sign * a * Math.cosh(t), b * Math.sinh(t), 0),
            );
        }
        group.add(makeFatLine(points, color, opacity, thickness));
    }

    tagEntity(group, ent);
    return group;
}

export function updateHyperbola(mesh, ent, prev) {
    if (contentChanged(ent, prev, ['a', 'b'])) return false;
    if (styleNeedsRebuild(ent, prev)) return false;
    applyStyleUpdate(mesh, ent);
    return true;
}
