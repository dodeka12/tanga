// Motor renderer — general rotor (displaced axis) + translation arrow along it.
// Phase 6: Moved from inline factory.js to dedicated operator module.

import * as THREE from 'three';
import { buildRotorVisual, createArrow, styleParam, parseColor } from '../utils.js';


export function createMotor(ent) {
    const color = parseColor(ent, '#ff66cc');
    const opacity = styleParam(ent, 'opacity', 0.7);
    const lineWidth = styleParam(ent, 'line_thickness', 1);
    const r = ent.rotor || {};
    const t = ent.translator || {};
    const axis = r.axis || [0, 0, 1];
    const angle = r.angle ?? 0;
    const origin = r.origin || [0, 0, 0];
    const tv = t.vector || [0, 0, 0];
    const tm = Math.sqrt(tv[0] ** 2 + tv[1] ** 2 + tv[2] ** 2);
    const dr = ent.discRadius || 1.5;

    const g = new THREE.Group();

    // General rotor: rotor visualization displaced to its axis origin.
    const rotorG = buildRotorVisual(color, opacity, lineWidth, angle, dr);
    rotorG.setRotationFromQuaternion(
        new THREE.Quaternion().setFromUnitVectors(
            new THREE.Vector3(0, 0, 1),
            new THREE.Vector3(axis[0], axis[1], axis[2]).normalize()
        )
    );
    rotorG.position.set(origin[0], origin[1], origin[2]);
    g.add(rotorG);

    // Translation arrow along the axis (screw pitch).
    if (tm > 0) {
        g.add(createArrow(color, opacity, tv, tm, origin));
    }

    return g;
}