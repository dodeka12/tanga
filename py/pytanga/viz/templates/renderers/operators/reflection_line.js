// ReflectionLine renderer — cylinder oriented along the reflection direction.
// Phase 6: Moved from inline factory.js to dedicated operator module.

import * as THREE from 'three';
import { styleParam,  makeMaterial, parseColor } from '../utils.js';


export function createReflectionLine(ent) {
    const color = parseColor(ent, '#aaccff');
    const opacity = styleParam(ent, 'opacity', 0.6);
    const dir = ent.direction || [0, 0, 1];
    const len = ent.length || 5.0;
    const thick = ent.thickness || 0.04;
    const col = new THREE.Color(color);
    const g = new THREE.Group();
    const cg = new THREE.CylinderGeometry(thick, thick, len, 8, 1);
    g.add(new THREE.Mesh(cg, makeMaterial(col, opacity)));
    const d = new THREE.Vector3(dir[0], dir[1], dir[2]).normalize();
    g.setRotationFromQuaternion(
        new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), d)
    );
    return g;
}