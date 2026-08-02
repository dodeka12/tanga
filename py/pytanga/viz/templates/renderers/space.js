// Space renderer — rendered as box edges bounding the visible space.
// Phase 5: Per-entity module.

import * as THREE from 'three';
import { styleParam, parseColor, tagEntity } from './utils.js';

export function createSpace(ent) {
    const color = parseColor(ent, '#888888');
    const opacity = styleParam(ent, 'opacity', 0.15);
    const extent = styleParam(ent, 'extent', 10.0);

    const geometry = new THREE.BoxGeometry(extent * 2, extent * 2, extent * 2);
    const edges = new THREE.EdgesGeometry(geometry);
    const material = new THREE.LineBasicMaterial({
        color: new THREE.Color(color),
        opacity,
        transparent: true,
    });
    const box = new THREE.LineSegments(edges, material);

    tagEntity(box, ent);
    return box;
}