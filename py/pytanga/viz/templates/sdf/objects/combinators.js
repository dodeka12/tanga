// Per-combinator-kind GLSL emitters.
//
// Maps a combinator node `kind` to an expression folding its already-emitted
// child distance strings. Hard combinators use IQ min/max with sign
// preservation; `bound` is an alias for a finite clip box (intersect with an
// `sdBox`). A `group` node folds its children in order, each with its own
// `combine` mode (the nested-CSG shape used by `Composed` objects). Smooth
// `smooth_*` modes use the IQ `opSmooth*` helpers and fold down to a scalar by
// taking `.x` (the blend factor is only meaningful at the material-mixing fold
// in the proxy shader / composer, not inside a single member's tree).

import { emitPrimitive } from './primitives.js';
import { transformExpr } from './transform.js';

// Smooth-blend radius default (matches `sdf/composer.js`).
const COMBINE_SMOOTHNESS_DEFAULT = 0.1;

function _combineSmoothness(node) {
    const k = Number(
        node.smoothness != null ? node.smoothness : COMBINE_SMOOTHNESS_DEFAULT,
    );
    return Number.isFinite(k) ? k : COMBINE_SMOOTHNESS_DEFAULT;
}

function foldOp(op, a, b, k = COMBINE_SMOOTHNESS_DEFAULT) {
    if (op === 'intersection' || op === 'intersect') return `opIntersect(${a}, ${b})`;
    if (op === 'subtract') return `opSubtract(${a}, ${b})`;
    if (op === 'xor') return `opXor(${a}, ${b})`;
    if (op === 'smooth_union') return `opSmoothUnion(${a}, ${b}, ${k}).x`;
    if (op === 'smooth_intersection' || op === 'smooth_intersect') {
        return `opSmoothIntersect(${a}, ${b}, ${k}).x`;
    }
    if (op === 'smooth_subtract') return `opSmoothSubtract(${a}, ${b}, ${k}).x`;
    return `opUnion(${a}, ${b})`;
}

function childExpr(node, child) {
    // A primitive child evaluates in its local space; a combinator child has
    // already been emitted recursively.
    if (child.children) {
        return emitNode(child);
    }
    return emitPrimitive(child, transformExpr(child.transform));
}

function emitNode(node) {
    switch (node.kind) {
        case 'union':
        case 'intersect':
        case 'subtract':
        case 'xor':
        case 'smooth_union':
        case 'smooth_intersection':
        case 'smooth_intersect':
        case 'smooth_subtract': {
            // Uniform fold: every child combines with the node's single op.
            const k = _combineSmoothness(node);
            const [first, ...rest] = node.children;
            let acc = childExpr(node, first);
            for (const child of rest) {
                const d = childExpr(node, child);
                acc = foldOp(node.kind, acc, d, k);
            }
            return acc;
        }
        case 'group': {
            // Ordered fold: each child carries its own `combine` mode.
            const children = node.children || [];
            let acc = null;
            for (const child of children) {
                const d = childExpr(node, child);
                const k = _combineSmoothness(child);
                acc = acc === null ? d : foldOp(child.combine || 'union', acc, d, k);
            }
            return acc === null ? 'MAX_DIST' : acc;
        }
        default:
            throw new Error(`Unknown SDF combinator kind: ${node.kind}`);
    }
}

export function emitTree(tree) {
    // A root can be a bare primitive (e.g. a point = a single sphere), a
    // combinator tree, or a `group` of combined constituents.
    if (tree.children) {
        return emitNode(tree);
    }
    return emitPrimitive(tree, transformExpr(tree.transform));
}
