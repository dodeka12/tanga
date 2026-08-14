// Motor renderer — helix curve + axis line.
// Phase 6: Moved from inline factory.js to dedicated operator module.

import * as THREE from 'three';
import { makeFatLine, styleParam, parseColor } from '../utils.js';


export function createMotor(ent) {
    const color = parseColor(ent, '#ff66cc');
    const opacity = styleParam(ent, 'opacity', 0.7);
    const lineWidth = styleParam(ent, 'line_thickness', 1);
    const col = new THREE.Color(color);
    const r = ent.rotor || {};
    const t = ent.translator || {};
    const axis = r.axis || [0, 0, 1];
    const angle = r.angle ?? 1.5;
    const tv = t.vector || [0, 0, 0];
    const tm = Math.sqrt(tv[0] ** 2 + tv[1] ** 2 + tv[2] ** 2);
    const g = new THREE.Group();
    const hr = 1.0;
    const turns = Math.max(1, Math.ceil(Math.abs(angle) / (2 * Math.PI)));
    const pts = [];
    for (let i = 0; i <= turns * 64; i++) {
        const tt = i / (turns * 64);
        const a = tt * angle;
        pts.push(
            new THREE.Vector3(
                Math.cos(a) * hr,
                tt * tm * 2 - tm,
                Math.sin(a) * hr
            )
        );
    }
    g.add(makeFatLine(pts, col, opacity, lineWidth));
    g.setRotationFromQuaternion(
        new THREE.Quaternion().setFromUnitVectors(
            new THREE.Vector3(0, 0, 1),
            new THREE.Vector3(axis[0], axis[1], axis[2]).normalize()
        )
    );
    return g;
}