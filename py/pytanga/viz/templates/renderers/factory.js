// Entity renderer factory — thin dispatcher importing from per-entity
// and per-operator modules.  Phase 5+6 refactoring complete.

import { createPoint } from './point.js';
import { createCrossHairPoint } from './crosshair_point.js';
import { createDirection, updateDirection } from './direction.js';
import { createLine, updateLine } from './line.js';
import { createPlane } from './plane.js';
import { createArc, updateArc } from './arc.js';
import { createCircle } from './circle.js';
import { createCylinder, updateCylinder } from './cylinder.js';
import { createSphere } from './sphere.js';
import { createDisk } from './disk.js';
import { createPartialDisk } from './partial_disk.js';
import { createBox } from './box.js';
import { createEllipsoid } from './ellipsoid.js';
import { createEllipse } from './ellipse.js';
import { createRegularPolygon } from './regular_polygon.js';
import { createHyperbola } from './hyperbola.js';
import { createParabola } from './parabola.js';
import { createLinePair } from './line_pair.js';
import { createPointSet } from './point_set.js';
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
import { createPointPath, updatePointPath } from './point_path.js';
import { createAxis } from './axis.js';
import { createAxes2D } from './axes2d.js';
import { createAxes3D } from './axes3d.js';
import { createGrid } from './grid.js';
import { createVizGroup } from './group.js';
import { createSdfProxy, updateSdfProxy } from './sdf.js';
import { createRayProxy, updateRayProxy } from './ray.js';
import { applyStyleUpdate, entityRequiresRebuild, tagEntity } from './utils.js';

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
        case 'Arc':
            mesh = createArc(ent);
            break;
        case 'Sphere':
            mesh = await createSphere(ent);
            break;
        case 'Cylinder':
            mesh = createCylinder(ent);
            break;
        case 'Disk':
            mesh = createDisk(ent);
            break;
        case 'PartialDisk':
            mesh = createPartialDisk(ent);
            break;
        case 'Box':
            mesh = createBox(ent);
            break;
        case 'Ellipsoid':
            mesh = createEllipsoid(ent);
            break;
        case 'Ellipse':
            mesh = createEllipse(ent);
            break;
        case 'RegularPolygon':
            mesh = createRegularPolygon(ent);
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

        case 'VizGroup':
            mesh = createVizGroup(ent);
            break;

        case 'sdf':
            mesh = await createSdfProxy(ent);
            break;

        case 'ray':
            mesh = await createRayProxy(ent);
            break;

        case 'Hyperbola':
            mesh = createHyperbola(ent);
            break;

        case 'Parabola':
            mesh = createParabola(ent);
            break;

        case 'LinePair':
        case 'ParallelLinePair':
            mesh = createLinePair(ent);
            break;

        case 'PointSet':
            mesh = createPointSet(ent);
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

export function updateEntityMesh(mesh, ent, prev) {
    // Route to the co-located, kind-specific updater when one exists; these
    // handle bespoke placement (e.g. Line's segment midpoint) and return false
    // when the geometry must be rebuilt instead of updated in place.
    switch (ent.kind) {
        case 'sdf':
            // Structural (tree/bound/sdfKind) changes rebuild the shader;
            // transform/style changes are applied in place by updateSdfProxy.
            if (entityRequiresRebuild(ent, prev)) return false;
            return updateSdfProxy(mesh, ent, prev);
        case 'ray':
            if (entityRequiresRebuild(ent, prev)) return false;
            return updateRayProxy(mesh, ent);
        case 'Line':
            return updateLine(mesh, ent, prev);
        case 'PointPath':
            return updatePointPath(mesh, ent, prev);
        case 'Direction':
            return updateDirection(mesh, ent, prev);
        case 'Arc':
            return updateArc(mesh, ent, prev);
        case 'Cylinder':
            return updateCylinder(mesh, ent, prev);
        default:
            break;
    }

    // Generic in-place update: position/orientation + common style fields.
    if (ent.position) {
        mesh.position.set(ent.position[0], ent.position[1], ent.position[2]);
    }
    if (ent.center) {
        mesh.position.set(ent.center[0], ent.center[1], ent.center[2]);
    }
    if (ent.vector || ent.direction) {
        const vec = ent.vector || ent.direction;
        const origin = ent.origin || [0, 0, 0];
        mesh.position.set(origin[0], origin[1], origin[2]);
        const dir = new THREE.Vector3(vec[0], vec[1], vec[2]).normalize();
        const quat = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
        mesh.setRotationFromQuaternion(quat);
    }
    applyStyleUpdate(mesh, ent);

    return !entityRequiresRebuild(ent, prev);
}

export function removeEntityMesh(mesh) {
    if (!mesh) return;
    // Detach nested CSS2D label elements before removing from the scene so
    // they don't linger as ghost labels. Object3D.remove() only dispatches
    // 'removed' on the object itself, not its CSS2D descendants.
    mesh.traverse((c) => {
        if (c.isCSS2DObject && c.element && c.element.parentNode) {
            c.element.parentNode.removeChild(c.element);
        }
    });
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

