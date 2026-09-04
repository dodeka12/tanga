import test from 'node:test';
import assert from 'node:assert/strict';

class FakeResizeObserver {
    constructor(cb) { this._cb = cb; }
    observe() {}
    disconnect() {}
}
globalThis.ResizeObserver = FakeResizeObserver;

function makeEl() {
    const classes = new Set();
    return {
        style: {},
        className: '',
        textContent: '',
        innerHTML: '',
        title: '',
        children: [],
        classList: {
            add(...n) { n.forEach((x) => classes.add(x)); },
            remove(...n) { n.forEach((x) => classes.delete(x)); },
            contains: (n) => classes.has(n),
            toggle() {},
        },
        appendChild(c) { this.children.push(c); return c; },
        replaceChildren(...n) { this.children = n; },
        addEventListener() {},
        removeEventListener() {},
        remove() {},
        setAttribute() {},
    };
}
globalThis.document = {
    createElement: () => makeEl(),
    getElementById: () => null,
    head: { appendChild() {} },
    body: makeEl(),
};

const markedCalls = [];
globalThis.marked = {
    parse: (src, opts) => { markedCalls.push({ src, opts }); return `<p>${src}</p>`; },
};
globalThis.renderMathInElement = () => {};

const { createMarkdown } = await import('../../../py/pytanga/viz/templates/controls-panel.js');

test('createMarkdown renders markdown without `breaks` so `$$…$$` math survives', () => {
    createMarkdown({ id: 'md', value: '$$x$$', owner: 'layout' });
    assert.equal(markedCalls.length, 1);
    assert.equal(markedCalls[0].src, '$$x$$');
    assert.equal(markedCalls[0].opts, undefined);
});
