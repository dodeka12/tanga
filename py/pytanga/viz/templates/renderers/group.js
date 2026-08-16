// VizGroup renderer — an empty THREE.Group container (no geometry).
// Scene-graph group nodes carry only a transform + parent/child structure.

import * as THREE from 'three';
import { tagEntity } from './utils.js';

export function createVizGroup(ent) {
    const group = new THREE.Group();
    tagEntity(group, ent);
    return group;
}
