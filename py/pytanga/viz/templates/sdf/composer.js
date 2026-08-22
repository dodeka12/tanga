// SDF composer (Phase 5) — fold all per-object distance expressions into one
// global `vec2 map(vec3 p)` returning (distance, materialId).
//
// The Phase 5 scope is the union fold with material-ID tracking (the common
// case for the six supported entities). The signedness gate and the full
// intersection/subtract combine semantics with material preference are owned
// by Phase 11 (CSG booleans).

import { buildObjectExpr } from './scene-builder.js';

// Emit `vec2 map(vec3 p)` that returns the minimum distance over all objects
// and the 0-based material id of the winner (or -1 beyond `SDF_EPSILON`).
export function composeObjects(objects) {
    const lines = ['vec2 map(vec3 p) {', '    float d = MAX_DIST;', '    float m = -1.0;'];
    objects.forEach((obj, index) => {
        const expr = buildObjectExpr(obj);
        lines.push('    {');
        lines.push(`        float d${index} = ${expr};`);
        lines.push(`        if (d${index} < d) { d = d${index}; m = ${index}.0; }`);
        lines.push('    }');
    });
    lines.push('    return vec2(d, m);');
    lines.push('}');
    return lines.join('\n');
}