// Grid renderer — a coordinate grid in a UV plane.
// Draws lines parallel to dir_u and dir_v across the given ranges.

import * as THREE from 'three';
import { parseColor, styleParam, tagEntity } from './utils.js';

export function createGrid(ent) {
    const group = new THREE.Group();

    const origin = new THREE.Vector3(...(ent.origin || [0, 0, 0]));
    const dirU = new THREE.Vector3(...(ent.dir_u || [1, 0, 0])).normalize();
    const dirV = new THREE.Vector3(...(ent.dir_v || [0, 1, 0])).normalize();

    const rangeU = Math.abs(ent.range_u ?? 5.0);
    const rangeV = Math.abs(ent.range_v ?? 5.0);
    const intervalU = Math.abs(ent.interval_u ?? 1.0);
    const intervalV = Math.abs(ent.interval_v ?? 1.0);

    const color = parseColor(ent, '#555555');
    const opacity = styleParam(ent, 'opacity', 0.5);
    const material = new THREE.LineBasicMaterial({
        color: typeof color === 'string' ? new THREE.Color(color) : color,
        opacity,
        transparent: opacity < 1.0,
    });

    const halfU = rangeU / 2;
    const halfV = rangeV / 2;
    // Bottom-left corner of the grid rectangle in UV space.
    const corner = origin.clone()
        .addScaledVector(dirU, -halfU)
        .addScaledVector(dirV, -halfV);

    function addLine(a, b) {
        const geo = new THREE.BufferGeometry().setFromPoints([a, b]);
        const line = new THREE.Line(geo, material);
        line.renderOrder = 1;
        group.add(line);
    }

    // Lines parallel to dir_u (step along dir_v)
    const vSteps = Math.floor(rangeV / intervalV);
    for (let i = 0; i <= vSteps; i++) {
        const t = i * intervalV;
        const a = corner.clone().addScaledVector(dirV, t);
        const b = a.clone().addScaledVector(dirU, rangeU);
        addLine(a, b);
    }

    // Lines parallel to dir_v (step along dir_u)
    const uSteps = Math.floor(rangeU / intervalU);
    for (let i = 0; i <= uSteps; i++) {
        const t = i * intervalU;
        const a = corner.clone().addScaledVector(dirU, t);
        const b = a.clone().addScaledVector(dirV, rangeV);
        addLine(a, b);
    }

    tagEntity(group, ent);
    return group;
}