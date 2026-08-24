// Line renderer — draws a straight segment from `origin` to
// `origin + normalize(direction) * length`.
//
// `length` is a content field: `0` means "infinite line → use the style's
// default length".  Rendering dispatches on the style type:
//   - `LineStyle` (default) → three.js `Line2` fat line; `thickness` is a
//     screen-space pixel width.
//   - `CylinderLineStyle`   → solid `CylinderGeometry`; `thickness` is the
//     cylinder radius in world units.
// Phase 5: Per-entity module.

import * as THREE from 'three';
import {
    makeFatLine,
    makeMaterial,
    rotationFromDirection,
    styleParam,
    parseColor,
    tagEntity,
    applyStyleUpdate,
    approxEqual,
} from './utils.js';

function isCylinderStyle(ent) {
    return !!(ent.style && ent.style.style_type === 'CylinderLineStyle');
}

function resolveLineLength(ent) {
    // `0` is the "infinite line" sentinel → fall back to the style default.
    return ent.length ? ent.length : styleParam(ent, 'length', 20.0);
}

export function createLine(ent) {
    const color = parseColor(ent, '#44ff44');
    const opacity = styleParam(ent, 'opacity', 0.8);
    const length = resolveLineLength(ent);
    const origin = ent.origin || [0, 0, 0];
    const dir = ent.direction || [1, 0, 0];

    const d = new THREE.Vector3(dir[0], dir[1], dir[2]).normalize();
    const start = new THREE.Vector3(origin[0], origin[1], origin[2]);
    const end = start.clone().addScaledVector(d, length);

    if (isCylinderStyle(ent)) {
        const thickness = styleParam(ent, 'thickness', 0.03);
        const geometry = new THREE.CylinderGeometry(thickness, thickness, length, 8, 1);
        const mesh = new THREE.Mesh(geometry, makeMaterial(color, opacity));
        mesh.setRotationFromQuaternion(rotationFromDirection(d.x, d.y, d.z));
        mesh.position.set(
            origin[0] + d.x * length / 2,
            origin[1] + d.y * length / 2,
            origin[2] + d.z * length / 2
        );
        tagEntity(mesh, ent);
        return mesh;
    }

    const thickness = styleParam(ent, 'thickness', 1.0);
    const line = makeFatLine([start, end], color, opacity, thickness);
    tagEntity(line, ent);
    return line;
}

export function updateLine(mesh, ent, prev) {
    // Switching between fat-line and cylinder rendering requires a rebuild.
    if (prev && isCylinderStyle(ent) !== isCylinderStyle(prev)) return false;

    const length = resolveLineLength(ent);
    // A length change alters the segment geometry; cheaper to rebuild.
    if (prev && !approxEqual(length, resolveLineLength(prev))) return false;

    const origin = ent.origin || prev?.origin || [0, 0, 0];
    const dir = ent.direction || prev?.direction || [1, 0, 0];
    const d = new THREE.Vector3(dir[0], dir[1], dir[2]).normalize();

    if (isCylinderStyle(ent)) {
        mesh.setRotationFromQuaternion(rotationFromDirection(d.x, d.y, d.z));
        mesh.position.set(
            origin[0] + d.x * length / 2,
            origin[1] + d.y * length / 2,
            origin[2] + d.z * length / 2
        );
    } else {
        const start = new THREE.Vector3(origin[0], origin[1], origin[2]);
        const end = start.clone().addScaledVector(d, length);
        mesh.geometry.setPositions([start.x, start.y, start.z, end.x, end.y, end.z]);
        const thickness = styleParam(ent, 'thickness', 1.0);
        if (mesh.material && mesh.material.linewidth !== undefined) {
            mesh.material.linewidth = Math.max(0.1, thickness);
        }
    }
    applyStyleUpdate(mesh, ent);
    return true;
}
