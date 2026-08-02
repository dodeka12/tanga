// CrossHairPointStyle renderer — renders a 3D crosshair (three orthogonal cylinders)
// instead of a sphere.  Phase 8b: extended style example.

import * as THREE from 'three';
import { makeMaterial, styleParam, parseColor, tagEntity } from './utils.js';

export function createCrossHairPoint(ent) {
    const color = parseColor(ent, '#ff4444');
    const opacity = styleParam(ent, 'opacity', 1.0);
    const size = styleParam(ent, 'size', 0.3);
    const armThickness = styleParam(ent, 'arm_thickness', size * 0.15);
    const pos = ent.position || [0, 0, 0];

    const group = new THREE.Group();
    const material = makeMaterial(color, opacity);

    // Three orthogonal arms (X, Y, Z)
    const directions = [
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
    ];

    for (const [dx, dy, dz] of directions) {
        // Cylinder centered at origin, extending ±size along direction
        const cylGeo = new THREE.CylinderGeometry(armThickness, armThickness, size * 2, 6, 1);
        const cyl = new THREE.Mesh(cylGeo, material);

        // Orient cylinder along direction
        const dir = new THREE.Vector3(dx, dy, dz).normalize();
        const quat = new THREE.Quaternion().setFromUnitVectors(
            new THREE.Vector3(0, 1, 0), dir
        );
        cyl.setRotationFromQuaternion(quat);

        group.add(cyl);
    }

    group.position.set(pos[0], pos[1], pos[2]);
    tagEntity(group, ent);
    return group;
}