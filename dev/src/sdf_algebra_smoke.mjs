// Headless smoke check for the algebra SDF leaf emitter (Phase 8).
//
// Imports the SDF algebra ESM modules and asserts they emit well-formed GLSL
// for `mv_sdf` objects, instantiate distance functions per algebra, pack the
// flat `u_M` uniform, and fold leaves into the single composed `map()` with no
// algebra/distance/entity branching. Run with:
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
    MAX_MV_FLOATS,
} from '../../py/pytanga/viz/templates/sdf/algebra/eval.js';

function assert(cond, msg) {
    if (!cond) {
        console.error('FAIL:', msg);
        process.exit(1);
    }
}

// An e3 mv_sdf object with a 24-float M (8 result blades x 3 point blades).
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
assert(leaf.includes('float dist_mv_0(vec3 p)'), 'leaf named dist_mv_0');
assert(leaf.includes('evalPointE3(p, a)'), 'leaf calls evalPointE3');
assert(leaf.includes('float r[8]'), 'e3 result vector is 8');
assert(leaf.includes('distOfScalarPseudo_E3(r) * u_Scale[0]'), 'leaf calls per-algebra distOf');
assert(leaf.includes('opIntersect'), 'bound clips via opIntersect');
assert(leaf.includes('sdBox(p, vec3(10.0, 10.0, 10.0))'), 'bound uses sdBox');
assert(leaf.includes('u_M[23] * a[2]'), 'last matmul term indexed correctly');

const dists = emitDistanceFunctions([e3plane], 'scalar_pseudo');
assert(dists.includes('distOfScalarPseudo_E3(in float r[8])'), 'distance instantiated per algebra');
assert(!dists.includes('SLOT_PSEUDO'), 'SLOT_PSEUDO token substituted away');
assert(dists.includes('r[7]'), 'SLOT_PSEUDO becomes 7 for e3');

const embeds = distinctEmbedSrcs([e3plane]);
assert(embeds.length === 1, 'one distinct embed for a single e3 object');
assert(embeds[0].includes('evalPointE3'), 'embed source defines evalPointE3');

const expr = buildObjectExpr(e3plane, 0);
assert(expr === 'dist_mv_0(p)', 'scene-builder delegates mv_sdf to its leaf');

const composed = composeObjects([e3plane]);
assert(composed.includes('dist_mv_0(p)'), 'composed map calls the algebra leaf');
assert(composed.includes('vec2 map(vec3 p)'), 'still a single composed map');

const fragment = [embeds[0], matrixUniformDecls(), dists, leaf, composed].join('\n');
assert(!/if\s*\(\s*algebra\s*==/.test(fragment), 'no algebra branching');
assert(!/if\s*\(\s*distance\s*==/.test(fragment), 'no distance branching');
assert(!/if\s*\(\s*entity\s*==/.test(fragment), 'no entity branching');

const { uM, uScale } = buildAlgebraUniforms([e3plane]);
assert(uM.length === MAX_MV_FLOATS, 'uM padded to capacity');
assert(uM[0] === 1 && uM[23] === 24, 'M packed row-major');
assert(uScale[0] === 1.0, 'scale default 1.0');

// Mixed-algebra scene: two distinct embeds + two distinct distOf instances.
const pga3point = {
    id: 'pga3point',
    sdfKind: 'mv_sdf',
    algebra: 'pga3',
    M: Array.from({ length: 224 }, () => 0.0),
    scale: 1.0,
};
const mixedLeaves = emitAlgebraLeaves([e3plane, pga3point], 'scalar_pseudo');
assert(mixedLeaves.includes('dist_mv_0') && mixedLeaves.includes('dist_mv_1'), 'both leaves emitted');
assert(mixedLeaves.includes('evalPointPGA3'), 'pga3 embed emitted');
const mixedDists = emitDistanceFunctions([e3plane, pga3point], 'scalar_pseudo');
assert(mixedDists.includes('distOfScalarPseudo_E3'), 'e3 distance present');
assert(mixedDists.includes('distOfScalarPseudo_PGA3'), 'pga3 distance present');
assert(mixedDists.includes('r[32]'), 'pga3 result vector is 32');
const mixedLayout = mvLayout([e3plane, pga3point]);
assert(mixedLayout.infos[0].offset === 0, 'e3 offset 0');
assert(mixedLayout.infos[1].offset === 24, 'pga3 offset after e3');
assert(mixedLayout.totalFloats === 24 + 224, 'total floats summed');

// `grade`/`component` distance functions instantiate with default params.
const gradeDists = emitDistanceFunctions([e3plane], 'grade');
assert(gradeDists.includes('gradeNorm_E3'), 'gradeNorm emitted for grade');
assert(gradeDists.includes('distOfGrade_E3(in float r[8], int k)'), 'grade instantiated');
const gradeLeaf = emitAlgebraLeaves([e3plane], 'grade');
assert(gradeLeaf.includes('distOfGrade_E3(r, 1)'), 'grade leaf passes default k=1');

console.log('OK: SDF algebra leaf emitter smoke');
