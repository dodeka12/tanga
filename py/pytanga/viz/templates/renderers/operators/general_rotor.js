// GeneralRotor renderer — two bivector discs with common axis.
// Phase 6: Moved from inline factory.js to dedicated operator module.

import * as THREE from 'three';
import { styleParam,  parseColor } from '../utils.js';


export function createGeneralRotor(ent) {
    const color = parseColor(ent, '#ff9966');
    const opacity = styleParam(ent, 'opacity', 0.6);
    const col = new THREE.Color(color);
    const r = ent.rotor || {};
    const t = ent.translator || {};
    const ax = r.axis || [0, 0, 1];
    const tv = t.vector || [1, 0, 0];
    const g = new THREE.Group();
    const dg = new THREE.CircleGeometry(1.5, 32);
    g.add(
        new THREE.Mesh(
            dg,
            new THREE.MeshBasicMaterial({
                color: col,
                opacity: opacity * 0.5,
                transparent: true,
                side: THREE.DoubleSide,
                depthWrite: false,
            })
        )
    );
    const bd = new THREE.Mesh(
        new THREE.CircleGeometry(1.0, 32),
        new THREE.MeshBasicMaterial({
            color: col,
            opacity: opacity * 0.35,
            transparent: true,
            side: THREE.DoubleSide,
            depthWrite: false,
        })
    );
    bd.setRotationFromQuaternion(
        new THREE.Quaternion().setFromUnitVectors(
            new THREE.Vector3(0, 0, 1),
            new THREE.Vector3(tv[0], tv[1], tv[2]).normalize()
        )
    );
    g.add(bd);
    g.setRotationFromQuaternion(
        new THREE.Quaternion().setFromUnitVectors(
            new THREE.Vector3(0, 0, 1),
            new THREE.Vector3(ax[0], ax[1], ax[2]).normalize()
        )
    );
    return g;
}