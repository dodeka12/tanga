// Curve renderer — draws each path (a list of 3D points) as a fat polyline.
import * as THREE from 'three';
import {
    makeFatLine,
    styleParam,
    parseColor,
    tagEntity,
    applyStyleUpdate,
    contentChanged,
} from './utils.js';

export function createCurve(ent) {
    const color = parseColor(ent, '#44ff44');
    const opacity = styleParam(ent, 'opacity', 0.8);
    const thickness = styleParam(ent, 'thickness', 2.0);
    const group = new THREE.Group();
    for (const path of ent.paths || []) {
        if (!path || path.length < 2) continue;
        const points = path.map((p) => new THREE.Vector3(p[0], p[1], p[2]));
        group.add(makeFatLine(points, color, opacity, thickness));
    }
    tagEntity(group, ent);
    return group;
}

export function updateCurve(mesh, ent, prev) {
    if (contentChanged(ent, prev, ['paths'])) return false;
    applyStyleUpdate(mesh, ent);
    return true;
}
