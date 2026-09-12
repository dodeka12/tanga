// Line pair renderer — draws the two member lines as a group.
import * as THREE from 'three';
import { createLine } from './line.js';
import { tagEntity, applyStyleUpdate, contentChanged } from './utils.js';

export function createLinePair(ent) {
    const group = new THREE.Group();
    for (const wire of [ent.line1, ent.line2]) {
        if (!wire) continue;
        group.add(
            createLine({
                origin: wire.origin,
                direction: wire.direction,
                color: ent.color,
                style: ent.style,
            }),
        );
    }
    tagEntity(group, ent);
    return group;
}

export function updateLinePair(mesh, ent, prev) {
    if (contentChanged(ent, prev, ['line1', 'line2'])) return false;
    applyStyleUpdate(mesh, ent);
    return true;
}
