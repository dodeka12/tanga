// Tanga Viewer — Pure content-size arithmetic for `StackView` (no DOM).
// Node-testable independently of the flex container.

export const GAP = 4; // px; must match the flex gap set in stack-view.js

export function stackMainAxis(direction) {
    return direction === 'vertical' ? 'y' : 'x';
}

export function stackCrossAxis(direction) {
    return direction === 'vertical' ? 'x' : 'y';
}

/**
 * Minimum content size of a stack along `axis`.
 *
 * Vertical/horizontal stacks derive a min from their children (sum along the
 * main axis, max along the cross axis).  `wrap` stacks are measured from the
 * rendered DOM, so their derived min is 0 here.
 */
export function stackMinSize(axis, direction, children, available) {
    if (!children || children.length === 0) return 0;
    if (direction === 'wrap') return 0;
    if (axis === stackMainAxis(direction)) {
        return children.reduce((s, c) => s + c.minSizePx(axis, available), 0)
            + (children.length - 1) * GAP;
    }
    return children.reduce((m, c) => Math.max(m, c.minSizePx(axis, available)), 0);
}

/**
 * Preferred content size of a stack along `axis`, or `null` if not derivable
 * (empty children, or `wrap` direction whose size depends on the rendered DOM).
 */
export function stackPreferredSize(axis, direction, children, available) {
    if (!children || children.length === 0) return null;
    if (direction === 'wrap') return null;
    const main = stackMainAxis(direction);
    if (axis === main) {
        return children.reduce((s, c) => {
            const p = c.preferredPx(axis, available);
            return s + (p !== null && p !== undefined ? p : c.minSizePx(axis, available));
        }, 0) + (children.length - 1) * GAP;
    }
    let m = 0;
    for (const c of children) {
        const p = c.preferredPx(axis, available);
        m = Math.max(m, p !== null && p !== undefined ? p : c.minSizePx(axis, available));
    }
    return m;
}
