// Tanga Viewer — pure helpers for the native table grid.
// No DOM, no imports: kept pure so the width-fit and row-sort logic is
// unit-testable in Node (`node --test dev/src/js-tests/`).

/** Minimum width (px) a data column is ever squeezed to. */
export const TABLE_MIN_COLUMN = 24;

/**
 * Distribute `available` width across `weights` proportionally, clamping each
 * column at `min`.  `available` is the full width to fill (no reserved gap) and
 * `weights` are relative column weights (equal initial values fill evenly).
 *
 * Returns one width (number, px) per weight.  The caller sets the table's
 * `min-width` to the sum of the minimums so that, when the clamped total
 * exceeds `available`, the table overflows into a horizontal scrollbar instead
 * of squeezing columns below `min`.
 */
export function fitColumnWidths(available, weights, { min = TABLE_MIN_COLUMN } = {}) {
    const n = weights.length;
    if (n === 0) return [];
    const avail = Math.max(0, available);
    const total = weights.reduce((a, b) => a + b, 0) || n;
    return weights.map((w) => Math.max(min, (avail * w) / total));
}

/**
 * Size each column to its measured content width, clamped to ``[min, max]`` and
 * padded by ``padding``.  ``measured`` holds one raw content width (px) per
 * column (e.g. from ``canvas.measureText``); returns the resulting column widths.
 */
export function fitContentColumnWidths(measured, { min = TABLE_MIN_COLUMN, max = 240, padding = 0 } = {}) {
    return measured.map((w) => clamp(w + padding, min, max));
}

/**
 * Return the display order (array of original row indexes) for a stable sort of
 * `rows` by `colIndex`.  `direction` is `'asc'`, `'desc'`, or anything else
 * (identity order).  Numeric-aware: cells that both parse as finite numbers
 * compare numerically, otherwise as strings (locale).
 */
export function sortRows(rows, colIndex, direction) {
    const indexes = rows.map((_, i) => i);
    if (direction !== 'asc' && direction !== 'desc') return indexes;

    const numeric = (v) => {
        const n = Number.parseFloat(v);
        return Number.isFinite(n) ? n : null;
    };

    indexes.sort((a, b) => {
        const va = String((rows[a] && rows[a][colIndex]) ?? '');
        const vb = String((rows[b] && rows[b][colIndex]) ?? '');
        const na = numeric(va);
        const nb = numeric(vb);
        const cmp = na !== null && nb !== null ? na - nb : va.localeCompare(vb);
        return direction === 'asc' ? cmp : -cmp;
    });
    return indexes;
}

/**
 * Read a cell's model coordinates from a rendered `<td>`: the original row
 * index (``data-original-index`` — the index into the backend ``rows`` list,
 * which survives display-only sorting) and the column (``data-col``).
 */
export function cellCoordinates(td) {
    const d = td && td.dataset ? td.dataset : {};
    return {
        row: parseInt(d.originalIndex, 10),
        col: parseInt(d.col, 10),
    };
}

/**
 * Clamp a display cell coordinate to the grid bounds (``[0, rowCount)`` ×
 * ``[0, colCount)``).  ``col`` is a data-column index — the row-number column
 * is not part of this coordinate space, so clamping never lands on it.
 */
export function clampCell(row, col, rowCount, colCount) {
    let r = row;
    let c = col;
    if (c < 0) c = 0;
    if (c >= colCount) c = Math.max(0, colCount - 1);
    if (r < 0) r = 0;
    if (r >= rowCount) r = Math.max(0, rowCount - 1);
    return { row: r, col: c };
}

/**
 * Move a display cell coordinate by an arrow key and clamp to the grid bounds.
 */
export function moveCell(row, col, key, rowCount, colCount) {
    let r = row;
    let c = col;
    if (key === 'ArrowUp') r -= 1;
    else if (key === 'ArrowDown') r += 1;
    else if (key === 'ArrowLeft') c -= 1;
    else if (key === 'ArrowRight') c += 1;
    return clampCell(r, c, rowCount, colCount);
}

/**
 * Clamp `value` to the inclusive range `[min, max]`.
 */
export function clamp(value, min, max) {
    return value < min ? min : value > max ? max : value;
}
