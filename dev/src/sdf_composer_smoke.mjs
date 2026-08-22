// Headless smoke check for the SDF composer + scene-builder + material table.
//
// Imports the SDF template ESM modules and asserts they emit well-formed GLSL
// for the analytic entity trees. Run with: node dev/src/sdf_composer_smoke.mjs

import { composeObjects } from '../../py/pytanga/viz/templates/sdf/composer.js';
import { buildObjectExpr } from '../../py/pytanga/viz/templates/sdf/scene-builder.js';
import { floatParam } from '../../py/pytanga/viz/templates/sdf/objects/transform.js';
import {
    buildMaterialRows,
    materialColorSrc,
    materialPreamble,
    padMaterialRows,
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

// GLSL ES 3.0 has no implicit int → float conversion, so float params must be
// emitted with a `.0` suffix (an integral `3` is an int literal).
assert(floatParam(3) === '3.0', 'floatParam appends .0 to integral values');
assert(floatParam(0.08) === '0.08', 'floatParam keeps decimals');
assert(floatParam(-1.5) === '-1.5', 'floatParam keeps negative decimals');
assert(lineExpr.includes('2.0, 0.05'), 'line params are float literals');
assert(sphereExpr.includes('), 1.0)'), 'sphere radius is a float literal');
assert(!sphereExpr.includes('), 1)'), 'no int literal passed to sdSphere');

const composed = composeObjects([line, sphere]);
assert(composed.includes('vec2 map(vec3 p)'), 'composes a vec2 map');
assert(composed.includes('d0'), 'includes object 0 distance');
assert(composed.includes('d1'), 'includes object 1 distance');

// Combine-mode fold: subtract carves with max(acc, -d) (material unchanged);
// intersection caps with max(acc, d) (outer surface's material wins).
const carved = composeObjects([
    sphere,
    { id: 'carve', combine: 'subtract', tree: { kind: 'sphere', params: { radius: 0.8 } } },
]);
assert(carved.includes('max(d, -d1)'), 'subtract folds as max(acc, -d)');
assert(!/if \(d1 < d\)/.test(carved), 'subtract object does not use the union fold');

const intersected = composeObjects([
    sphere,
    { id: 'cap', combine: 'intersection', tree: { kind: 'sphere', params: { radius: 0.5 } } },
]);
assert(intersected.includes('if (d1 > d)'), 'intersection folds as max(acc, d)');

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
const padded = padMaterialRows(rows);
assert(padded.length === 64, 'material rows padded to MAX_SDF_OBJECTS capacity');
assert(padded[63][0] === 0 && padded[63][3] === 0, 'padding row is transparent black');
assert(materialPreamble.includes('uMaterial'), 'material preamble declares array');
assert(materialColorSrc.includes('materialColor'), 'material sampler present');

console.log('OK: SDF composer / scene-builder / material-table smoke');