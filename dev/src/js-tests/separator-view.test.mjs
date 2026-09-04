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
        title: '',
        children: [],
        classList: {
            add(...names) { names.forEach((n) => classes.add(n)); },
            remove(...names) { names.forEach((n) => classes.delete(n)); },
            contains: (n) => classes.has(n),
            toggle() {},
        },
        appendChild(c) { this.children.push(c); return c; },
        replaceChildren(...nodes) { this.children = nodes; },
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

const { SeparatorView } = await import('../../../py/pytanga/viz/templates/views/separator-view.js');

test('explicit vertical separator applies class, margin, and preferred width', () => {
    const sep = new SeparatorView({ orientation: 'vertical', spacing: 6 });
    assert.ok(sep.el.classList.contains('tanga-separator-vertical'));
    assert.equal(sep.el.style.margin, '0 6px');
    assert.equal(sep.preferredWidth.value, 1);
});

test('explicit horizontal separator applies class, margin, and preferred height', () => {
    const sep = new SeparatorView({ orientation: 'horizontal', spacing: 8 });
    assert.ok(sep.el.classList.contains('tanga-separator-horizontal'));
    assert.equal(sep.el.style.margin, '8px 0');
    assert.equal(sep.preferredHeight.value, 1);
});

test('auto resolves perpendicular from the container direction', () => {
    const sep = new SeparatorView({ orientation: 'auto' });
    sep.resolveOrientation('horizontal'); // horizontal container → vertical line
    assert.ok(sep.el.classList.contains('tanga-separator-vertical'));
    assert.equal(sep.preferredWidth.value, 1);

    const sep2 = new SeparatorView({ orientation: 'auto' });
    sep2.resolveOrientation('vertical'); // vertical container → horizontal line
    assert.ok(sep2.el.classList.contains('tanga-separator-horizontal'));
    assert.equal(sep2.preferredHeight.value, 1);
});

test('resolveOrientation is a no-op for an explicit orientation', () => {
    const sep = new SeparatorView({ orientation: 'horizontal' });
    sep.resolveOrientation('horizontal'); // must not flip to vertical
    assert.ok(sep.el.classList.contains('tanga-separator-horizontal'));
    assert.ok(!sep.el.classList.contains('tanga-separator-vertical'));
});
