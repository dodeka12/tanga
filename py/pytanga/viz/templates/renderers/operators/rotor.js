// Rotor renderer — disc arc, outer torus, arc line, radial line, and axis line.
// Phase 6: Moved from inline factory.js to dedicated operator module.

import * as THREE from 'three';
import { styleParam,  makeMaterial, parseColor } from '../utils.js';


export function createRotor(ent) {
    const color = parseColor(ent, '#ff8844');
    const opacity = styleParam(ent, 'opacity', 0.7);
    const col = new THREE.Color(color);
    const axis = ent.axis || [0, 0, 1];
    const angle = ent.angle ?? 0;
    const dr = ent.discRadius || 1.5;
    const g = new THREE.Group();
    const absA = Math.abs(angle);
    const segs = Math.max(8, Math.ceil(absA / (Math.PI / 32)));
    const rg = new THREE.RingGeometry(dr * 0.15, dr, segs, 1, 0, absA);
    const disc = new THREE.Mesh(
        rg,
        new THREE.MeshBasicMaterial({
            color: col,
            opacity: opacity * 0.8,
            transparent: true,
            side: THREE.DoubleSide,
            depthWrite: false,
        })
    );
    g.add(disc);
    g.add(
        new THREE.Mesh(
            new THREE.TorusGeometry(dr, 0.03, 16, 64),
            makeMaterial(col, opacity * 0.5)
        )
    );
    const al = dr * 1.6;
    g.add(
        new THREE.Line(
            new THREE.BufferGeometry().setFromPoints([
                new THREE.Vector3(0, 0, -al),
                new THREE.Vector3(0, 0, al),
            ]),
            new THREE.LineBasicMaterial({
                color: col,
                opacity: 0.4,
                transparent: true,
            })
        )
    );
    g.setRotationFromQuaternion(
        new THREE.Quaternion().setFromUnitVectors(
            new THREE.Vector3(0, 0, 1),
            new THREE.Vector3(axis[0], axis[1], axis[2]).normalize()
        )
    );
    return g;
}