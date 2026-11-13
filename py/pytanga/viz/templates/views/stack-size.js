// Tanga Viewer — Pure content-size arithmetic for `StackView` (no DOM).
// Node-testable independently of the flex container.

export const GAP = 4; // px; must match the flex gap set in stack-view.js

/**
 * Resolve a CSS gap value (as returned by `getComputedStyle(el).rowGap`)
 * to a px number.  Browsers report `"normal"` for `gap: normal`, and an
 * element outside the document reports `""`; both fall back.
 */
export function resolveGapPx(value, fallback = GAP) {
    if (typeof value === 'number') return Number.isFinite(value) ? value : fallback;
    const px = parseFloat(value);
    return Number.isFinite(px) ? px : fallback;
}

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
 *
 * Hidden children are skipped entirely: `View.setHidden` removes them from flow
 * (`display: none`), so they contribute neither size nor a gap.
 */
export function stackMinSize(axis, direction, children, available, gap = GAP) {
    const kids = visibleChildren(children);
    if (kids.length === 0) return 0;
    if (direction === 'wrap') return 0;
    if (axis === stackMainAxis(direction)) {
        return kids.reduce((s, c) => s + c.minSizePx(axis, available), 0)
            + (kids.length - 1) * gap;
    }
    return kids.reduce((m, c) => Math.max(m, c.minSizePx(axis, available)), 0);
}

/**
 * Preferred content size of a stack along `axis`, or `null` if not derivable
 * (no visible children, or `wrap` direction whose size depends on the DOM).
 */
export function stackPreferredSize(axis, direction, children, available, gap = GAP) {
    const kids = visibleChildren(children);
    if (kids.length === 0) return null;
    if (direction === 'wrap') return null;
    const main = stackMainAxis(direction);
    if (axis === main) {
        return kids.reduce((s, c) => {
            const p = c.preferredPx(axis, available);
            return s + (p !== null && p !== undefined ? p : c.minSizePx(axis, available));
        }, 0) + (kids.length - 1) * gap;
    }
    let m = 0;
    for (const c of kids) {
        const p = c.preferredPx(axis, available);
        m = Math.max(m, p !== null && p !== undefined ? p : c.minSizePx(axis, available));
    }
    return m;
}

/** The children that participate in layout (`View.hidden === false`). */
export function visibleChildren(children) {
    return (children || []).filter((c) => !c.hidden);
}
