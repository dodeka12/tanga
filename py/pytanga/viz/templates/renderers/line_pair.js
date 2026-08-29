// Line pair renderer — draws the two member lines as a group.
import * as THREE from 'three';
import { createLine } from './line.js';
import { tagEntity } from './utils.js';

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
