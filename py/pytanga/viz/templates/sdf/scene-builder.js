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

export function buildObjectExpr(obj) {
    if (!obj.tree) {
        throw new Error(`SDF object ${obj.id} has no tree`);
    }
    // Analytic path: the tree carries its own primitive params/transforms; the
    // per-object color/opacity are attached at the material table (Phase 5).
    return emitTree(obj.tree);
}