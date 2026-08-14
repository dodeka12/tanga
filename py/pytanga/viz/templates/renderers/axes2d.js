// Axes2D renderer — a group of coordinate axes in a 2D plane.
// Each axis half is drawn via the shared `addAxis` base so all axes
// render identically.

import * as THREE from 'three';
import { addAxis } from './axis.js';
import { tagEntity } from './utils.js';

export function createAxes2D(ent) {
    const group = new THREE.Group();
    for (const axis of ent.axes || []) {
        addAxis(group, axis);
    }
    tagEntity(group, ent);
    return group;
}