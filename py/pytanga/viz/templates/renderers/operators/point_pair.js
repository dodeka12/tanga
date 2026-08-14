// PointPair renderer — two spheres connected by a line.
// Phase 6: Moved from inline factory.js to dedicated operator module.

import * as THREE from 'three';
import {
    makeFatLine,
    makeMaterial,
    styleParam,
    parseColor,
    addWireframeOverlay,
} from '../utils.js';

export function createPointPair(ent) {
    const color = parseColor(ent, '#44ff44');
    const opacity = styleParam(ent, 'opacity', 1.0);
    const col = new THREE.Color(color);
    const g = new THREE.Group();

    // Place the group at the midpoint so that child positions are relative
    // to the midpoint (consistent with all other entity renderers).
    const pa = ent.pointA || [0, 0, 0];
    const pb = ent.pointB || [0, 0, 0];
    const mid = [(pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2, (pa[2] + pb[2]) / 2];
    g.position.set(mid[0], mid[1], mid[2]);

    const sz = ent.pointSize || 0.06;
    const wireframe = styleParam(ent, 'wireframe', false);
    const wfColor = styleParam(ent, 'wireframe_color', null);
    const wfOpacity = styleParam(ent, 'wireframe_opacity', 1.0);
    const dash = wireframe ? styleParam(ent, 'wireframe_dash', null) : null;

    for (const pt of [pa, pb]) {
        const gm = new THREE.Mesh(
            new THREE.SphereGeometry(sz, 16, 16),
            makeMaterial(col, opacity)
        );
        // Positions relative to midpoint
        gm.position.set(pt[0] - mid[0], pt[1] - mid[1], pt[2] - mid[2]);

        // Wireframe overlay on each point sphere
        if (wireframe) {
            addWireframeOverlay(
                gm,
                new THREE.SphereGeometry(sz * 1.005, 16, 16),
                wfColor || col,
                dash,
                wfOpacity
            );
        }

        g.add(gm);
    }

    const lineThickness = styleParam(ent, 'line_thickness', 1);
    const start = new THREE.Vector3(
        pa[0] - mid[0], pa[1] - mid[1], pa[2] - mid[2]
    );
    const end = new THREE.Vector3(
        pb[0] - mid[0], pb[1] - mid[1], pb[2] - mid[2]
    );
    g.add(makeFatLine([start, end], col, opacity, lineThickness));
    return g;
}