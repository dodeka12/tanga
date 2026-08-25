// Pure GLSL assembly for the per-object SDF proxy shader (no three.js / DOM).
//
// The proxy marches a *single* object's local-space SDF inside a bounding-box
// proxy mesh, replacing the fullscreen viewer's global `vec2 map()` fold and
// material table with a `float map(vec3 p)` and a single `uColor`/`uOpacity`.

import { emitTree } from '../../sdf/objects/combinators.js';
import { lightPreamble } from './lighting.js';

// Compile-time march cap. `uMaxSteps` clamps the loop at runtime so lowering
// the budget does not require a shader recompile.
export const MAX_STEPS = 256;

// Compile-time cap on the number of members in an `SdfGroup`. The fold is
// unrolled per group, so this only sizes the uniform array (padded slots are
// identity and never read).
export const MAX_GROUP_MEMBERS = 16;

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
    const lines = [];
    children.forEach((child, i) => {
        lines.push(`float member${i}(vec3 p) {`);
        lines.push(`    return ${emitTree(child)};`);
        lines.push('}');
    });
    lines.push('float map(vec3 p) {');
    lines.push('    float d = MAX_DIST;');
    children.forEach((child, i) => {
        const combine = (child.combine || 'union').toLowerCase();
        lines.push(`    vec3 pm${i} = (uMemberInvTransform[${i}] * vec4(p, 1.0)).xyz;`);
        lines.push(`    float d${i} = member${i}(pm${i});`);
        if (combine === 'subtract') {
            lines.push(`    d = opSubtract(d, d${i});`);
        } else if (combine === 'intersection') {
            lines.push(`    d = opIntersect(d, d${i});`);
        } else {
            lines.push(`    d = opUnion(d, d${i});`);
        }
    });
    lines.push('    return d;');
    lines.push('}');
    return lines.join('\n');
}

// Assemble the proxy fragment from the fetched shader parts + the entity's
// single-object tree. `shaderParts` = { common, primitives, combinators, proxy }.
export function buildProxyFragment(ent, shaderParts) {
    const { common, primitives, combinators, proxy } = shaderParts;
    const isGroup = !!ent.members;

    const mapSrc = isGroup
        ? buildGroupMap(ent)
        : `float map(vec3 p) {
    return ${emitTree(ent.tree)};
}`;

    const groupPreamble = isGroup
        ? `const int MAX_GROUP_MEMBERS = ${MAX_GROUP_MEMBERS};
uniform mat4 uMemberInvTransform[MAX_GROUP_MEMBERS];`
        : '';

    const parts = [
        common,
        primitives,
        combinators,
        lightPreamble,
        `const int MAX_STEPS = ${MAX_STEPS};`,
        groupPreamble,
        mapSrc,
        proxy,
    ];
    return parts.filter((s) => s !== '').join('\n');
}
