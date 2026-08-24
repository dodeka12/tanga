// SDF composer — fold all per-object distance expressions into one global
// `vec3 map(vec3 p)` returning (distance, materialId, gradientNorm).
//
// Fold order follows serialization (insertion) order. Each object folds with
// its `combine` mode:
//   · union        → min(acc, d)   (default; the closer object's material wins)
//   · intersect    → max(acc, d)   (the outer surface's material wins)
//   · subtract     → max(acc, -d)  (carves; the positive accumulator keeps its material)
//   · smooth_*     → the Phase 1 vec2 smooth combinator (opSmoothUnion/…) for
//                    the distance; the material is blended by the blend factor
//                    (smooth_subtract keeps the positive accumulator material).
//
// The gradient norm `g` is threaded through the fold exactly like `m`: the
// winner's `g` follows the winner's material; smooth folds `mix` `g` by the
// blend factor; `subtract`/`smooth_subtract` keep the positive accumulator's
// `g`. `d` starts at MAX_DIST (an empty scene is far away), `m` at -1, `g` at 1.0.

import { buildObjectExpr } from './scene-builder.js';
import { floatParam } from './objects/transform.js';

const SMOOTHNESS_DEFAULT = 0.1;

function smoothnessOf(obj) {
    return floatParam(obj.smoothness != null ? obj.smoothness : SMOOTHNESS_DEFAULT);
}

export function composeObjects(objects) {
    const lines = ['vec3 map(vec3 p) {', '    float d = MAX_DIST;', '    float m = -1.0;', '    float g = 1.0;'];
    objects.forEach((obj, index) => {
        const expr = buildObjectExpr(obj, index);
        const mode = (obj.combine || 'union').toLowerCase();
        lines.push('    {');
        lines.push(`        vec2 d${index} = ${expr};`);
        if (mode === 'subtract') {
            lines.push(`        d = max(d, -d${index}.x);`);
        } else if (mode === 'intersection') {
            lines.push(`        if (d${index}.x > d) { d = d${index}.x; m = ${index}.0; g = d${index}.y; }`);
        } else if (mode === 'smooth_subtract') {
            lines.push(`        vec2 sm${index} = opSmoothSubtract(d, d${index}.x, ${smoothnessOf(obj)});`);
            lines.push(`        d = sm${index}.x;`);
            // a negative object emits no surface: keep the positive material + g
        } else if (mode === 'smooth_intersection') {
            lines.push(`        vec2 sm${index} = opSmoothIntersect(d, d${index}.x, ${smoothnessOf(obj)});`);
            lines.push(`        d = sm${index}.x;`);
            lines.push(`        m = mix(${index}.0, m, sm${index}.y);`);
            lines.push(`        g = mix(d${index}.y, g, sm${index}.y);`);
        } else if (mode === 'smooth_union') {
            lines.push(`        vec2 sm${index} = opSmoothUnion(d, d${index}.x, ${smoothnessOf(obj)});`);
            lines.push(`        d = sm${index}.x;`);
            lines.push(`        m = mix(${index}.0, m, sm${index}.y);`);
            lines.push(`        g = mix(d${index}.y, g, sm${index}.y);`);
        } else {
            lines.push(`        if (d${index}.x < d) { d = d${index}.x; m = ${index}.0; g = d${index}.y; }`);
        }
        lines.push('    }');
    });
    lines.push('    return vec3(d, m, g);');
    lines.push('}');
    return lines.join('\n');
}