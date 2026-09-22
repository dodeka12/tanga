// Entity renderer factory — thin dispatcher importing from per-entity
// and per-operator modules.  Phase 5+6 refactoring complete.

import { sendLog } from '../events.js';
import { createPoint } from './point.js';
import { createCrossHairPoint } from './crosshair_point.js';
import { createSquarePoint } from './square_point.js';
import { createDirection, updateDirection } from './direction.js';
import { createLine, updateLine } from './line.js';
import { createPlane } from './plane.js';
import { createArc, updateArc } from './arc.js';
import { createCircle, updateCircle } from './circle.js';
import { createCylinder, updateCylinder } from './cylinder.js';
import { createCone, updateCone } from './cone.js';
import { createSphere } from './sphere.js';
import { createDisk } from './disk.js';
import { createPartialDisk } from './partial_disk.js';
import { createBox } from './box.js';
import { createEllipsoid } from './ellipsoid.js';
import { createEllipse, updateEllipse } from './ellipse.js';
import { createRegularPolygon } from './regular_polygon.js';
import { createRectangle2D } from './rectangle2d.js';
import { createFrustum } from './frustum.js';
import { createHyperbola, updateHyperbola } from './hyperbola.js';
import { createParabola, updateParabola } from './parabola.js';
import { createLinePair, updateLinePair } from './line_pair.js';
import { createPlanePair, updatePlanePair } from './plane_pair.js';
import { createCurve, updateCurve } from './curve.js';
import { createPointSet, updatePointSet } from './point_set.js';
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
import { createImage, updateImage } from './image.js';
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
            } else if (ent.style?.style_type === 'SquarePointStyle') {
                mesh = createSquarePoint(ent);
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
        case 'Cone':
            mesh = createCone(ent);
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
        case 'Rectangle2D':
            mesh = createRectangle2D(ent);
            break;

        case 'Frustum':
            mesh = createFrustum(ent);
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

        case 'image':
            mesh = await createImage(ent);
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

        case 'PlanePair':
        case 'ParallelPlanePair':
            mesh = await createPlanePair(ent);
            break;

        case 'PlaneConic':
        case 'PlaneConicPair':
        case 'Curve':
            mesh = createCurve(ent);
            break;

        case 'PointSet':
            mesh = createPointSet(ent);
            break;

        default:
            console.warn(`Unknown entity kind: ${ent.kind}`);
            sendLog('warn', `Unknown entity kind: ${ent.kind}`, { source: 'factory.js' });
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
        case 'image':
            return updateImage(mesh, ent, prev);
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
        case 'Hyperbola':
            return updateHyperbola(mesh, ent, prev);
        case 'Parabola':
            return updateParabola(mesh, ent, prev);
        case 'Ellipse':
            return updateEllipse(mesh, ent, prev);
        case 'Circle':
            return updateCircle(mesh, ent, prev);
        case 'LinePair':
        case 'ParallelLinePair':
            return updateLinePair(mesh, ent, prev);
        case 'PlanePair':
        case 'ParallelPlanePair':
            return updatePlanePair(mesh, ent, prev);
        case 'PlaneConic':
        case 'PlaneConicPair':
        case 'Curve':
            return updateCurve(mesh, ent, prev);
        case 'PointSet':
            return updatePointSet(mesh, ent, prev);
        case 'Cone':
            return updateCone(mesh, ent, prev);
        case 'Frustum':
            // Corners/apex are structural; always rebuild (a one-shot entity).
            return false;
        default:
            break;
    }

    // Placement now rides on the node transform (the `transform` aspect), so the
    // generic in-place path only applies the cheap style fields; anything
    // structural (content fields, non-color/opacity style) triggers a rebuild.
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

