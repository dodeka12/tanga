// Ellipse renderer — a 2D ellipse drawn as a screen-space fat line, plus an
// optional semi-transparent fill disc under the outline (so the body is easy
// to click/select, like a filled Rectangle2D).
// Phase 4: Per-entity module.

import * as THREE from 'three';
import {
    makeFatLine,
    makeMaterial,
    styleParam,
    parseColor,
    tagEntity,
    applyStyleUpdate,
    contentChanged,
} from './utils.js';
import { styleNeedsRebuild } from './style-diff.js';

const ELLIPSE_SEGMENTS = 128;

export function createEllipse(ent) {
    const color = parseColor(ent, '#ff44ff');
    const opacity = styleParam(ent, 'opacity', 0.9);
    const thickness = styleParam(ent, 'thickness', 1.0);
    const radiusU = Math.max(ent.radiusU || 1.0, 0.001);
    const radiusV = Math.max(ent.radiusV || 0.5, 0.001);

    const group = new THREE.Group();

    // Optional semi-transparent fill disc under the outline.
    if (styleParam(ent, 'fill', false)) {
        const fillOpacity = styleParam(ent, 'fill_opacity', 0.2);
        const fillGeo = new THREE.CircleGeometry(1, ELLIPSE_SEGMENTS);
        const fill = new THREE.Mesh(fillGeo, makeMaterial(color, fillOpacity, true));
        // A unit disc scaled to the ellipse radii, in the canonical XY plane.
        fill.scale.set(radiusU, radiusV, 1);
        // Mark the fill so style updates apply `fill_opacity` (not the
        // top-level outline `opacity`) to it.
        fill.userData.isFillQuad = true;
        group.add(fill);
    }

    // Canonical: an ellipse in the XY plane at the origin, `radiusU` along +X
    // and `radiusV` along +Y.  Placement (center + normal + dirU/dirV) rides on
    // the node transform.
    const points = [];
    for (let i = 0; i <= ELLIPSE_SEGMENTS; i++) {
        const t = (2 * Math.PI * i) / ELLIPSE_SEGMENTS;
        points.push(new THREE.Vector3(radiusU * Math.cos(t), radiusV * Math.sin(t), 0));
    }

    group.add(makeFatLine(points, color, opacity, thickness));
    tagEntity(group, ent);
    return group;
}

export function updateEllipse(mesh, ent, prev) {
    if (contentChanged(ent, prev, ['radiusU', 'radiusV'])) return false;
    if (styleNeedsRebuild(ent, prev)) return false;
    applyStyleUpdate(mesh, ent);
    return true;
}
