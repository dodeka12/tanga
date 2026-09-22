// Line pair renderer — draws the two member lines (world-space, baked) as a
// group.  Member lines carry their own origin/direction, so they are rendered
// inline rather than through the canonical `createLine`.
import * as THREE from 'three';
import { makeFatLine, styleParam, parseColor, tagEntity, applyStyleUpdate, contentChanged } from './utils.js';
import { styleNeedsRebuild } from './style-diff.js';

function _bakedLine(wire, ent) {
    const color = parseColor(ent, '#44ff44');
    const opacity = styleParam(ent, 'opacity', 0.8);
    const thickness = styleParam(ent, 'thickness', 1.0);
    const origin = new THREE.Vector3(...(wire.origin || [0, 0, 0]));
    const dir = new THREE.Vector3(...(wire.direction || [1, 0, 0])).normalize();
    const length = wire.length ?? styleParam(ent, 'length', 20.0);
    const end = origin.clone().addScaledVector(dir, length);
    return makeFatLine([origin, end], color, opacity, thickness);
}

export function createLinePair(ent) {
    const group = new THREE.Group();
    for (const wire of [ent.line1, ent.line2]) {
        if (!wire) continue;
        group.add(_bakedLine(wire, ent));
    }
    tagEntity(group, ent);
    return group;
}

export function updateLinePair(mesh, ent, prev) {
    if (contentChanged(ent, prev, ['line1', 'line2'])) return false;
    if (styleNeedsRebuild(ent, prev)) return false;
    applyStyleUpdate(mesh, ent);
    return true;
}
