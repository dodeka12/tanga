// ReflectionOrigin renderer — 3-axis crosshair at the origin.
// Phase 6: Moved from inline factory.js to dedicated operator module.

import * as THREE from 'three';
import { styleParam,  parseColor } from '../utils.js';


export function createReflectionOrigin(ent) {
    const color = parseColor(ent, '#ffffff');
    const opacity = styleParam(ent, 'opacity', 0.5);
    const col = new THREE.Color(color);
    const ext = ent.extent || 1.0;
    const g = new THREE.Group();
    for (const d of [
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
    ]) {
        const pts = [
            new THREE.Vector3(-d[0] * ext, -d[1] * ext, -d[2] * ext),
            new THREE.Vector3(d[0] * ext, d[1] * ext, d[2] * ext),
        ];
        g.add(
            new THREE.Line(
                new THREE.BufferGeometry().setFromPoints(pts),
                new THREE.LineBasicMaterial({
                    color: col,
                    opacity,
                    transparent: true,
                })
            )
        );
    }
    return g;
}