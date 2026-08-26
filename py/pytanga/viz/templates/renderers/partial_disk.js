// PartialDisk renderer — a flat, pie-shaped slab oriented along `normal`.
// Phase 4: Per-entity module.

import * as THREE from 'three';
import {
    makeMaterial,
    styleParam,
    parseColor,
    tagEntity,
    addWireframeOverlay,
} from './utils.js';

/**
 * Build a quaternion that maps local +Y to `normal` and local +Z to
 * `inPlane`. `inPlane` is assumed perpendicular to `normal`.
 */
function rotationFromAxes(normal, inPlane) {
    const y = new THREE.Vector3(...normal).normalize();
    const z = new THREE.Vector3(...inPlane).normalize();
    const x = new THREE.Vector3().crossVectors(y, z).normalize();
    const zOrtho = new THREE.Vector3().crossVectors(x, y).normalize();
    const m = new THREE.Matrix4().makeBasis(x, y, zOrtho);
    return new THREE.Quaternion().setFromRotationMatrix(m);
}

export function createPartialDisk(ent) {
    const color = parseColor(ent, '#ffcc44');
    const opacity = styleParam(ent, 'opacity', 0.9);
    const center = ent.center || [0, 0, 0];
    const radius = Math.max(ent.radius || 1.0, 0.001);
    const thickness = Math.max(styleParam(ent, 'thickness', 0.02), 0.001);
    const normal = ent.normal || [0, 0, 1];
    const startDirection = ent.startDirection || [1, 0, 0];
    const angle = Math.min(Math.max(ent.angle ?? 2 * Math.PI, 0.0), 2 * Math.PI);

    // The sector is symmetric about its bisector (matching the SDF primitive,
    // which is symmetric about local +Z). The bisector is `startDirection`
    // rotated by half the sweep about `normal`.
    const n = new THREE.Vector3(...normal).normalize();
    const s = new THREE.Vector3(...startDirection).normalize();
    const bisector = s.clone().multiplyScalar(Math.cos(angle / 2)).add(
        new THREE.Vector3().crossVectors(n, s).multiplyScalar(Math.sin(angle / 2))
    );

    const geometry = new THREE.CylinderGeometry(
        radius, radius, thickness, 48, 1, false, -angle / 2, angle
    );
    const mesh = new THREE.Mesh(geometry, makeMaterial(color, opacity));
    mesh.position.set(center[0], center[1], center[2]);
    mesh.setRotationFromQuaternion(rotationFromAxes(normal, bisector));

    const wireframe = styleParam(ent, 'wireframe', false);
    if (wireframe) {
        const wfColor = styleParam(ent, 'wireframe_color', null) || color;
        const wfOpacity = styleParam(ent, 'wireframe_opacity', 1.0);
        const dash = styleParam(ent, 'wireframe_dash', null);
        addWireframeOverlay(
            mesh,
            new THREE.CylinderGeometry(
                radius * 1.005, radius * 1.005, thickness, 48, 1, false,
                -angle / 2, angle
            ),
            wfColor,
            dash,
            wfOpacity
        );
    }

    tagEntity(mesh, ent);
    return mesh;
}
