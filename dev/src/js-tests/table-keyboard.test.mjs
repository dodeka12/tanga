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
