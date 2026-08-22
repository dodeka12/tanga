// Headless smoke check for the SDF composer + scene-builder + material table.
//
// Imports the SDF template ESM modules and asserts they emit well-formed GLSL
// for the analytic entity trees. Run with: node dev/src/sdf_composer_smoke.mjs

import { composeObjects } from '../../py/pytanga/viz/templates/sdf/composer.js';
import { buildObjectExpr } from '../../py/pytanga/viz/templates/sdf/scene-builder.js';
import {
    buildMaterialRows,
    materialColorSrc,
    materialPreamble,
} from '../../py/pytanga/viz/templates/sdf/material-table.js';

function assert(cond, msg) {
    if (!cond) {
        console.error('FAIL:', msg);
        process.exit(1);
    }
}

// A line + a sphere, as the Python serializer would emit them.
const line = {
    id: 'line',
    tree: {
        kind: 'cappedCylinder',
        params: { halfHeight: 2.0, radius: 0.05 },
        transform: { position: [0, 0, 2] },
    },
};
const sphere = {
    id: 'sphere',
    tree: { kind: 'sphere', params: { radius: 1.0 }, transform: { position: [0, 0, 0] } },
};

const lineExpr = buildObjectExpr(line);
const sphereExpr = buildObjectExpr(sphere);
assert(lineExpr.includes('sdCappedCylinder'), 'line emits capped cylinder');
assert(sphereExpr.includes('sdSphere'), 'sphere emits sphere');

const composed = composeObjects([line, sphere]);
assert(composed.includes('vec2 map(vec3 p)'), 'composes a vec2 map');
assert(composed.includes('d0'), 'includes object 0 distance');
assert(composed.includes('d1'), 'includes object 1 distance');

// A nested combinator (infinite line = intersect(cappedCylinder, box)).
const infiniteLine = {
    id: 'inf',
    tree: {
        kind: 'intersect',
        children: [
            { kind: 'cappedCylinder', params: { halfHeight: 2.0, radius: 0.05 } },
            { kind: 'box', params: { halfExtents: [2, 2, 2] } },
        ],
    },
};
const infExpr = buildObjectExpr(infiniteLine);
assert(infExpr.includes('opIntersect'), 'nested tree uses opIntersect');

const rows = buildMaterialRows([line, sphere]);
assert(rows.length === 2, 'two material rows');
assert(materialPreamble.includes('uMaterial'), 'material preamble declares array');
assert(materialColorSrc.includes('materialColor'), 'material sampler present');

console.log('OK: SDF composer / scene-builder / material-table smoke');