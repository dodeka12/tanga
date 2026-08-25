// Headless smoke check for the per-object SDF proxy shader assembly (Phase 3).
//
// Imports the pure proxy assembly + lighting modules and asserts they emit
// well-formed GLSL for a single-object `float map()`. Run with:
//   node dev/src/sdf_proxy_smoke.mjs

import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import {
    buildProxyFragment,
    buildProxyVertex,
} from '../../py/pytanga/viz/templates/renderers/sdf/glsl.js';
import {
    DEFAULT_LIGHTING,
    parseHexColor,
    parseLighting,
} from '../../py/pytanga/viz/templates/renderers/sdf/lighting.js';

const here = dirname(fileURLToPath(import.meta.url));
const templates = join(here, '..', '..', 'py', 'pytanga', 'viz', 'templates');
const read = (p) => readFileSync(join(templates, p), 'utf8');

const parts = {
    common: read('sdf/shaders/sdf_common.glsl'),
    primitives: read('sdf/shaders/primitives.glsl'),
    combinators: read('sdf/shaders/combinators.glsl'),
    proxy: read('renderers/sdf/proxy.glsl'),
};

function assert(cond, msg) {
    if (!cond) {
        console.error('FAIL:', msg);
        process.exit(1);
    }
}

const ent = {
    id: 's',
    sdfKind: 'Sphere',
    tree: { kind: 'sphere', params: { radius: 1.0 } },
};

const frag = buildProxyFragment(ent, parts);
assert((frag.match(/void main/g) || []).length === 1, 'fragment has exactly one main');
assert(frag.includes('float map(vec3 p)'), 'fragment declares float map');
assert(frag.includes('sdSphere('), 'map emits the sphere tree');
// Examine code lines only (the header comment mentions `gl_FragColor`).
const fragCode = frag.split('\n').filter((ln) => !ln.trim().startsWith('//')).join('\n');
assert(fragCode.includes('out vec4'), 'fragment declares out vec4');
assert(!fragCode.includes('gl_FragColor'), 'no legacy gl_FragColor');
assert(frag.includes('gl_FragDepth'), 'writes gl_FragDepth');
assert(frag.includes('uniform vec3 uColor'), 'declares uColor');
assert(frag.includes('uniform float uOpacity'), 'declares uOpacity');
assert(frag.includes('uniform int uMaxSteps'), 'declares uMaxSteps');
assert(frag.includes('uniform float uSoftShadows'), 'declares uSoftShadows');
assert(frag.includes('uniform vec3 uBoundHalf'), 'declares uBoundHalf');
assert(!fragCode.includes('#version'), 'no #version directive');
assert(!fragCode.includes('precision'), 'no precision directive');

const vert = buildProxyVertex();
assert(vert.includes('vLocalPos'), 'vertex passes local position');
assert(vert.includes('vCameraLocal'), 'vertex passes local camera');
assert(vert.includes('inverse(modelMatrix)'), 'vertex computes local camera');
assert(vert.includes('gl_Position'), 'vertex writes gl_Position');

const [r, g, b] = parseHexColor('#ff0000');
assert(r === 1 && g === 0 && b === 0, 'parseHexColor parses red');
const lt = parseLighting(DEFAULT_LIGHTING);
assert(lt.lights.length === 1, 'default lighting has one light');
assert(lt.ambient[0] === 0.45 && lt.ambient[1] === 0.45 && lt.ambient[2] === 0.45, 'ambient parsed');

// ── SDF group fold ──────────────────────────────────────────
const group = {
    id: 'g',
    sdfKind: 'SdfGroup',
    tree: {
        kind: 'group',
        children: [
            { kind: 'sphere', params: { radius: 1.0 }, combine: 'union' },
            { kind: 'cappedCylinder', params: { halfHeight: 0.6, radius: 0.4 }, combine: 'subtract' },
            { kind: 'box', params: { halfExtents: [0.5, 0.5, 0.5] }, combine: 'intersection' },
        ],
    },
    members: [
        { transform: { position: [0, 0, 0], rotation: [0, 0, 0], scale: [1, 1, 1] }, bound: { min: [-1, -1, -1], max: [1, 1, 1] } },
        { transform: { position: [1, 0, 0], rotation: [0, 0, 0], scale: [1, 1, 1] }, bound: { min: [-1, -1, -1], max: [1, 1, 1] } },
        { transform: { position: [0, 0, 0], rotation: [0, 0, 0], scale: [1, 1, 1] }, bound: { min: [-1, -1, -1], max: [1, 1, 1] } },
    ],
};

const groupFrag = buildProxyFragment(group, parts);
assert(groupFrag.includes('float member0(vec3 p)'), 'group emits member0');
assert(groupFrag.includes('float member1(vec3 p)'), 'group emits member1');
assert(groupFrag.includes('float member2(vec3 p)'), 'group emits member2');
assert(groupFrag.includes('uniform mat4 uMemberInvTransform[MAX_GROUP_MEMBERS]'), 'group declares member transform array');
assert(groupFrag.includes('opUnion(d, d0)'), 'group folds member0 as union');
assert(groupFrag.includes('opSubtract(d, d1)'), 'group folds member1 as subtract');
assert(groupFrag.includes('opIntersect(d, d2)'), 'group folds member2 as intersection');
assert(groupFrag.includes('uMemberInvTransform[0]'), 'group applies member0 transform');
assert((groupFrag.match(/void main/g) || []).length === 1, 'group fragment has exactly one main');
assert(!groupFrag.includes('emitTree('), 'group fragment has no stray emitter');

console.log('OK: SDF proxy shader / lighting smoke');
