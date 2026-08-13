// Entity renderer factory — thin dispatcher importing from per-entity
// and per-operator modules.  Phase 5+6 refactoring complete.

import { createPoint } from './point.js';
import { createCrossHairPoint } from './crosshair_point.js';
import { createDirection } from './direction.js';
import { createLine } from './line.js';
import { createPlane } from './plane.js';
import { createCircle } from './circle.js';
import { createSphere } from './sphere.js';
import { createSpace } from './space.js';
import { createPointPair } from './operators/point_pair.js';
import { createInversion } from './operators/inversion.js';
import { createRotor } from './operators/rotor.js';
import { createTranslator } from './operators/translator.js';
import { createDilator } from './operators/dilator.js';
import { createMotor } from './operators/motor.js';
import { createGeneralRotor } from './operators/general_rotor.js';
import { createReflectionLine } from './operators/reflection_line.js';
import { createReflectionPlane } from './operators/reflection_plane.js';
import { createReflectionPoint } from './operators/reflection_point.js';
import { createPointPath } from './point_path.js';
import { createAxis } from './axis.js';
import { createAxes2D } from './axes2d.js';
import { createAxes3D } from './axes3d.js';
import { createGrid } from './grid.js';
import { tagEntity } from './utils.js';

/**
 * Create a Three.js Object3D for a given entity JSON dict.
 * Dispatches to the appropriate per-entity renderer.
 */
export async function createEntityMesh(ent) {
    let mesh;

    switch (ent.kind) {
        // ── Per-entity renderers (Phase 5) ──
        case 'Point':
        case 'HPoint':
            if (ent.style?.style_type === 'CrossHairPointStyle') {
                mesh = createCrossHairPoint(ent);
            } else {
                mesh = createPoint(ent);
            }
            break;
        case 'Direction':
            mesh = createDirection(ent);
            break;
        case 'Line':
            mesh = createLine(ent);
            break;
        case 'Plane':
            mesh = await createPlane(ent);
            break;
        case 'Circle':
            mesh = createCircle(ent);
            break;
        case 'Sphere':
            mesh = await createSphere(ent);
            break;
        case 'Space':
            mesh = createSpace(ent);
            break;

        // ── Operators (inline until Phase 6 refactoring) ──
        case 'PointPair':
            mesh = createPointPair(ent);
            break;
        case 'Inversion':
            mesh = createInversion(ent);
            break;
        case 'Rotor':
            mesh = createRotor(ent);
            break;
        case 'Translator':
            mesh = createTranslator(ent);
            break;
        case 'Dilator':
            mesh = createDilator(ent);
            break;
        case 'Motor':
            mesh = createMotor(ent);
            break;
        case 'GeneralRotor':
            mesh = createGeneralRotor(ent);
            break;
        case 'ReflectionLine':
            mesh = createReflectionLine(ent);
            break;
        case 'ReflectionPlane':
            mesh = createReflectionPlane(ent);
            break;
        case 'ReflectionPoint':
            mesh = createReflectionPoint(ent);
            break;

        case 'PointPath':
            mesh = createPointPath(ent);
            break;

        case 'Axis':
            mesh = createAxis(ent);
            break;
        case 'Axes2D':
            mesh = createAxes2D(ent);
            break;
        case 'Axes3D':
            mesh = createAxes3D(ent);
            break;
        case 'Grid':
            mesh = createGrid(ent);
            break;

        default:
            console.warn(`Unknown entity kind: ${ent.kind}`);
            return null;
    }

    if (mesh) {
        tagEntity(mesh, ent);
    }
    return mesh;
}

export function removeEntityMesh(mesh) {
    if (!mesh) return;
    if (mesh.parent) mesh.parent.remove(mesh);
    mesh.traverse((c) => {
        if (c.geometry) c.geometry.dispose();
        if (c.material) {
            if (Array.isArray(c.material))
                c.material.forEach((m) => m.dispose());
            else c.material.dispose();
        }
    });
}

