// SDF composer — fold all per-object distance expressions into one global
// `vec2 map(vec3 p)` returning (distance, materialId).
//
// Fold order follows serialization (insertion) order. Each object folds with
// its `combine` mode:
//   · union      → min(acc, d)   (default; the closer object's material wins)
//   · intersect  → max(acc, d)   (the outer surface's material wins)
//   · subtract   → max(acc, -d)  (carves; the positive accumulator keeps its material)
//
// `d` starts at MAX_DIST (an empty scene is far away) and `m` at -1.

import { buildObjectExpr } from './scene-builder.js';

export function composeObjects(objects) {
    const lines = ['vec2 map(vec3 p) {', '    float d = MAX_DIST;', '    float m = -1.0;'];
    objects.forEach((obj, index) => {
        const expr = buildObjectExpr(obj);
        const mode = (obj.combine || 'union').toLowerCase();
        lines.push('    {');
        lines.push(`        float d${index} = ${expr};`);
        if (mode === 'subtract') {
            lines.push(`        d = max(d, -d${index});`);
        } else if (mode === 'intersection') {
            lines.push(`        if (d${index} > d) { d = d${index}; m = ${index}.0; }`);
        } else {
            lines.push(`        if (d${index} < d) { d = d${index}; m = ${index}.0; }`);
        }
        lines.push('    }');
    });
    lines.push('    return vec2(d, m);');
    lines.push('}');
    return lines.join('\n');
}