// SDF scene builder — per-object dispatcher (Phase 4).
//
// Maps a serialized SDF scene object to its GLSL distance expression. Each
// object carries an `sdfKind` (Point/Line/… from the Python serializer) and a
// `tree` of primitive/combinator nodes. The tree emitters in `objects/*`
// (mirroring the existing `renderers/`) turn that tree into a single GLSL
// expression string.
//
// The composed global `map()` and the material table are added in Phase 5
// (`material-table.js` + the composition loop); this module is the per-object
// building block both the vertical slice and the compositor rely on.

import { emitTree } from './objects/combinators.js';

export function buildObjectExpr(obj, index) {
    // Algebra path: a `mv_sdf` object is emitted as a call to its pre-declared
    // `dist_mv_<i>` leaf function (defined by `algebra/eval.js` in the preamble).
    if (obj.sdfKind === 'mv_sdf') {
        if (typeof index !== 'number') {
            throw new Error(`mv_sdf object ${obj.id} needs an object index`);
        }
        return `dist_mv_${index}(p)`;
    }
    if (!obj.tree) {
        throw new Error(`SDF object ${obj.id} has no tree`);
    }
    // Analytic path: a proper SDF has |∇d| = 1, so its gradient norm is 1.0.
    return `vec2(${emitTree(obj.tree)}, 1.0)`;
}