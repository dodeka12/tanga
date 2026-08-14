// Grid renderer — a coordinate grid in a UV plane.
// Draws lines parallel to dir_u and dir_v across the given ranges.
// range_u / range_v are [min, max] pairs relative to `origin`.

import * as THREE from 'three';
import {
    makeLineMaterial,
    makeFatLineWithMaterial,
    parseColor,
    styleParam,
    tagEntity,
} from './utils.js';

export function createGrid(ent) {
    const group = new THREE.Group();

    const origin = new THREE.Vector3(...(ent.origin || [0, 0, 0]));
    const dirU = new THREE.Vector3(...(ent.dir_u || [1, 0, 0])).normalize();
    const dirV = new THREE.Vector3(...(ent.dir_v || [0, 1, 0])).normalize();

    const rangeU = ent.range_u || [0, 5];
    const rangeV = ent.range_v || [0, 5];
    const minU = Math.min(rangeU[0], rangeU[1]);
    const maxU = Math.max(rangeU[0], rangeU[1]);
    const minV = Math.min(rangeV[0], rangeV[1]);
    const maxV = Math.max(rangeV[0], rangeV[1]);
    const extentU = maxU - minU;
    const extentV = maxV - minV;

    const intervalU = Math.abs(ent.interval_u ?? 1.0);
    const intervalV = Math.abs(ent.interval_v ?? 1.0);

    const color = parseColor(ent, '#555555');
    const opacity = styleParam(ent, 'opacity', 0.5);
    const lineWidth = styleParam(ent, 'line_thickness', 1);
    const material = makeLineMaterial(color, opacity, lineWidth);

    // Corner of the grid rectangle in UV space.
    const corner = origin.clone()
        .addScaledVector(dirU, minU)
        .addScaledVector(dirV, minV);

    function addLine(a, b) {
        const line = makeFatLineWithMaterial([a, b], material);
        group.add(line);
    }

    // Lines parallel to dir_u (step along dir_v)
    const vSteps = Math.floor(extentV / intervalV);
    for (let i = 0; i <= vSteps; i++) {
        const t = i * intervalV;
        const a = corner.clone().addScaledVector(dirV, t);
        const b = a.clone().addScaledVector(dirU, extentU);
        addLine(a, b);
    }

    // Lines parallel to dir_v (step along dir_u)
    const uSteps = Math.floor(extentU / intervalU);
    for (let i = 0; i <= uSteps; i++) {
        const t = i * intervalU;
        const a = corner.clone().addScaledVector(dirU, t);
        const b = a.clone().addScaledVector(dirV, extentV);
        addLine(a, b);
    }

    tagEntity(group, ent);
    return group;
}