// Ellipse renderer — a 2D ellipse drawn as a screen-space fat line.
// Phase 4: Per-entity module.

import * as THREE from 'three';
import {
    makeFatLine,
    rotationFromNormal,
    styleParam,
    parseColor,
    tagEntity,
} from './utils.js';

const ELLIPSE_SEGMENTS = 128;

export function createEllipse(ent) {
    const color = parseColor(ent, '#ff44ff');
    const opacity = styleParam(ent, 'opacity', 0.9);
    const thickness = styleParam(ent, 'thickness', 1.0);
    const center = ent.center || [0, 0, 0];
    const radiusU = Math.max(ent.radiusU || 1.0, 0.001);
    const radiusV = Math.max(ent.radiusV || 0.5, 0.001);
    const normal = ent.normal || [0, 0, 1];

    const q = rotationFromNormal(normal[0], normal[1], normal[2]);
    const ex = new THREE.Vector3(1, 0, 0).applyQuaternion(q);
    const ey = new THREE.Vector3(0, 1, 0).applyQuaternion(q);

    const points = [];
    for (let i = 0; i <= ELLIPSE_SEGMENTS; i++) {
        const t = (2 * Math.PI * i) / ELLIPSE_SEGMENTS;
        points.push(
            new THREE.Vector3(center[0], center[1], center[2])
                .addScaledVector(ex, radiusU * Math.cos(t))
                .addScaledVector(ey, radiusV * Math.sin(t)),
        );
    }

    const line = makeFatLine(points, color, opacity, thickness);
    tagEntity(line, ent);
    return line;
}
