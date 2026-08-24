// Algebra leaf expression emitter (Phase 8).
//
// Emits the `evalPoint → M·a → distOf` algebra leaves *inside* the single
// composed `map()`: each `mv_sdf` object becomes a `dist_mv_<i>` function that
// embeds the point, multiplies by the object's packed `M` matrix (from the
// vec4-packed `u_M[]` uniform), applies the active distance function, and scales
// by the per-object `u_ObjectParams[i].x` calibration factor. An optional
// `bound` clips infinite entities via `opIntersect` with an `sdBox`.
//
// Because the result vector is the *full* algebra (ascending blade ids), the
// distance functions are instantiated per distinct algebra with that algebra's
// `NR`/`SLOT_PSEUDO` constants substituted in, so `scalar_pseudo` reads the
// scalar at slot 0 and the pseudoscalar at slot NR-1 for every algebra.

import { distanceFuncs } from './distances.js';
import { embedFuncs } from './embeds.js';
import { MAX_SDF_OBJECTS } from '../material-table.js';
import { floatParam } from '../objects/transform.js';

// Flat u_M capacity (floats). Each `mv_sdf` contributes NR*NP floats (e.g.
// 224 for pga3, 24 for e3). Past this threshold, escalate to a data texture
// (see README "texture escalation" / "algebra-leaf uniform budget").
export const MAX_MV_FLOATS = 1024;

function pascalCase(name) {
    return name.split('_').map((s) => s.charAt(0).toUpperCase() + s.slice(1)).join('');
}

export function distFnName(name) {
    return 'distOf' + pascalCase(name);
}

export function algebraSuffix(algebra) {
    return String(algebra).toUpperCase();
}

// ── Layout (offset/stride per mv_sdf object) ──────────────

export function mvLayout(objects) {
    let cursor = 0;
    const infos = objects.map((obj, index) => {
        if (!obj || obj.sdfKind !== 'mv_sdf') return null;
        const entry = embedFuncs.get(obj.algebra);
        if (!entry) throw new Error(`No embedding registered for algebra '${obj.algebra}'`);
        const info = {
            index,
            algebra: obj.algebra,
            np: entry.NP,
            nr: entry.NR,
            slotPseudo: entry.SLOT_PSEUDO,
            offset: cursor,
        };
        cursor += entry.NP * entry.NR;
        if (cursor > MAX_MV_FLOATS) {
            throw new Error(`mv_sdf matrix budget exceeded (${cursor} > ${MAX_MV_FLOATS})`);
        }
        return info;
    });
    return { infos, totalFloats: cursor };
}

export function distinctEmbedSrcs(objects) {
    const seen = new Set();
    const srcs = [];
    for (const obj of objects) {
        if (!obj || obj.sdfKind !== 'mv_sdf') continue;
        if (seen.has(obj.algebra)) continue;
        seen.add(obj.algebra);
        const entry = embedFuncs.get(obj.algebra);
        srcs.push(entry.snippet);
    }
    return srcs;
}

export function matrixUniformDecls(totalFloats) {
    // Pack the flat M matrices into vec4s (4 floats each) and all per-object
    // scalars into a single vec4 array: ANGLE/D3D drivers count every *float* of
    // a scalar uniform array as one full vec4 slot, so float arrays blow the
    // GL_MAX_FRAGMENT_UNIFORM_VECTORS budget very fast.
    const vec4Count = Math.ceil(Math.max(totalFloats || 0, 1) / 4);
    return `
uniform vec4 u_M[${vec4Count}];
uniform vec4 u_ObjectParams[${MAX_SDF_OBJECTS}];
`;
}

// ── Distance-function instantiation (per distinct algebra) ──

function instantiateDist(name, nr, slotPseudo, suffix) {
    const base = distanceFuncs.get(name);
    if (!base) throw new Error(`Unknown distance function '${name}'`);
    const fn = distFnName(name);
    let src = base.snippet;
    // Replace the bare `NR` token (array size in `r[NR]` *and* the loop bound
    // `i < NR`) and the `SLOT_PSEUDO` constant with the algebra's values.
    src = src.replaceAll('NR', String(nr)).replaceAll('SLOT_PSEUDO', String(slotPseudo));
    src = src.replace(fn, fn + '_' + suffix);
    if (name === 'grade') {
        src = src.replace('gradeNorm(r', `gradeNorm_${suffix}(r`);
    }
    return src;
}

function gradeNormSrc(nr, suffix) {
    return `
float gradeNorm_${suffix}(in float r[${nr}], int k) {
    float s = 0.0;
    for (int i = 0; i < ${nr}; i++) {
        if (bitCount(i) == k) s += r[i] * r[i];
    }
    return sqrt(s);
}`;
}

export function emitDistanceFunctions(objects, activeDistance) {
    const seen = new Set();
    const parts = [];
    for (const obj of objects) {
        if (!obj || obj.sdfKind !== 'mv_sdf') continue;
        if (seen.has(obj.algebra)) continue;
        seen.add(obj.algebra);
        const entry = embedFuncs.get(obj.algebra);
        const suffix = algebraSuffix(obj.algebra);
        if (activeDistance === 'grade') {
            parts.push(gradeNormSrc(entry.NR, suffix));
        }
        parts.push(instantiateDist(activeDistance, entry.NR, entry.SLOT_PSEUDO, suffix));
    }
    return parts.join('\n');
}


// ── Leaf emission ────────────────────────────────────────

export function distCall(activeDistance, algebra, resultVar = 'r') {
    const fn = distFnName(activeDistance) + '_' + algebraSuffix(algebra);
    if (activeDistance === 'grade') return `${fn}(${resultVar}, 1)`;
    if (activeDistance === 'component') return `${fn}(${resultVar}, 0)`;
    return `${fn}(${resultVar})`;
}

export function emitAlgebraLeaf(obj, info, activeDistance) {
    const { index, algebra, np, nr, offset } = info;
    const embedFn = `evalPoint${algebraSuffix(algebra)}`;
    const lines = [
        `float dist_mv_${index}(vec3 p) {`,
        `    float a[${np}]; ${embedFn}(p, a);`,
        `    float r[${nr}];`,
    ];
    for (let j = 0; j < nr; j++) {
        const terms = [];
        for (let k = 0; k < np; k++) {
            const slot = offset + j * np + k;
            terms.push(`u_M[${slot >> 2}][${slot & 3}] * a[${k}]`);
        }
        lines.push(`    r[${j}] = ${terms.join(' + ')};`);
    }
    const distExpr = `${distCall(activeDistance, algebra)} * u_ObjectParams[${index}].x - u_ObjectParams[${index}].y`;
    if (obj.bound && obj.bound.halfExtents) {
        const he = obj.bound.halfExtents;
        const box = `sdBox(p, vec3(${floatParam(he[0])}, ${floatParam(he[1])}, ${floatParam(he[2])}))`;
        lines.push(`    return opIntersect(${distExpr}, ${box});`);
    } else {
        lines.push(`    return ${distExpr};`);
    }
    lines.push('}');
    return lines.join('\n');
}

export function emitAlgebraLeaves(objects, activeDistance) {
    const { infos } = mvLayout(objects);
    const out = [];
    infos.forEach((info) => {
        if (info) out.push(emitAlgebraLeaf(objects[info.index], info, activeDistance));
    });
    return out.join('\n');
}

// ── Uniform packing ──────────────────────────────────────

export function buildAlgebraUniforms(objects) {
    const { infos, totalFloats } = mvLayout(objects);
    // u_M is packed into vec4 slots (padded to a multiple of 4).
    const vec4Count = Math.ceil(Math.max(totalFloats, 1) / 4);
    const uM = new Float32Array(vec4Count * 4);
    // vec4 per object: (scale, thickness, falloff, max_distance); w = -1 marks
    // a non-algebraic (analytic) object.
    const uObjectParams = new Float32Array(MAX_SDF_OBJECTS * 4);
    for (let i = 0; i < MAX_SDF_OBJECTS; i++) {
        uObjectParams[i * 4 + 3] = -1.0;
    }
    infos.forEach((info) => {
        if (!info) return;
        const obj = objects[info.index];
        const M = obj.M || [];
        const stride = info.np * info.nr;
        for (let i = 0; i < stride; i++) {
            uM[info.offset + i] = (typeof M[i] === 'number') ? M[i] : 0.0;
        }
        const base = info.index * 4;
        uObjectParams[base + 0] = (typeof obj.scale === 'number') ? obj.scale : 1.0;
        uObjectParams[base + 1] = (typeof obj.thickness === 'number') ? obj.thickness : 0.0;
        uObjectParams[base + 2] = (typeof obj.falloff === 'number') ? obj.falloff : 0.0;
        uObjectParams[base + 3] = (typeof obj.max_distance === 'number') ? obj.max_distance : 0.0;
    });
    return { uM, uObjectParams, totalFloats };
}
