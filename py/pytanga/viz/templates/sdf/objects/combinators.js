// Per-combinator-kind GLSL emitters.
//
// Maps a combinator node `kind` to an expression folding its already-emitted
// child distance strings. Hard combinators use IQ min/max with sign
// preservation; `bound` is an alias for a finite clip box (intersect with an
// `sdBox`). A `group` node folds its children in order, each with its own
// `combine` mode (the nested-CSG shape used by `Composed` objects).

import { emitPrimitive } from './primitives.js';
import { transformExpr } from './transform.js';

function foldOp(op, a, b) {
    if (op === 'intersection' || op === 'intersect') return `opIntersect(${a}, ${b})`;
    if (op === 'subtract') return `opSubtract(${a}, ${b})`;
    if (op === 'xor') return `opXor(${a}, ${b})`;
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
        case 'xor': {
            // Uniform fold: every child combines with the node's single op.
            const [first, ...rest] = node.children;
            let acc = childExpr(node, first);
            for (const child of rest) {
                const d = childExpr(node, child);
                acc = foldOp(node.kind, acc, d);
            }
            return acc;
        }
        case 'group': {
            // Ordered fold: each child carries its own `combine` mode.
            const children = node.children || [];
            let acc = null;
            for (const child of children) {
                const d = childExpr(node, child);
                acc = acc === null ? d : foldOp(child.combine || 'union', acc, d);
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
