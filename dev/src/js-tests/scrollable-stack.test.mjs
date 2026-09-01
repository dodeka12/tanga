import test from 'node:test';
import assert from 'node:assert/strict';

// Stub the browser-only globals before importing the view modules.
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
        addEventListener() {},
        removeEventListener() {},
        remove() {},
        setAttribute() {},
    };
}

const styleEls = [];
globalThis.document = {
    createElement: (tag) => {
        if (tag === 'style') {
            const el = { id: '', textContent: '', appendChild() {} };
            styleEls.push(el);
            return el;
        }
        return makeEl();
    },
    getElementById: (id) => styleEls.find((s) => s.id === id) || null,
    head: { appendChild() {} },
    body: makeEl(),
};

const { StackView } = await import('../../../py/pytanga/viz/templates/views/stack-view.js');
const { GroupView } = await import('../../../py/pytanga/viz/templates/views/group-view.js');
const { GAP } = await import('../../../py/pytanga/viz/templates/views/stack-size.js');

const child = (min, pref) => ({
    minSizePx: (axis) => (axis === 'x' ? min.x : min.y),
    preferredPx: (axis) => (axis === 'x' ? pref.x : pref.y),
});

test('scrollable vertical stack decouples min/preferred along the main axis', () => {
    const stack = new StackView({ direction: 'vertical', scrollable: true });
    stack.children = [
        child({ x: 100, y: 20 }, { x: null, y: 20 }),
        child({ x: 100, y: 30 }, { x: null, y: 30 }),
    ];
    assert.equal(stack.minSizePx('y', 0), 0);
    assert.equal(stack.preferredPx('y', 0), null);
    // Cross axis stays content-derived.
    assert.equal(stack.minSizePx('x', 0), 100);
});

test('non-scrollable vertical stack derives min/preferred from content', () => {
    const stack = new StackView({ direction: 'vertical' });
    stack.children = [
        child({ x: 100, y: 20 }, { x: null, y: 20 }),
        child({ x: 100, y: 30 }, { x: null, y: 30 }),
    ];
    assert.equal(stack.minSizePx('y', 0), 20 + 30 + GAP);
    assert.equal(stack.preferredPx('y', 0), 20 + 30 + GAP);
});

test('scrollable stack sets overflow auto and the tanga-scroll class', () => {
    const stack = new StackView({ direction: 'vertical', scrollable: true });
    assert.equal(stack.el.style.overflow, 'auto');
    assert.equal(stack.el.classList.contains('tanga-scroll'), true);
});

test('scrollable group scrolls its content, not the panel', () => {
    const group = new GroupView({ title: 'Controls', scrollable: true });
    group.children = [child({ x: 100, y: 200 }, { x: null, y: 200 })];
    assert.equal(group.el.style.overflow, 'hidden');
    assert.equal(group._content.style.overflow, 'auto');
    assert.equal(group._content.classList.contains('tanga-scroll'), true);
    // Min height along y is just the title bar (HEADER_HEIGHT), decoupled from
    // the 200px-tall child.
    assert.equal(group.minSizePx('y', 0) > 0, true);
    assert.equal(group.minSizePx('y', 0) < 50, true);
});
