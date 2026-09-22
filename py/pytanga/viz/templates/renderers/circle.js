// Circle renderer — a torus (tube) by default, or a thick screen-space line
// when styled with `CircleStyle`. Phase 5: Per-entity module.

import * as THREE from 'three';
import {
    makeMaterial,
    makeFatLine,
    styleParam,
    parseColor,
    tagEntity,
    addWireframeOverlay,
    applyStyleUpdate,
    contentChanged,
} from './utils.js';
import { styleNeedsRebuild } from './style-diff.js';

const CIRCLE_SEGMENTS = 96;

function isLineStyle(ent) {
    return !!(ent.style && ent.style.style_type === 'CircleStyle');
}

function createLineCircle(ent) {
    const color = parseColor(ent, '#ff44ff');
    const opacity = styleParam(ent, 'opacity', 0.9);
    const thickness = styleParam(ent, 'thickness', 1.0);
    const radius = Math.max(ent.radius || 1.0, 0.001);

    // Canonical: a circle in the XY plane centered at the origin.
    const points = [];
    for (let i = 0; i <= CIRCLE_SEGMENTS; i++) {
        const t = (2 * Math.PI * i) / CIRCLE_SEGMENTS;
        points.push(new THREE.Vector3(radius * Math.cos(t), radius * Math.sin(t), 0));
    }

    const line = makeFatLine(points, color, opacity, thickness);
    tagEntity(line, ent);
    return line;
}


export function createCircle(ent) {
    if (isLineStyle(ent)) {
        return createLineCircle(ent);
    }

    const color = parseColor(ent, '#ff44ff');
    const opacity = styleParam(ent, 'opacity', 0.7);
    const radius = Math.max(ent.radius || 1.0, 0.001);
    const tubeRadius = styleParam(ent, 'tubeRadius', 0.03);
    const wireframe = styleParam(ent, 'wireframe', false);

    const wireframeOnly = wireframe && opacity === 0;

    // Canonical: a torus (circle) in the XY plane (normal +Z) at the origin.
    const geometry = new THREE.TorusGeometry(radius, tubeRadius, 16, 64);
    const mesh = wireframeOnly
        ? new THREE.Group()
        : new THREE.Mesh(geometry, makeMaterial(color, opacity));

    // Wireframe overlay
    if (wireframe) {
        const wfColor = styleParam(ent, 'wireframe_color', null) || color;
        const wfOpacity = styleParam(ent, 'wireframe_opacity', 1.0);
        const dash = styleParam(ent, 'wireframe_dash', null);
        addWireframeOverlay(
            mesh,
            new THREE.TorusGeometry(radius * 1.005, tubeRadius, 16, 64),
            wfColor,
            dash,
            wfOpacity
        );
    }

    tagEntity(mesh, ent);
    return mesh;
}

export function updateCircle(mesh, ent, prev) {
    if (contentChanged(ent, prev, ['radius', 'tubeRadius'])) return false;
    if (styleNeedsRebuild(ent, prev)) return false;
    // Switching between the tube and thick-line style requires a rebuild.
    const curLine = isLineStyle(ent);
    const prevLine = prev ? isLineStyle(prev) : false;
    if (curLine !== prevLine) return false;
    applyStyleUpdate(mesh, ent);
    return true;
}