// Plane pair renderer — draws the two member planes (world-space, baked) as a
// group.  Member planes carry their own point/normal, so they are rendered
// inline rather than through the canonical `createPlane`.
import * as THREE from 'three';
import { makeMaterial, styleParam, parseColor, tagEntity, applyStyleUpdate, contentChanged } from './utils.js';
import { styleNeedsRebuild } from './style-diff.js';

function _bakedPlane(wire, ent) {
    const color = parseColor(ent, '#4488ff');
    const opacity = styleParam(ent, 'opacity', 0.3);
    const extent = wire.extent ?? styleParam(ent, 'extent', 10.0);
    const geometry = new THREE.PlaneGeometry(extent * 2, extent * 2);
    const mesh = new THREE.Mesh(geometry, makeMaterial(color, opacity, true));
    const point = wire.point || [0, 0, 0];
    const normal = wire.normal || [0, 0, 1];
    mesh.position.set(point[0], point[1], point[2]);
    mesh.setRotationFromQuaternion(
        new THREE.Quaternion().setFromUnitVectors(
            new THREE.Vector3(0, 0, 1),
            new THREE.Vector3(...normal).normalize(),
        ),
    );
    return mesh;
}

export async function createPlanePair(ent) {
    const group = new THREE.Group();
    for (const wire of [ent.plane1, ent.plane2]) {
        if (!wire) continue;
        group.add(_bakedPlane(wire, ent));
    }
    tagEntity(group, ent);
    return group;
}

export function updatePlanePair(mesh, ent, prev) {
    if (contentChanged(ent, prev, ['plane1', 'plane2'])) return false;
    if (styleNeedsRebuild(ent, prev)) return false;
    applyStyleUpdate(mesh, ent);
    return true;
}
