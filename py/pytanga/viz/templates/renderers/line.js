// Line renderer — draws a canonical straight segment along +Y from the origin
// to `+Y * length`.  Placement (origin + direction) rides on the node transform.
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
    styleParam,
    parseColor,
    tagEntity,
    applyStyleUpdate,
    approxEqual,
} from './utils.js';
import { styleNeedsRebuild } from './style-diff.js';

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

    const start = new THREE.Vector3(0, 0, 0);
    const end = new THREE.Vector3(0, length, 0);

    if (isCylinderStyle(ent)) {
        const thickness = styleParam(ent, 'thickness', 0.03);
        const geometry = new THREE.CylinderGeometry(thickness, thickness, length, 8, 1);
        const mesh = new THREE.Mesh(geometry, makeMaterial(color, opacity));
        mesh.position.set(0, length / 2, 0);
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
    if (styleNeedsRebuild(ent, prev)) return false;

    const length = resolveLineLength(ent);
    // A length change alters the segment geometry; cheaper to rebuild.
    if (prev && !approxEqual(length, resolveLineLength(prev))) return false;

    if (isCylinderStyle(ent)) {
        mesh.position.set(0, length / 2, 0);
    } else {
        mesh.geometry.setPositions([0, 0, 0, 0, length, 0]);
        const thickness = styleParam(ent, 'thickness', 1.0);
        if (mesh.material && mesh.material.linewidth !== undefined) {
            mesh.material.linewidth = Math.max(0.1, thickness);
        }
    }
    applyStyleUpdate(mesh, ent);
    return true;
}
