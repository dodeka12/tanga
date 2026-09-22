// Direction renderer — rendered as a 3D arrow (cylinder shaft + cone head).
// Phase 5: Per-entity module.

import * as THREE from 'three';
import {
    makeMaterial,
    styleParam,
    parseColor,
    tagEntity,
    applyStyleUpdate,
    approxEqual,
} from './utils.js';
import { styleNeedsRebuild } from './style-diff.js';

export function createDirection(ent) {
    const color = parseColor(ent, '#ffffff');
    const opacity = styleParam(ent, 'opacity', 0.9);
    const length = styleParam(ent, 'length', 2.0);

    // Canonical: an arrow along +Y from the origin; placement (the direction
    // vector) rides on the node transform.
    const group = new THREE.Group();

    // Arrow shaft
    const shaftLength = length * 0.75;
    const shaftRadius = 0.04;
    const shaftGeo = new THREE.CylinderGeometry(shaftRadius, shaftRadius, shaftLength, 8, 1);
    const shaftMat = makeMaterial(color, opacity);
    const shaft = new THREE.Mesh(shaftGeo, shaftMat);
    shaft.position.y = shaftLength / 2;
    group.add(shaft);

    // Arrow head
    const headLength = length * 0.25;
    const headRadius = 0.10;
    const headGeo = new THREE.ConeGeometry(headRadius, headLength, 8, 1);
    const headMat = makeMaterial(color, opacity);
    const head = new THREE.Mesh(headGeo, headMat);
    head.position.y = shaftLength + headLength / 2;
    group.add(head);

    tagEntity(group, ent);
    return group;
}

export function updateDirection(mesh, ent, prev) {
    if (styleNeedsRebuild(ent, prev)) return false;
    applyStyleUpdate(mesh, ent);

    if (ent.length !== undefined && prev && !approxEqual(ent.length, prev.length)) return false;
    return true;
}
