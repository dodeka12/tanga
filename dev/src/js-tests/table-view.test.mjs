import test from 'node:test';
import assert from 'node:assert/strict';

// Minimal DOM stubs so `controls-panel.js` (imported transitively by
// `table-view.js` via `controls/table.js`) can load in Node; its
// `_injectStyles()` runs at import time and needs `document`.
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
    createTextNode: (text) => ({ textContent: text }),
    body: makeEl('body'),
    head: makeEl('head'),
    getElementById: () => null,
    addEventListener() {},
    removeEventListener() {},
};

const { TableView } = await import(
    '../../../py/pytanga/viz/templates/views/table-view.js'
);

test('table view pins its natural size but caps its width at the parent', () => {
    const view = new TableView({ id: 't1', columns: ['a'], rows: [['x']] });
    assert.equal(view.el.style.width, '480px');
    assert.equal(view.el.style.height, '320px');
    // A narrower flow container must shrink the table (grid scrolls internally)
    // rather than the container scrolling the whole widget.
    assert.equal(view.el.style.maxWidth, '100%');
    assert.equal(view.el.style.overflow, 'hidden');
});
