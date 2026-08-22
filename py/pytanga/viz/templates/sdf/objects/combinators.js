// Per-combinator-kind GLSL emitters.
//
// Maps a combinator node `kind` to an expression folding its already-emitted
// child distance strings. Hard combinators use IQ min/max with sign
// preservation; `bound` is an alias for a finite clip box (intersect with an
// `sdBox`).

import { emitPrimitive } from './primitives.js';
import { transformExpr } from './transform.js';

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
        case 'subtract': {
            const [first, ...rest] = node.children;
            let acc = childExpr(node, first);
            for (const child of rest) {
                const d = childExpr(node, child);
                if (node.kind === 'union') acc = `opUnion(${acc}, ${d})`;
                else if (node.kind === 'intersect') acc = `opIntersect(${acc}, ${d})`;
                else acc = `opSubtract(${acc}, ${d})`;
            }
            return acc;
        }
        default:
            throw new Error(`Unknown SDF combinator kind: ${node.kind}`);
    }
}

export function emitTree(tree) {
    return emitNode(tree);
}