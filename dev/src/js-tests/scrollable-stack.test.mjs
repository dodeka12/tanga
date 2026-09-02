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
        replaceChildren(...nodes) { this.children = nodes; },
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
const { SpacerView } = await import('../../../py/pytanga/viz/templates/views/spacer-view.js');
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

test('a spacer with fr preferred grows along the flow main axis (flex 1 1 0)', () => {
    const stack = new StackView({ direction: 'horizontal' });
    const spacer = new SpacerView();
    // `build.js::applySizeSpecs` assigns this from the serialized Python node.
    spacer.preferredWidth = { value: 1, unit: 'fr' };
    spacer.preferredHeight = { value: 1, unit: 'fr' };
    stack.addChild(spacer);
    assert.equal(spacer.el.style.flex, '1 1 0');
    assert.equal(spacer.el.style.minWidth, '0');
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
    // Min height along y is just the chrome (title bar + shell), decoupled from
    // the 200px-tall child.
    assert.equal(group.minSizePx('y', 0) > 0, true);
    assert.equal(group.minSizePx('y', 0) < 60, true);
});

test('a group with equal min/max reads as fixed (min == max)', () => {
    const group = new GroupView({ title: 'Fixed' });
    group.minHeight = { value: 120, unit: 'px' };
    group.maxHeight = { value: 120, unit: 'px' };
    // The title bar must not push the derived min above the explicit max,
    // otherwise min == max panes would not be detected as fixed.
    assert.equal(group.minSizePx('y', 0), 120);
    assert.equal(group.maxSizePx('y', 0), 120);
});

test('collapse pins a fixed group to the header and emits constraintschange', () => {
    const group = new GroupView({ title: 'Fixed' });
    group.minHeight = { value: 120, unit: 'px' };
    group.maxHeight = { value: 120, unit: 'px' };

    let events = 0;
    group.on('constraintschange', () => { events += 1; });

    group.setCollapsed(true);
    assert.equal(group.collapsed, true);
    // Folded: the pane reports just the chrome up to the title bar's border
    // (FOLDED_FALLBACK = 38).
    assert.equal(group.minSizePx('y', 0), 38);
    assert.equal(group.maxSizePx('y', 0), 38);
    assert.equal(group.minHeight.value, 38);
    assert.equal(group.maxHeight.value, 38);
    assert.ok(events >= 1, 'collapse should broadcast constraintschange');

    const afterCollapse = events;
    group.setCollapsed(true); // already collapsed → no-op
    assert.equal(events, afterCollapse);

    group.setCollapsed(false);
    assert.equal(group.collapsed, false);
    assert.equal(group.minSizePx('y', 0), 120);
    assert.equal(group.maxSizePx('y', 0), 120);
    assert.equal(group.minHeight.value, 120);
    assert.equal(group.maxHeight.value, 120);
});

test('collapse restore clears the inline CSS of a group with no explicit min/max', () => {
    const group = new GroupView({ title: 'Flexible' });
    group.setCollapsed(true);
    assert.equal(group.el.style.minHeight, '38px');
    assert.equal(group.el.style.maxHeight, '38px');

    group.setCollapsed(false);
    assert.equal(group._minHeight, null);
    assert.equal(group._maxHeight, null);
    // Clearing a constraint must release its CSS (not leave a stale 38px).
    assert.equal(group.el.style.minHeight, '');
    assert.equal(group.el.style.maxHeight, '');
});
