// Tanga Viewer — Pure split layout resolver (no DOM).
// Computes per-child px sizes, splitter positions/movability, and any leftover
// (spacer) or overflow, honoring per-child min/max/preferred constraints.

export const SPLITTER_SIZE = 6;

/**
 * Resolve a 1-D split allocation.
 *
 * @param {Array<{min: number, max: number|null, preferred: number|null}>} descriptors
 *   One entry per child, already resolved to pixels along the split axis.
 * @param {number} available  Total extent (px) available to the split,
 *   including splitter bars.
 * @returns {{
 *   items: Array<{size: number, fixed: boolean}>,
 *   splitters: Array<{position: number, movable: boolean}>,
 *   spacer: number,
 *   overflow: number,
 * }}
 */
export function resolveSplit(descriptors, available) {
    const n = descriptors.length;
    if (n === 0) return { items: [], splitters: [], spacer: 0, overflow: 0 };

    const splitterTotal = (n - 1) * SPLITTER_SIZE;
    const childSpace = Math.max(0, available - splitterTotal);

    const fixed = new Array(n);
    const sizes = new Array(n).fill(0);
    let fixedSum = 0;

    for (let i = 0; i < n; i++) {
        const d = descriptors[i];
        const isFixed = d.max !== null && d.max !== undefined && d.min === d.max;
        fixed[i] = isFixed;
        if (isFixed) {
            sizes[i] = d.min;
            fixedSum += d.min;
        }
    }

    const remaining = childSpace - fixedSum;
    const flexible = [];
    for (let i = 0; i < n; i++) if (!fixed[i]) flexible.push(i);

    let total = 0;
    if (flexible.length > 0) {
        const alloc = _distribute(flexible, descriptors, remaining);
        for (const i of flexible) {
            sizes[i] = alloc.get(i);
            total += alloc.get(i);
        }
    }

    const leftover = remaining - total;
    const spacer = leftover > 0 ? leftover : 0;
    const overflow = leftover < 0 ? -leftover : 0;

    const items = sizes.map((size, i) => ({ size, fixed: fixed[i] }));

    const splitters = [];
    let offset = 0;
    for (let i = 0; i < n; i++) {
        offset += sizes[i];
        if (i < n - 1) {
            splitters.push({ position: offset, movable: !fixed[i] && !fixed[i + 1] });
            offset += SPLITTER_SIZE;
        }
    }

    return { items, splitters, spacer, overflow };
}

/**
 * Derive a container's minimum extent along `axis` from its children.
 * Along the split axis children stack (sum of minima + splitters); along the
 * cross axis the container must fit its tallest/widest child (max of minima).
 *
 * @param {'x'|'y'} axis        Axis whose minimum is being asked for.
 * @param {'x'|'y'} splitAxis   The container's own layout axis.
 * @param {Array<{minSizePx(axis: string, available: number): number}>} children
 * @param {number} available    Parent extent along `axis` (px).
 * @returns {number}
 */
export function deriveMinSize(axis, splitAxis, children, available) {
    if (!children || children.length === 0) return 0;
    if (axis === splitAxis) {
        return children.reduce((sum, c) => sum + c.minSizePx(axis, available), 0)
            + (children.length - 1) * SPLITTER_SIZE;
    }
    return children.reduce((max, c) => Math.max(max, c.minSizePx(axis, available)), 0);
}

function _distribute(indices, descriptors, remaining) {
    const alloc = new Map();
    const count = indices.length;
    for (const i of indices) {
        const d = descriptors[i];
        alloc.set(
            i,
            d.preferred !== null && d.preferred !== undefined
                ? d.preferred
                : remaining / count
        );
    }

    for (let pass = 0; pass < 20; pass++) {
        let total = 0;
        for (const i of indices) {
            const d = descriptors[i];
            let v = alloc.get(i);
            const lo = d.min;
            const hi = d.max !== null && d.max !== undefined ? d.max : Infinity;
            if (v < lo) v = lo;
            if (v > hi) v = hi;
            alloc.set(i, v);
            total += v;
        }
        const diff = remaining - total;
        if (Math.abs(diff) < 0.5) return alloc;
        const adjustable = indices.filter((i) => {
            const d = descriptors[i];
            const v = alloc.get(i);
            const hi = d.max !== null && d.max !== undefined ? d.max : Infinity;
            return diff > 0 ? v < hi : v > d.min;
        });
        if (adjustable.length === 0) return alloc;
        const delta = diff / adjustable.length;
        for (const i of adjustable) alloc.set(i, alloc.get(i) + delta);
    }
    return alloc;
}
