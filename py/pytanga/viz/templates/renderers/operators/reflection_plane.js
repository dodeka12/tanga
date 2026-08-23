// ReflectionPlane renderer — mirror plane with normal arrow.
// Phase 6: Moved from inline factory.js to dedicated operator module.

import * as THREE from 'three';
import { styleParam,  parseColor, createArrow } from '../utils.js';


export function createReflectionPlane(ent) {
    const color = parseColor(ent, '#88ccff');
    const opacity = styleParam(ent, 'opacity', 0.35);
    const col = new THREE.Color(color);
    const n = ent.normal || [0, 0, 1];
    const ext = ent.extent ?? 5;
    const g = new THREE.Group();
    const pg = new THREE.PlaneGeometry(ext * 2, ext * 2);
    const pm = new THREE.MeshPhongMaterial({
        color: col,
        opacity,
        transparent: true,
        depthWrite: false,
        side: THREE.DoubleSide,
        emissive: col,
        emissiveIntensity: 0.15,
    });
    g.add(new THREE.Mesh(pg, pm));
    const al = ext * 0.3;
    const arrowG = createArrow(color, 0.8, n, al, [0, 0, 0]);
    g.add(arrowG);
    g.setRotationFromQuaternion(
        new THREE.Quaternion().setFromUnitVectors(
            new THREE.Vector3(0, 0, 1),
            new THREE.Vector3(n[0], n[1], n[2]).normalize()
        )
    );
    return g;
}