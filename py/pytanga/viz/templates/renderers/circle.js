// Circle renderer — a torus (tube) by default, or a thick screen-space line
// when styled with `CircleStyle`. Phase 5: Per-entity module.

import * as THREE from 'three';
import {
    makeMaterial,
    makeFatLine,
    rotationFromNormal,
    styleParam,
    parseColor,
    tagEntity,
    addWireframeOverlay,
} from './utils.js';

const SEGMENTS = 96;

function isLineStyle(ent) {
    return !!(ent.style && ent.style.style_type === 'CircleStyle');
}

function createLineCircle(ent) {
    const color = parseColor(ent, '#ff44ff');
    const opacity = styleParam(ent, 'opacity', 0.9);
    const thickness = styleParam(ent, 'thickness', 1.0);
    const center = ent.center || [0, 0, 0];
    const radius = Math.max(ent.radius || 1.0, 0.001);
    const normal = ent.normal || [0, 0, 1];

    const q = rotationFromNormal(normal[0], normal[1], normal[2]);
    const ex = new THREE.Vector3(1, 0, 0).applyQuaternion(q);
    const ey = new THREE.Vector3(0, 1, 0).applyQuaternion(q);

    const points = [];
    for (let i = 0; i <= SEGMENTS; i++) {
        const t = (2 * Math.PI * i) / SEGMENTS;
        points.push(
            new THREE.Vector3(center[0], center[1], center[2])
                .addScaledVector(ex, radius * Math.cos(t))
                .addScaledVector(ey, radius * Math.sin(t)),
        );
    }

    const line = makeFatLine(points, color, opacity, thickness);
    tagEntity(line, ent);
    return line;
}


export function createCircle(ent) {
    if (isLineStyle(ent)) {
        return createLineCircle(ent);
    }

    const color = parseColor(ent, '#ff44ff');
    const opacity = styleParam(ent, 'opacity', 0.7);
    const center = ent.center || [0, 0, 0];
    const radius = Math.max(ent.radius || 1.0, 0.001);
    const tubeRadius = styleParam(ent, 'tubeRadius', 0.03);
    const wireframe = styleParam(ent, 'wireframe', false);

    const wireframeOnly = wireframe && opacity === 0;

    const geometry = new THREE.TorusGeometry(radius, tubeRadius, 16, 64);
    const mesh = wireframeOnly
        ? new THREE.Group()
        : new THREE.Mesh(geometry, makeMaterial(color, opacity));

    mesh.position.set(center[0], center[1], center[2]);

    if (ent.normal) {
        mesh.setRotationFromQuaternion(
            rotationFromNormal(ent.normal[0], ent.normal[1], ent.normal[2])
        );
    }

    // Wireframe overlay
    if (wireframe) {
        const wfColor = styleParam(ent, 'wireframe_color', null) || color;
        const wfOpacity = styleParam(ent, 'wireframe_opacity', 1.0);
        const dash = styleParam(ent, 'wireframe_dash', null);
        addWireframeOverlay(
            mesh,
            new THREE.TorusGeometry(radius * 1.005, tubeRadius, 16, 64),
            wfColor,
            dash,
            wfOpacity
        );
    }

    tagEntity(mesh, ent);
    return mesh;
}