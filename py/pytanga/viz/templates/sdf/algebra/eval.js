// Algebra leaf expression emitter (Phase 8, analytical gradient in Phase 13).
//
// Emits the `evalPoint → M·a → distOf` algebra leaves *inside* the single
// composed `map()`: each `mv_sdf` object becomes a `dist_mv_<i>` function that
// embeds the point, multiplies by the object's packed `M` matrix (from the
// vec4-packed `u_M[]` uniform), applies the active distance function, and scales
// by the per-object `u_ObjectParams[i].x` calibration factor. An optional
// `bound` clips infinite entities via `opIntersect` with an `sdBox`.
//
// Phase 13: the result vector is the object's *active result mask* (the backend
// `result_ids`, scalar always at slot 0, pseudoscalar at `slot_pseudo`), so the
// distance functions are instantiated per distinct result mask with that mask's
// `NR`/`SLOT_PSEUDO` substituted. Each leaf also returns `vec2(d, g)` carrying
// the analytical gradient norm `g = scale·|∇d|` (distance-function derivative
// `g[k] = ∂D/∂r[k]`, transposed matvec `h = Mᵀg`, per-algebra point Jacobian).

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
    const maskFirst = new Map(); // mask key → first object index (stable suffix)
    const infos = objects.map((obj, index) => {
        if (!obj || obj.sdfKind !== 'mv_sdf') return null;
        const entry = embedFuncs.get(obj.algebra);
        if (!entry) throw new Error(`No embedding registered for algebra '${obj.algebra}'`);
        const ids = obj.result_ids || [];
        const key = ids.join(',');
        if (!maskFirst.has(key)) maskFirst.set(key, index);
        const info = {
            index,
            algebra: obj.algebra,
            np: entry.NP,
            nr: ids.length,
            slotPseudo: obj.slot_pseudo,
            resultIds: ids,
            maskKey: key,
            maskSuffix: String(maskFirst.get(key)),
            offset: cursor,
        };
        cursor += entry.NP * ids.length;
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

function gradeNormSrc(resultIds, nr, suffix) {
    const ids = resultIds.join(', ');
    return `
const int RESULT_IDS_${suffix}[${nr}] = int[](${ids});
float gradeNorm_${suffix}(in float r[${nr}], int k) {
    float s = 0.0;
    for (int i = 0; i < ${nr}; i++) {
        if (bitCount(RESULT_IDS_${suffix}[i]) == k) s += r[i] * r[i];
    }
    return sqrt(s);
}`;
}

export function emitDistanceFunctions(objects, activeDistance) {
    const { infos } = mvLayout(objects);
    const seen = new Set();
    const parts = [];
    for (const info of infos) {
        if (!info) continue;
        if (seen.has(info.maskKey)) continue;
        seen.add(info.maskKey);
        if (activeDistance === 'grade') {
            parts.push(gradeNormSrc(info.resultIds, info.nr, info.maskSuffix));
        }
        parts.push(instantiateDist(activeDistance, info.nr, info.slotPseudo, info.maskSuffix));
    }
    return parts.join('\n');
}


// ── Leaf emission ────────────────────────────────────────

export function distCall(activeDistance, maskSuffix, resultVar = 'r') {
    const fn = distFnName(activeDistance) + '_' + maskSuffix;
    if (activeDistance === 'grade') return `${fn}(${resultVar}, 1)`;
    if (activeDistance === 'component') return `${fn}(${resultVar}, 0)`;
    return `${fn}(${resultVar})`;
}

// Emit the `g[k] = ∂D/∂r[k]` derivative coefficients for the active distance
// function over the object's result mask. The `1/sqrt` denominators use a
// branchless guard (`inversesqrt(x + float(x < EPS_SQ) * EPS_SQ)`), never an
// `if (rest < eps)` branch.
function emitGradientCoeffs(distance, nr, slotPseudo, resultIds, suffix) {
    const lines = [`    float g[${nr}];`];
    if (distance === 'scalar_pseudo') {
        lines.push('    float rest = 0.0;');
        lines.push(`    for (int i = 0; i < ${nr}; i++) { if (i != 0 && i != ${slotPseudo}) rest += r[i] * r[i]; }`);
        lines.push('    float invRest = inversesqrt(rest + float(rest < 1e-6) * 1e-6);');
        lines.push('    g[0] = 1.0;');
        lines.push(`    g[${slotPseudo}] = 1.0;`);
        for (let k = 0; k < nr; k++) {
            if (k !== 0 && k !== slotPseudo) lines.push(`    g[${k}] = r[${k}] * invRest;`);
        }
    } else if (distance === 'magnitude') {
        lines.push('    float norm2 = 0.0;');
        lines.push(`    for (int i = 0; i < ${nr}; i++) norm2 += r[i] * r[i];`);
        lines.push('    float invNorm = inversesqrt(norm2 + float(norm2 < 1e-6) * 1e-6);');
        for (let k = 0; k < nr; k++) lines.push(`    g[${k}] = r[${k}] * invNorm;`);
    } else if (distance === 'grade') {
        lines.push('    float grade2 = 0.0;');
        lines.push(`    for (int i = 0; i < ${nr}; i++) { if (bitCount(RESULT_IDS_${suffix}[i]) == 1) grade2 += r[i] * r[i]; }`);
        lines.push('    float invGrade = inversesqrt(grade2 + float(grade2 < 1e-6) * 1e-6);');
        for (let k = 0; k < nr; k++) {
            lines.push(`    g[${k}] = (bitCount(RESULT_IDS_${suffix}[${k}]) == 1) ? r[${k}] * invGrade : 0.0;`);
        }
    } else {
        // scalar / component (default params select the scalar slot 0).
        lines.push('    g[0] = 1.0;');
        for (let k = 1; k < nr; k++) lines.push(`    g[${k}] = 0.0;`);
    }
    return lines;
}

export function emitAlgebraLeaf(obj, info, activeDistance) {
    const { index, algebra, np, nr, slotPseudo, offset, resultIds, maskSuffix } = info;
    const embedFn = `evalPoint${algebraSuffix(algebra)}`;
    const entry = embedFuncs.get(algebra);
    const lines = [
        `vec2 dist_mv_${index}(vec3 p) {`,
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
    const distExpr = `${distCall(activeDistance, maskSuffix)} * u_ObjectParams[${index}].x - u_ObjectParams[${index}].y`;
    if (obj.bound && obj.bound.halfExtents) {
        const he = obj.bound.halfExtents;
        const box = `sdBox(p, vec3(${floatParam(he[0])}, ${floatParam(he[1])}, ${floatParam(he[2])}))`;
        lines.push(`    float d = opIntersect(${distExpr}, ${box});`);
    } else {
        lines.push(`    float d = ${distExpr};`);
    }
    // Analytical gradient: g[k] = ∂D/∂r[k], h = Mᵀg, grad = Jᵀh, g = scale·|∇d|.
    lines.push(...emitGradientCoeffs(activeDistance, nr, slotPseudo, resultIds, maskSuffix));
    lines.push(`    float h[${np}];`);
    for (let m = 0; m < np; m++) {
        const terms = [];
        for (let k = 0; k < nr; k++) {
            const slot = offset + k * np + m;
            terms.push(`u_M[${slot >> 2}][${slot & 3}] * g[${k}]`);
        }
        lines.push(`    h[${m}] = ${terms.join(' + ')};`);
    }
    lines.push(`    ${entry.gradient}`);
    lines.push(`    return vec2(d, u_ObjectParams[${index}].x * length(grad));`);
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
    // vec4 per object: (scale, thickness, falloff, max_distance). Analytic
    // objects stay (0, 0, 0, 0): falloff 0 → no density; max_distance is unused.
    const uObjectParams = new Float32Array(MAX_SDF_OBJECTS * 4);
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
