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
        default:
            throw new Error(`Unknown SDF primitive kind: ${node.kind}`);
    }
}