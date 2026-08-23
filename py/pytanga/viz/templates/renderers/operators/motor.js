// Motor renderer — rotor visualization + helix + movement arrow.
// Phase 6: Moved from inline factory.js to dedicated operator module.

import * as THREE from 'three';
import { buildRotorVisual, makeFatLine, createArrow, styleParam, parseColor } from '../utils.js';


export function createMotor(ent) {
    const color = parseColor(ent, '#ff66cc');
    const opacity = styleParam(ent, 'opacity', 0.7);
    const lineWidth = styleParam(ent, 'line_thickness', 1);
    const r = ent.rotor || {};
    const t = ent.translator || {};
    const axis = r.axis || [0, 0, 1];
    const angle = r.angle ?? 1.5;
    const tv = t.vector || [0, 0, 0];
    const tm = Math.sqrt(tv[0] ** 2 + tv[1] ** 2 + tv[2] ** 2);
    const dr = ent.discRadius || 1.5;
    const origin = ent.origin || [0, 0, 0];

    const g = new THREE.Group();
    const rot = new THREE.Group();

    // Rotor visualization (disc arc + torus + axis line), local +Z axis.
    rot.add(buildRotorVisual(color, opacity, lineWidth, angle, dr));

    // Helix curling around the rotation axis and advancing along it.
    const hr = 1.0;
    const turns = Math.max(1, Math.ceil(Math.abs(angle) / (2 * Math.PI)));
    const pts = [];
    for (let i = 0; i <= turns * 64; i++) {
        const tt = i / (turns * 64);
        const a = tt * angle;
        pts.push(
            new THREE.Vector3(
                Math.cos(a) * hr,
                Math.sin(a) * hr,
                tt * tm * 2 - tm
            )
        );
    }
    rot.add(makeFatLine(pts, color, opacity, lineWidth));

    // Align the rotor + helix so local +Z maps to the rotation axis.
    rot.setRotationFromQuaternion(
        new THREE.Quaternion().setFromUnitVectors(
            new THREE.Vector3(0, 0, 1),
            new THREE.Vector3(axis[0], axis[1], axis[2]).normalize()
        )
    );
    g.add(rot);

    // Movement arrow along the translation direction.
    if (tm > 0) {
        g.add(createArrow(color, opacity, tv, tm, [0, 0, 0]));
    }

    g.position.set(origin[0], origin[1], origin[2]);
    return g;
}