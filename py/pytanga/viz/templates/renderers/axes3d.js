// Axes3D renderer — a group of coordinate axes in 3D space.
// Each axis half is drawn via the shared `addAxis` base so all axes
// render identically.

import * as THREE from 'three';
import { addAxis } from './axis.js';
import {
    applyStyleUpdate,
    clearGroupChildren,
    contentChanged,
    tagEntity,
} from './utils.js';
import { styleNeedsRebuild } from './style-diff.js';

export function createAxes3D(ent) {
    const group = new THREE.Group();
    for (const axis of ent.axes || []) {
        addAxis(group, axis);
    }
    tagEntity(group, ent);
    return group;
}

export function updateAxes3D(mesh, ent, prev) {
    if (!prev) return false;
    if (styleNeedsRebuild(ent, prev)) return false;
    if (contentChanged(ent, prev, ['axes'])) {
        clearGroupChildren(mesh);
        for (const axis of ent.axes || []) {
            addAxis(mesh, axis);
        }
    }
    applyStyleUpdate(mesh, ent);
    return true;
}