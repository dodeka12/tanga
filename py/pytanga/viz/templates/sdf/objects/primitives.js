// Per-primitive-kind GLSL emitters.
//
// Each entry maps the serialized node `kind` (shared with Python
// `sdf/primitives.py`) to a function returning the GLSL call string from the
// node's local-space point expression `p` and its typed `params`.

import { floatParam } from './transform.js';

const vec3 = (v) => `vec3(${floatParam(v[0])}, ${floatParam(v[1])}, ${floatParam(v[2])})`;
const vec2 = (v) => `vec2(${floatParam(v[0])}, ${floatParam(v[1])})`;

export function emitPrimitive(node, p) {
    const params = node.params || {};
    switch (node.kind) {
        case 'sphere':
            return `sdSphere(${p}, ${floatParam(params.radius)})`;
        case 'box':
            return `sdBox(${p}, ${vec3(params.halfExtents)})`;
        case 'roundBox':
            return `sdRoundBox(${p}, ${vec3(params.halfExtents)}, ${floatParam(params.radius)})`;
        case 'cylinder':
            return `sdCylinder(${p}, ${floatParam(params.radius)})`;
        case 'cappedCylinder':
            return `sdCappedCylinder(${p}, ${floatParam(params.halfHeight)}, ${floatParam(params.radius)})`;
        case 'torus':
            return `sdTorus(${p}, ${vec2([params.mainRadius, params.tubeRadius])})`;
        case 'cone':
            return `sdCone(${p}, ${floatParam(params.angle)})`;
        case 'cappedCone':
            return `sdCappedCone(${p}, ${floatParam(params.halfHeight)}, ${floatParam(params.radius1)}, ${floatParam(params.radius2)})`;
        case 'ellipsoid':
            return `sdEllipsoid(${p}, ${vec3(params.radii)})`;
        case 'capsule':
            return `sdCapsule(${p}, ${vec3(params.a)}, ${vec3(params.b)}, ${floatParam(params.radiusA)}, ${floatParam(params.radiusB)})`;
        case 'segment':
            return `sdSegment(${p}, ${vec3(params.a)}, ${vec3(params.b)})`;
        case 'plane':
            return `sdPlane(${p}, ${vec3(params.normal)}, ${floatParam(params.offset)})`;
        default:
            throw new Error(`Unknown SDF primitive kind: ${node.kind}`);
    }
}