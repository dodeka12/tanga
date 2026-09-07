import test from 'node:test';
import assert from 'node:assert/strict';

// Minimal DOM stubs so controls-panel.js (and its transitive imports) can load
// in Node; its `_injectStyles()` runs at import time and needs `document`.
class FakeResizeObserver {
    constructor(cb) { this._cb = cb; }
    observe() {}
    disconnect() {}
}
globalThis.ResizeObserver = FakeResizeObserver;

function makeEl(tag = 'div') {
    return {
        tagName: tag.toUpperCase(),
        className: '',
        textContent: '',
        value: '',
        checked: false,
        title: '',
        type: '',
        style: {},
        children: [],
        classList: { add() {}, remove() {}, toggle() {}, contains: () => false },
        appendChild(c) { this.children.push(c); return c; },
        addEventListener() {},
        removeEventListener() {},
        remove() {},
        setAttribute() {},
        querySelector() { return null; },
        getBoundingClientRect() { return { left: 0, top: 0 }; },
        focus() {},
    };
}
globalThis.document = {
    createElement: (tag) => makeEl(tag),
    body: makeEl('body'),
    head: makeEl('head'),
    getElementById: () => null,
    addEventListener() {},
    removeEventListener() {},
};

const { resolveUndoRedoAction } = await import(
    '../../../py/pytanga/viz/templates/controls-panel.js'
);

test('resolveUndoRedoAction maps Ctrl+Z / Ctrl+Shift+Z / Ctrl+Y', () => {
    assert.equal(resolveUndoRedoAction({ ctrlKey: true, shiftKey: false, key: 'z' }), 'undo');
    assert.equal(resolveUndoRedoAction({ ctrlKey: true, shiftKey: false, key: 'Z' }), 'undo');
    assert.equal(resolveUndoRedoAction({ ctrlKey: true, shiftKey: true, key: 'z' }), 'redo');
    assert.equal(resolveUndoRedoAction({ ctrlKey: true, shiftKey: false, key: 'y' }), 'redo');
    assert.equal(resolveUndoRedoAction({ ctrlKey: true, shiftKey: true, key: 'y' }), 'redo');
    assert.equal(resolveUndoRedoAction({ ctrlKey: false, shiftKey: false, key: 'z' }), null);
    assert.equal(resolveUndoRedoAction({ ctrlKey: true, shiftKey: false, key: 'a' }), null);
    assert.equal(resolveUndoRedoAction({ ctrlKey: true, shiftKey: false, key: '' }), null);
});

const { fitColumnWidths, fitContentColumnWidths, resizeColumnWidths, cellCoordinates, moveCell, clampCell, sortRows, clamp } = await import(
    '../../../py/pytanga/viz/templates/table-grid.js'
);

test('fitColumnWidths fills the available width proportionally', () => {
    assert.deepEqual(fitColumnWidths(300, [1, 1, 1]), [100, 100, 100]);
    assert.deepEqual(fitColumnWidths(300, [2, 1]), [200, 100]);
});

test('fitColumnWidths clamps columns at the minimum width', () => {
    assert.deepEqual(fitColumnWidths(30, [1, 1, 1]), [24, 24, 24]);
    assert.deepEqual(fitColumnWidths(100, [3, 1, 1]), [60, 24, 24]);
});

test('fitColumnWidths returns [] for no weights', () => {
    assert.deepEqual(fitColumnWidths(300, []), []);
});

test('fitContentColumnWidths clamps at min/max and adds padding', () => {
    assert.deepEqual(
        fitContentColumnWidths([10, 200, 500], { min: 24, max: 240, padding: 16 }),
        [26, 216, 240],
    );
});

test('fitContentColumnWidths defaults', () => {
    assert.deepEqual(fitContentColumnWidths([10]), [24]); // min default clamps
    assert.deepEqual(fitContentColumnWidths([300]), [240]); // max default clamps
    assert.deepEqual(fitContentColumnWidths([]), []);
});

test('resizeColumnWidths changes only the dragged column', () => {
    // Growing a middle column leaves its neighbours unchanged (the table's total
    // width grows, and the columns to the right just shift).
    assert.deepEqual(resizeColumnWidths([100, 100, 100], 1, 40), [100, 140, 100]);
    assert.deepEqual(resizeColumnWidths([100, 100, 100], 0, -30), [70, 100, 100]);
});

test('resizeColumnWidths clamps at the minimum width', () => {
    assert.deepEqual(resizeColumnWidths([100, 100, 100], 1, -100), [100, 24, 100]);
    // Custom minimum.
    assert.deepEqual(resizeColumnWidths([40, 40], 0, -100, 40), [40, 40]);
});

test('resizeColumnWidths does not mutate the input array', () => {
    const widths = [100, 100];
    const result = resizeColumnWidths(widths, 0, 50);
    assert.deepEqual(result, [150, 100]);
    assert.deepEqual(widths, [100, 100]);
});

test('cellCoordinates maps a rendered cell to its original row + column', () => {
    assert.deepEqual(
        cellCoordinates({ dataset: { originalIndex: '7', col: '2' } }),
        { row: 7, col: 2 }
    );
    assert.deepEqual(cellCoordinates(null), { row: NaN, col: NaN });
});

test('moveCell clamps to grid bounds and never enters a row-number column', () => {
    // 3 rows × 2 data columns.
    assert.deepEqual(moveCell(1, 1, 'ArrowDown', 3, 2), { row: 2, col: 1 });
    assert.deepEqual(moveCell(2, 1, 'ArrowDown', 3, 2), { row: 2, col: 1 }); // clamp bottom
    assert.deepEqual(moveCell(0, 0, 'ArrowUp', 3, 2), { row: 0, col: 0 });   // clamp top
    assert.deepEqual(moveCell(1, 0, 'ArrowLeft', 3, 2), { row: 1, col: 0 });  // clamp left
    assert.deepEqual(moveCell(1, 1, 'ArrowRight', 3, 2), { row: 1, col: 1 }); // clamp right
});

test('clampCell keeps coordinates inside [0, rowCount) × [0, colCount)', () => {
    assert.deepEqual(clampCell(-1, -1, 2, 2), { row: 0, col: 0 });
    assert.deepEqual(clampCell(9, 9, 2, 2), { row: 1, col: 1 });
    assert.deepEqual(clampCell(0, 0, 2, 2), { row: 0, col: 0 });
});

test('sortRows orders rows numerically-aware and resets on null', () => {
    const rows = [['10'], ['2'], ['1']];
    assert.deepEqual(sortRows(rows, 0, 'asc'), [2, 1, 0]);  // 1, 2, 10
    assert.deepEqual(sortRows(rows, 0, 'desc'), [0, 1, 2]); // 10, 2, 1
    assert.deepEqual(sortRows(rows, 0, null), [0, 1, 2]);
});

test('sortRows compares non-numeric cells as strings', () => {
    const rows = [['b'], ['a'], ['c']];
    assert.deepEqual(sortRows(rows, 0, 'asc'), [1, 0, 2]);
    assert.deepEqual(sortRows(rows, 0, 'desc'), [2, 0, 1]);
});

test('clamp bounds a value to [min, max]', () => {
    assert.equal(clamp(5, 0, 10), 5);
    assert.equal(clamp(-1, 0, 10), 0);
    assert.equal(clamp(11, 0, 10), 10);
});

test('fitColumnWidths zooms columns via a colScale multiplier', () => {
    // 300px avail, weights [2, 1], colScale 2 → 600px content → [400, 200].
    assert.deepEqual(fitColumnWidths(300 * 2, [2, 1]), [400, 200]);
    assert.deepEqual(fitColumnWidths(300 * 0.5, [2, 1]), [100, 50]);
});
