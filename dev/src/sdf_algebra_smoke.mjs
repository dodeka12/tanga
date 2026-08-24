// Headless smoke check for the algebra SDF leaf emitter (Phase 8, Phase 13).
//
// Imports the SDF algebra ESM modules and asserts they emit well-formed GLSL
// for `mv_sdf` objects, instantiate distance functions per distinct result mask,
// pack the flat `u_M` uniform, return `vec2(d, scale·|∇d|)` from each leaf, and
// fold leaves into the single composed `map()` with no algebra/distance/entity
// branching. Run with:
//   node dev/src/sdf_algebra_smoke.mjs

import { composeObjects } from '../../py/pytanga/viz/templates/sdf/composer.js';
import { buildObjectExpr } from '../../py/pytanga/viz/templates/sdf/scene-builder.js';
import {
    mvLayout,
    distinctEmbedSrcs,
    matrixUniformDecls,
    emitDistanceFunctions,
    emitAlgebraLeaves,
    buildAlgebraUniforms,
} from '../../py/pytanga/viz/templates/sdf/algebra/eval.js';

function assert(cond, msg) {
    if (!cond) {
        console.error('FAIL:', msg);
        process.exit(1);
    }
}

// An e3 mv_sdf object with an active 8-blade result mask (8 result x 3 point).
const e3plane = {
    id: 'e3plane',
    sdfKind: 'mv_sdf',
    algebra: 'e3',
    product: 'op',
    distance: 'scalar_pseudo',
    normalize: true,
    point_ids: [1, 2, 4],
    result_ids: [0, 1, 2, 3, 4, 5, 6, 7],
    slot_pseudo: 7,
    M: Array.from({ length: 24 }, (_, i) => i + 1),
    scale: 1.0,
    bound: { halfExtents: [10, 10, 10] },
};

const layout = mvLayout([e3plane]);
assert(layout.totalFloats === 24, 'e3 stride is 24 floats');
assert(layout.infos[0].offset === 0, 'first object offset 0');
assert(layout.infos[0].np === 3 && layout.infos[0].nr === 8, 'e3 NP=3 NR=8');

const leaf = emitAlgebraLeaves([e3plane], 'scalar_pseudo');
assert(leaf.includes('vec2 dist_mv_0(vec3 p)'), 'leaf named dist_mv_0 and returns vec2');
assert(leaf.includes('evalPointE3(p, a)'), 'leaf calls evalPointE3');
assert(leaf.includes('float r[8]'), 'e3 result vector is 8');
assert(leaf.includes('distOfScalarPseudo_0(r) * u_ObjectParams[0].x'), 'leaf calls per-mask distOf');
assert(leaf.includes('opIntersect'), 'bound clips via opIntersect');
assert(leaf.includes('sdBox(p, vec3(10.0, 10.0, 10.0))'), 'bound uses sdBox');
assert(leaf.includes('u_M[5][3] * a[2]'), 'last matmul term indexed correctly (vec4-packed)');
assert(leaf.includes('return vec2(d,'), 'leaf returns vec2(d, scale*|grad d|)');
assert(leaf.includes('inversesqrt(rest + float(rest < 1e-6) * 1e-6)'), 'branchless 1/sqrt guard present');
assert(!/if\s*\(\s*rest\s*</.test(leaf), 'no if (rest < eps) epsilon branch');

// thickness (per-object distance cutoff) is subtracted from the scaled distance
// and packed into u_ObjectParams.y.
const thickLeaf = emitAlgebraLeaves([{ ...e3plane, thickness: 0.1 }], 'scalar_pseudo');
assert(thickLeaf.includes('- u_ObjectParams[0].y'), 'thickness subtracted in the leaf');
const { uObjectParams: thickParams } = buildAlgebraUniforms([{ ...e3plane, thickness: 0.1 }]);
assert(Math.abs(thickParams[1] - 0.1) < 1e-6, 'thickness packed into u_ObjectParams.y');

const dists = emitDistanceFunctions([e3plane], 'scalar_pseudo');
assert(dists.includes('distOfScalarPseudo_0(in float r[8])'), 'distance instantiated per result mask');
assert(!dists.includes('SLOT_PSEUDO'), 'SLOT_PSEUDO token substituted away');
assert(dists.includes('r[7]'), 'SLOT_PSEUDO becomes 7 for e3');
assert(dists.includes('i < 8'), 'loop bound NR substituted');
assert(!dists.includes('NR'), 'no bare NR token remains');

const embeds = distinctEmbedSrcs([e3plane]);
assert(embeds.length === 1, 'one distinct embed for a single e3 object');
assert(embeds[0].includes('evalPointE3'), 'embed source defines evalPointE3');

const expr = buildObjectExpr(e3plane, 0);
assert(expr === 'dist_mv_0(p)', 'scene-builder delegates mv_sdf to its leaf');

const composed = composeObjects([e3plane]);
assert(composed.includes('dist_mv_0(p)'), 'composed map calls the algebra leaf');
// `vec3 map(vec3 p)` is asserted in sdf_composer_smoke.mjs (Part B4).

const fragment = [embeds[0], matrixUniformDecls(), dists, leaf, composed].join('\n');
assert(!/if\s*\(\s*algebra\s*==/.test(fragment), 'no algebra branching');
assert(!/if\s*\(\s*distance\s*==/.test(fragment), 'no distance branching');
assert(!/if\s*\(\s*entity\s*==/.test(fragment), 'no entity branching');

const { uM, uObjectParams, totalFloats } = buildAlgebraUniforms([e3plane]);
assert(totalFloats === 24, 'total floats for e3 plane is 24');
assert(uM.length === 24, 'uM sized to the actual total (vec4-padded), not a fixed capacity');
assert(uM[0] === 1 && uM[23] === 24, 'M packed row-major');
assert(uObjectParams[0] === 1.0, 'scale default 1.0 (u_ObjectParams.x)');
assert(uObjectParams[3] === 0.0, 'max_distance default 0.0 (u_ObjectParams.w)');
assert(!Array.from(uObjectParams).some((v) => v === -1.0), 'no -1 analytic sentinel fill');

// Mixed-algebra scene: two distinct embeds + two distinct per-mask distOf.
const pga3plane = {
    id: 'pga3plane',
    sdfKind: 'mv_sdf',
    algebra: 'pga3',
    point_ids: [7, 11, 13, 14, 19, 21, 22],
    result_ids: [0, 15, 23, 31],
    slot_pseudo: 3,
    M: Array.from({ length: 28 }, () => 0.0),
    scale: 1.0,
};
const mixedLeaves = emitAlgebraLeaves([e3plane, pga3plane], 'scalar_pseudo');
assert(mixedLeaves.includes('dist_mv_0') && mixedLeaves.includes('dist_mv_1'), 'both leaves emitted');
assert(mixedLeaves.includes('evalPointPGA3'), 'pga3 embed emitted');
const mixedDists = emitDistanceFunctions([e3plane, pga3plane], 'scalar_pseudo');
assert(mixedDists.includes('distOfScalarPseudo_0'), 'e3 mask distance present');
assert(mixedDists.includes('distOfScalarPseudo_1'), 'pga3 mask distance present');
assert(mixedDists.includes('r[4]'), 'pga3 result vector is 4 (active mask)');
const mixedLayout = mvLayout([e3plane, pga3plane]);
assert(mixedLayout.infos[0].offset === 0, 'e3 offset 0');
assert(mixedLayout.infos[1].offset === 24, 'pga3 offset after e3');
assert(mixedLayout.totalFloats === 24 + 28, 'total floats summed');

// `grade`/`component` distance functions instantiate with default params.
const gradeDists = emitDistanceFunctions([e3plane], 'grade');
assert(gradeDists.includes('gradeNorm_0'), 'gradeNorm emitted for grade');
assert(gradeDists.includes('distOfGrade_0(in float r[8], int k)'), 'grade instantiated');
assert(gradeDists.includes('RESULT_IDS_0[8] = int[](0, 1, 2, 3, 4, 5, 6, 7)'), 'gradeNorm carries the per-mask RESULT_IDS');
const gradeLeaf = emitAlgebraLeaves([e3plane], 'grade');
assert(gradeLeaf.includes('distOfGrade_0(r, 1)'), 'grade leaf passes default k=1');

console.log('OK: SDF algebra leaf emitter smoke');
