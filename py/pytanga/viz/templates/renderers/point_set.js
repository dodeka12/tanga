// Point set renderer — draws each point as a small sphere in a group.
import * as THREE from 'three';
import { createPoint } from './point.js';
import { tagEntity, applyStyleUpdate, contentChanged } from './utils.js';

export function createPointSet(ent) {
    const group = new THREE.Group();
    for (const p of ent.points || []) {
        group.add(
            createPoint({
                position: p,
                color: ent.color,
                style: ent.style,
            }),
        );
    }
    tagEntity(group, ent);
    return group;
}

export function updatePointSet(mesh, ent, prev) {
    if (contentChanged(ent, prev, ['points'])) return false;
    applyStyleUpdate(mesh, ent);
    return true;
}
