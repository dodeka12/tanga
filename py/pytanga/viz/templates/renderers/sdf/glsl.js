// Pure GLSL assembly for the per-object SDF proxy shader (no three.js / DOM).
//
// The proxy marches a *single* object's local-space SDF inside a bounding-box
// proxy mesh. `map()` returns `vec2(distance, materialIndex)` so grouped
// objects can shade each member with its own material; single objects use
// material slot 0 (index is always 0.0).

import { emitTree } from '../../sdf/objects/combinators.js';
import { lightPreamble } from './lighting.js';

// Compile-time march cap. `uMaxSteps` clamps the loop at runtime so lowering
// the budget does not require a shader recompile.
export const MAX_STEPS = 256;

// Compile-time cap on the number of members in an `SdfGroup`. The fold is
// unrolled per group, so this only sizes the uniform array (padded slots are
// identity and never read).
export const MAX_GROUP_MEMBERS = 16;

// Smooth-blend radius default for the `smooth_*` fold modes (matches
// `sdf/composer.js`). A member with no explicit `smoothness` uses this.
const GROUP_SMOOTHNESS_DEFAULT = 0.1;

function _groupSmoothness(child) {
    const k = Number(
        child.smoothness != null ? child.smoothness : GROUP_SMOOTHNESS_DEFAULT,
    );
    return Number.isFinite(k) ? k : GROUP_SMOOTHNESS_DEFAULT;
}

export function buildProxyVertex() {
    return `
out vec3 vLocalPos;
flat out vec3 vCameraLocal;

void main() {
    vLocalPos = position;
    // Camera position in the mesh's local space (same for every vertex).
    vCameraLocal = (inverse(modelMatrix) * vec4(cameraPosition, 1.0)).xyz;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
`;
}

// Fold an `SdfGroup`'s members into a single `float map(vec3 p)`. Each member
// is wrapped as `float memberI(vec3 p)` (its local-space tree) and folded with
// its combine mode; the member's runtime transform is applied via the
// `uMemberInvTransform[i]` uniform (inverse transform: point → member local).
function buildGroupMap(ent) {
    const children = (ent.tree && ent.tree.children) || [];
    const hasTransforms = !!ent.members;
    const lines = [];
    children.forEach((child, i) => {
        lines.push(`float member${i}(vec3 p) {`);
        lines.push(`    return ${emitTree(child)};`);
        lines.push('}');
    });
    lines.push('vec2 map(vec3 p) {');
    lines.push('    float d = MAX_DIST;');
    lines.push('    float m = 0.0;');
    children.forEach((child, i) => {
        const combine = (child.combine || 'union').toLowerCase();
        const k = _groupSmoothness(child);
        const local = hasTransforms
            ? `(uMemberInvTransform[${i}] * vec4(p, 1.0)).xyz`
            : 'p';
        lines.push(`    float d${i} = member${i}(${local});`);
        if (combine === 'subtract') {
            // The cut contributes no material; the material stays with `d`.
            lines.push(`    d = opSubtract(d, d${i});`);
        } else if (combine === 'intersection') {
            lines.push(`    if (d${i} > d) m = ${i}.0;`);
            lines.push(`    d = opIntersect(d, d${i});`);
        } else if (combine === 'xor') {
            lines.push(`    if (d${i} < d) m = ${i}.0;`);
            lines.push(`    d = opXor(d, d${i});`);
        } else if (combine === 'smooth_subtract') {
            // The cut contributes no material; the material stays with `d`.
            lines.push(`    vec2 sm${i} = opSmoothSubtract(d, d${i}, ${k});`);
            lines.push(`    d = sm${i}.x;`);
        } else if (combine === 'smooth_intersection') {
            lines.push(`    vec2 sm${i} = opSmoothIntersect(d, d${i}, ${k});`);
            lines.push(`    d = sm${i}.x;`);
            lines.push(`    m = mix(${i}.0, m, sm${i}.y);`);
        } else if (combine === 'smooth_union') {
            lines.push(`    vec2 sm${i} = opSmoothUnion(d, d${i}, ${k});`);
            lines.push(`    d = sm${i}.x;`);
            lines.push(`    m = mix(${i}.0, m, sm${i}.y);`);
        } else {
            lines.push(`    if (d${i} < d) m = ${i}.0;`);
            lines.push(`    d = opUnion(d, d${i});`);
        }
    });
    lines.push('    return vec2(d, m);');
    lines.push('}');
    return lines.join('\n');
}

// Assemble the proxy fragment from the fetched shader parts + the entity's
// single-object tree. `shaderParts` = { common, primitives, combinators, proxy }.
export function buildProxyFragment(ent, shaderParts) {
    const { common, primitives, combinators, proxy } = shaderParts;
    const isGroup = !!(ent.tree && ent.tree.kind === 'group');

    const mapSrc = isGroup
        ? buildGroupMap(ent)
        : `vec2 map(vec3 p) {
    return vec2(${emitTree(ent.tree)}, 0.0);
}`;

    // `MAX_GROUP_MEMBERS` is sized once here; the `uMaterial` uniform itself is
    // declared in `proxy.glsl` (single source, no redefinition).
    const materialPreamble = `const int MAX_GROUP_MEMBERS = ${MAX_GROUP_MEMBERS};`;

    const transformPreamble = isGroup
        ? `uniform mat4 uMemberInvTransform[MAX_GROUP_MEMBERS];`
        : '';

    const parts = [
        common,
        primitives,
        combinators,
        lightPreamble,
        `const int MAX_STEPS = ${MAX_STEPS};`,
        materialPreamble,
        transformPreamble,
        mapSrc,
        proxy,
    ];
    return parts.filter((s) => s !== '').join('\n');
}
