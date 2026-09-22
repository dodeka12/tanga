// Rectangle2D renderer — a flat rectangle: outline (fat line) + optional fill.
// Phase: interactive rectangles.

import * as THREE from 'three';
import {
    makeMaterial,
    makeFatSegmentsFromFlat,
    styleParam,
    parseColor,
    tagEntity,
} from './utils.js';

export function createRectangle2D(ent) {
    const color = parseColor(ent, '#ffffff');
    const opacity = styleParam(ent, 'opacity', 1.0);
    const size = ent.size || [1, 1];
    // Canonical plane is XY (normal +Z); placement rides on the node transform.
    const angle = ent.angle || 0.0;

    const group = new THREE.Group();

    // Optional semi-transparent fill under the outline.
    if (styleParam(ent, 'fill', false)) {
        const fillOpacity = styleParam(ent, 'fill_opacity', 0.2);
        const fillGeo = new THREE.PlaneGeometry(size[0], size[1]);
        const fill = new THREE.Mesh(fillGeo, makeMaterial(color, fillOpacity, true));
        // Mark the fill so style updates apply `fill_opacity` (not the
        // top-level outline `opacity`) to it.
        fill.userData.isFillQuad = true;
        group.add(fill);
    }

    // Outline: a fat-line rectangle loop (4 segments) in the local xy-plane.
    const hw = size[0] / 2;
    const hh = size[1] / 2;
    const thickness = styleParam(ent, 'thickness', 2.0);
    const outline = makeFatSegmentsFromFlat([
        -hw, -hh, 0,  hw, -hh, 0,
         hw, -hh, 0,  hw,  hh, 0,
         hw,  hh, 0, -hw,  hh, 0,
        -hw,  hh, 0, -hw, -hh, 0,
    ], color, opacity, thickness);
    group.add(outline);

    if (angle) {
        group.rotateZ(angle);
    }

    tagEntity(group, ent);
    return group;
}
