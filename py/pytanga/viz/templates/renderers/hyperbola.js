// Hyperbola renderer — samples both branches as a fat-line curve.
import * as THREE from 'three';
import { makeFatLine, styleParam, parseColor, tagEntity } from './utils.js';

export function createHyperbola(ent) {
    const color = parseColor(ent, '#ff44ff');
    const opacity = styleParam(ent, 'opacity', 0.9);
    const thickness = styleParam(ent, 'thickness', 1.0);
    const center = ent.center || [0, 0, 0];
    const d1 = new THREE.Vector3(...(ent.dir1 || [1, 0, 0])).normalize();
    const d2 = new THREE.Vector3(...(ent.dir2 || [0, 1, 0])).normalize();
    const a = Math.max(ent.a || 1.0, 0.001);
    const b = Math.max(ent.b || 1.0, 0.001);
    const range = styleParam(ent, 'extent', 2.0);
    const segments = 128;

    const points = [];
    for (let i = 0; i <= segments; i++) {
        const t = -range + (2 * range * i) / segments;
        const x = a * Math.cosh(t);
        const y = b * Math.sinh(t);
        points.push(
            new THREE.Vector3(center[0], center[1], center[2])
                .addScaledVector(d1, x)
                .addScaledVector(d2, y),
        );
    }

    const line = makeFatLine(points, color, opacity, thickness);
    tagEntity(line, ent);
    return line;
}
