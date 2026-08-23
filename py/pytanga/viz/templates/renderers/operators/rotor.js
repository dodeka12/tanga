// Rotor renderer — disc arc, outer torus, and axis line.
// Phase 6: Moved from inline factory.js to dedicated operator module.

import * as THREE from 'three';
import { buildRotorVisual, styleParam, parseColor } from '../utils.js';


export function createRotor(ent) {
    const color = parseColor(ent, '#ff8844');
    const opacity = styleParam(ent, 'opacity', 0.7);
    const lineWidth = styleParam(ent, 'line_thickness', 1);
    const axis = ent.axis || [0, 0, 1];
    const angle = ent.angle ?? 0;
    const dr = ent.discRadius || 1.5;

    const g = buildRotorVisual(color, opacity, lineWidth, angle, dr);
    g.setRotationFromQuaternion(
        new THREE.Quaternion().setFromUnitVectors(
            new THREE.Vector3(0, 0, 1),
            new THREE.Vector3(axis[0], axis[1], axis[2]).normalize()
        )
    );
    return g;
}