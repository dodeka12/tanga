import test from 'node:test';
import assert from 'node:assert/strict';

// Minimal DOM stubs so controls-panel.js (and its transitive view imports) can
// load and render in Node.
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
    getElementById: () => makeEl('div'),
    addEventListener() {},
    removeEventListener() {},
};

const {
    createFileChooser,
    applyControlValue,
    forgetControl,
} = await import('../../../py/pytanga/viz/templates/controls-panel.js');

test('applyControlValue and forgetControl manage the control registry', () => {
    createFileChooser({ id: 'fc', owner: 'layout', label: 'File', value: '' });
    createFileChooser({ id: 'panel', label: 'Panel', value: '' });

    const unknown = [];
    const origDebug = console.debug;
    console.debug = (...args) => unknown.push(args);
    try {
        // Both entries live initially.
        applyControlValue('fc', '/x');
        applyControlValue('panel', '/x');
        assert.equal(unknown.length, 0);

        // forgetControl drops a single entry, leaving other entries intact.
        forgetControl('panel');
        applyControlValue('fc', '/y');
        assert.equal(unknown.length, 0);

        // The forgotten entry now reports unknown.
        applyControlValue('panel', '/y');
        assert.equal(unknown.length, 1);
    } finally {
        console.debug = origDebug;
    }
});
