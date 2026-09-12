// Plane pair renderer — draws the two member planes as a group.
import * as THREE from 'three';
import { createPlane } from './plane.js';
import { tagEntity, applyStyleUpdate, contentChanged } from './utils.js';

export async function createPlanePair(ent) {
    const group = new THREE.Group();
    for (const wire of [ent.plane1, ent.plane2]) {
        if (!wire) continue;
        group.add(
            await createPlane({
                point: wire.point,
                normal: wire.normal,
                extent: wire.extent,
                color: ent.color,
                opacity: ent.opacity,
                style: ent.style,
            }),
        );
    }
    tagEntity(group, ent);
    return group;
}

export function updatePlanePair(mesh, ent, prev) {
    if (contentChanged(ent, prev, ['plane1', 'plane2'])) return false;
    applyStyleUpdate(mesh, ent);
    return true;
}
