// Grid renderer — a coordinate grid in a UV plane.
// Draws lines parallel to dir_u and dir_v across the given ranges.
// range_u / range_v are [min, max] pairs relative to `origin`.

import * as THREE from 'three';
import {
    applyStyleUpdate,
    clearGroupChildren,
    makeLineMaterial,
    makeFatLineWithMaterial,
    parseColor,
    styleParam,
    tagEntity,
} from './utils.js';
import { styleNeedsRebuild } from './style-diff.js';

function _gridMaterial(ent) {
    const color = parseColor(ent, '#555555');
    const opacity = styleParam(ent, 'opacity', 0.5);
    const lineWidth = styleParam(ent, 'line_thickness', 1);
    return makeLineMaterial(color, opacity, lineWidth);
}

/**
 * Return the ordered `[a, b]` segment endpoint pairs for a grid, in the order
 * `createGrid` draws them (lines parallel to dir_u first, then dir_v).
 */
function _gridSegments(ent) {
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

    // Corner of the grid rectangle in UV space.
    const corner = origin.clone()
        .addScaledVector(dirU, minU)
        .addScaledVector(dirV, minV);

    const segments = [];

    // Lines parallel to dir_u (positioned along dir_v).
    if (Array.isArray(ent.line_positions_v)) {
        for (const vp of ent.line_positions_v) {
            const a = origin.clone()
                .addScaledVector(dirU, minU)
                .addScaledVector(dirV, vp);
            segments.push([a, a.clone().addScaledVector(dirU, extentU)]);
        }
    } else {
        const vSteps = Math.floor(extentV / intervalV);
        for (let i = 0; i <= vSteps; i++) {
            const t = i * intervalV;
            const a = corner.clone().addScaledVector(dirV, t);
            segments.push([a, a.clone().addScaledVector(dirU, extentU)]);
        }
    }

    // Lines parallel to dir_v (positioned along dir_u).
    if (Array.isArray(ent.line_positions_u)) {
        for (const up of ent.line_positions_u) {
            const a = origin.clone()
                .addScaledVector(dirU, up)
                .addScaledVector(dirV, minV);
            segments.push([a, a.clone().addScaledVector(dirV, extentV)]);
        }
    } else {
        const uSteps = Math.floor(extentU / intervalU);
        for (let i = 0; i <= uSteps; i++) {
            const t = i * intervalU;
            const a = corner.clone().addScaledVector(dirU, t);
            segments.push([a, a.clone().addScaledVector(dirV, extentV)]);
        }
    }

    return segments;
}

export function createGrid(ent) {
    const group = new THREE.Group();
    const material = _gridMaterial(ent);
    for (const [a, b] of _gridSegments(ent)) {
        group.add(makeFatLineWithMaterial([a, b], material));
    }
    tagEntity(group, ent);
    return group;
}

/**
 * Update a grid in place.
 *
 * When the segment count is unchanged, each line's positions are rewritten and
 * the shared material is reused; otherwise the group is refilled with the
 * (kept) shared material.  A change to a non-cheap style field (e.g. dash
 * patterns) is not applied in place and returns ``false`` to rebuild.
 */
export function updateGrid(mesh, ent, prev) {
    if (!prev) return false;
    if (styleNeedsRebuild(ent, prev)) return false;
    const segs = _gridSegments(ent);
    const lines = mesh.children.filter(
        (c) => c.geometry && typeof c.geometry.setPositions === 'function'
    );
    if (lines.length === segs.length && lines.length === mesh.children.length) {
        // Same segment count → rewrite each line's positions, reuse material.
        for (let i = 0; i < segs.length; i++) {
            const [a, b] = segs[i];
            lines[i].geometry.setPositions([a.x, a.y, a.z, b.x, b.y, b.z]);
            lines[i].geometry.computeBoundingSphere();
        }
    } else {
        const material = lines.length ? lines[0].material : _gridMaterial(ent);
        clearGroupChildren(mesh, { disposeMaterials: false });
        for (const [a, b] of segs) {
            mesh.add(makeFatLineWithMaterial([a, b], material));
        }
    }
    applyStyleUpdate(mesh, ent);
    return true;
}