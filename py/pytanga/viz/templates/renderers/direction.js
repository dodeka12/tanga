// Direction renderer — rendered as a 3D arrow (cylinder shaft + cone head).
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
} from './utils.js';

export function createDirection(ent) {
    const color = parseColor(ent, '#ffffff');
    const opacity = styleParam(ent, 'opacity', 0.9);
    const vec = ent.vector || [0, 0, 1];
    const length = styleParam(ent, 'length', 2.0);
    const origin = ent.origin || [0, 0, 0];

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

    group.setRotationFromQuaternion(rotationFromDirection(vec[0], vec[1], vec[2]));
    group.position.set(origin[0], origin[1], origin[2]);

    tagEntity(group, ent);
    return group;
}

export function updateDirection(mesh, ent, prev) {
    const vec = ent.vector || prev?.vector || [0, 0, 1];
    const origin = ent.origin || prev?.origin || [0, 0, 0];

    mesh.setRotationFromQuaternion(rotationFromDirection(vec[0], vec[1], vec[2]));
    mesh.position.set(origin[0], origin[1], origin[2]);

    applyStyleUpdate(mesh, ent);

    if (ent.length !== undefined && prev && !approxEqual(ent.length, prev.length)) return false;
    return true;
}
