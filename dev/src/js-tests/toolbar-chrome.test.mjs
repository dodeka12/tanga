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

globalThis.document = {
    createElement: () => makeEl(),
    getElementById: () => null,
    head: { appendChild() {} },
    body: makeEl(),
    addEventListener() {},
    removeEventListener() {},
};

const { ToolbarView } = await import('../../../py/pytanga/viz/templates/views/toolbar-view.js');
const { Size } = await import('../../../py/pytanga/viz/templates/views/size.js');
const { createDropdown, createSlider } = await import('../../../py/pytanga/viz/templates/controls-panel.js');

const child = (minY, prefY) => ({
    minSizePx: (a) => (a === 'y' ? minY : 0),
    preferredPx: (a) => (a === 'y' ? prefY : null),
});

test('_chrome falls back to the default constant when the DOM is not measurable', () => {
    const toolbar = new ToolbarView({});
    assert.deepEqual(toolbar._chrome(), { x: 14, y: 14 });
});

test('preferred height adds chrome to the content in the fallback path', () => {
    const toolbar = new ToolbarView({});
    toolbar.children = [child(32, 32)];
    assert.equal(toolbar.preferredPx('y', 0), 32 + 14);
});

test('min height adds chrome to the content in the fallback path', () => {
    const toolbar = new ToolbarView({});
    toolbar.children = [child(32, 32)];
    assert.equal(toolbar.minSizePx('y', 0), 32 + 14);
});

test('_chrome measures padding + border from getComputedStyle', () => {
    const toolbar = new ToolbarView({});
    globalThis.getComputedStyle = () => ({
        paddingLeft: '6px',
        paddingRight: '6px',
        paddingTop: '6px',
        paddingBottom: '6px',
        borderLeftWidth: '1px',
        borderRightWidth: '1px',
        borderTopWidth: '1px',
        borderBottomWidth: '1px',
    });
    assert.deepEqual(toolbar._chrome(), { x: 14, y: 14 });
    delete globalThis.getComputedStyle;
});

test('borderless toolbar omits the border class', () => {
    const toolbar = new ToolbarView({ border: false });
    assert.ok(toolbar.el.classList.contains('tanga-toolbar-borderless'));
});

test('max height is fixed to the natural content height on the cross axis', () => {
    const toolbar = new ToolbarView({});
    toolbar.children = [child(32, 32)];
    assert.equal(toolbar.maxSizePx('y', 0), 32 + 14);
});

test('max width stays unbounded on the main axis', () => {
    const toolbar = new ToolbarView({});
    toolbar.children = [child(32, 32)];
    assert.equal(toolbar.maxSizePx('x', 0), null);
});

test('explicit max height overrides the fixed default', () => {
    const toolbar = new ToolbarView({});
    toolbar.children = [child(32, 32)];
    toolbar.maxHeight = Size.px(100);
    assert.equal(toolbar.maxSizePx('y', 0), 100);
});

test('toolbar-variant dropdown gets the toolbar-item class', () => {
    const el = createDropdown({ id: 'dd', variant: 'toolbar', options: [], value: '' });
    assert.ok(el.classList.contains('tanga-toolbar-item'));
});

test('default dropdown has no toolbar-item class', () => {
    const el = createDropdown({ id: 'dd', options: [], value: '' });
    assert.ok(!el.classList.contains('tanga-toolbar-item'));
});

test('toolbar-variant slider gets the toolbar-item class', () => {
    const el = createSlider({ id: 's', variant: 'toolbar', min: 0, max: 1, value: 0.5 });
    assert.ok(el.classList.contains('tanga-toolbar-item'));
});

test('default slider has no toolbar-item class', () => {
    const el = createSlider({ id: 's', min: 0, max: 1, value: 0.5 });
    assert.ok(!el.classList.contains('tanga-toolbar-item'));
});
