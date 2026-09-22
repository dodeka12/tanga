// Arc renderer — renders an arcing cylinder (partial torus) in the canonical
// XY plane (normal +Z), starting at +X and sweeping `angle` radians.  Placement
// (origin + axis + startDirection) rides on the node transform.  When
// `ent.arrow` is set (and the arc is not a full turn), a cone arrow tip is
// drawn at the arc's end.
// Phase 5: Per-entity module.

import * as THREE from 'three';
import {
    makeMaterial,
    rotationFromDirection,
    styleParam,
    parseColor,
    tagEntity,
    applyStyleUpdate,
    approxEqual,
    addWireframeOverlay,
} from './utils.js';
import { styleNeedsRebuild } from './style-diff.js';

const TWO_PI = 2 * Math.PI;

function resolveArcRadius(ent) {
    return Math.max(ent.radius || 1.0, 0.001);
}

function resolveTubeRadius(ent) {
    return Math.max(ent.tubeRadius || 0.05, 0.001);
}

function resolveAngle(ent) {
    return THREE.MathUtils.clamp(ent.angle ?? TWO_PI, 0, TWO_PI);
}

export function createArc(ent) {
    const color = parseColor(ent, '#ffcc44');
    const opacity = styleParam(ent, 'opacity', 0.9);
    const radius = resolveArcRadius(ent);
    const tubeRadius = resolveTubeRadius(ent);
    const angle = resolveAngle(ent);

    const group = new THREE.Group();
    const torus = new THREE.Mesh(
        new THREE.TorusGeometry(radius, tubeRadius, 16, 64, angle),
        makeMaterial(color, opacity)
    );
    group.add(torus);

    // Wireframe overlay
    const wireframe = styleParam(ent, 'wireframe', false);
    if (wireframe) {
        const wfColor = styleParam(ent, 'wireframe_color', null) || color;
        const wfOpacity = styleParam(ent, 'wireframe_opacity', 1.0);
        const dash = styleParam(ent, 'wireframe_dash', null);
        addWireframeOverlay(
            group,
            new THREE.TorusGeometry(radius * 1.005, tubeRadius, 16, 64, angle),
            wfColor,
            dash,
            wfOpacity
        );
    }

    // Arrow tip (cone) at the arc's end — only for a genuine partial arc.
    const arrow = ent.arrow;
    if (arrow && angle < TWO_PI) {
        // Local torus coordinates: arc starts at +X, sweeps CCW in the XY
        // plane; the end point and forward tangent follow from the angle.
        const endPoint = new THREE.Vector3(
            radius * Math.cos(angle),
            radius * Math.sin(angle),
            0
        );
        const tangent = new THREE.Vector3(-Math.sin(angle), Math.cos(angle), 0);
        const cone = new THREE.Mesh(
            new THREE.ConeGeometry(arrow.radius, arrow.length, 16, 1),
            makeMaterial(color, opacity)
        );
        cone.setRotationFromQuaternion(rotationFromDirection(tangent.x, tangent.y, tangent.z));
        cone.position.copy(endPoint).addScaledVector(tangent, arrow.length / 2);
        group.add(cone);
    }

    tagEntity(group, ent);
    return group;
}

export function updateArc(mesh, ent, prev) {
    // Any structural change alters the swept geometry; cheaper to rebuild.
    if (prev && !approxEqual(resolveArcRadius(ent), resolveArcRadius(prev))) return false;
    if (prev && !approxEqual(resolveTubeRadius(ent), resolveTubeRadius(prev))) return false;
    if (prev && !approxEqual(resolveAngle(ent), resolveAngle(prev))) return false;
    if (styleNeedsRebuild(ent, prev)) return false;

    const a = ent.arrow || null;
    const b = prev?.arrow || null;
    if (!!a !== !!b) return false;
    if (
        a && b &&
        (!approxEqual(a.length, b.length) || !approxEqual(a.radius, b.radius))
    ) return false;

    applyStyleUpdate(mesh, ent);
    return true;
}
