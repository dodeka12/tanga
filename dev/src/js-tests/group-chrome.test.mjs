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

// A minimal `document` that also supports the theme-change event round-trip.
const docListeners = new Map();
globalThis.document = {
    createElement: () => makeEl(),
    getElementById: () => null,
    head: { appendChild() {} },
    body: makeEl(),
    addEventListener(type, fn) {
        if (!docListeners.has(type)) docListeners.set(type, new Set());
        docListeners.get(type).add(fn);
    },
    removeEventListener(type, fn) {
        docListeners.get(type)?.delete(fn);
    },
    dispatchEvent(event) {
        const set = docListeners.get(event.type);
        if (set) for (const fn of [...set]) fn(event);
        return true;
    },
};

globalThis.CustomEvent = class CustomEvent {
    constructor(type) { this.type = type; }
};

const { GroupView } = await import('../../../py/pytanga/viz/templates/views/group-view.js');

const child = (minY, prefY) => ({ minSizePx: (a) => (a === 'y' ? minY : 0), preferredPx: (a) => (a === 'y' ? prefY : null) });

test('_chromeY falls back to constants when the DOM is not measurable', () => {
    const group = new GroupView({ title: 'G' });
    assert.deepEqual(group._chromeY(), { folded: 38, chrome: 53 });
});

test('preferred height adds chrome to the content in the fallback path', () => {
    const group = new GroupView({ title: 'G' });
    group.children = [child(32, 32)];
    assert.equal(group.preferredPx('y', 0), 32 + 53);
});

test('_chromeY measures from getBoundingClientRect + getComputedStyle', () => {
    const group = new GroupView({ title: 'G' });
    group.el.getBoundingClientRect = () => ({ top: 100, height: 100 });
    group._header.getBoundingClientRect = () => ({ top: 109, bottom: 138, height: 29 });
    globalThis.getComputedStyle = (el) => (
        el === group._header
            ? { marginBottom: '6px' }
            : { paddingBottom: '8px', borderBottomWidth: '1px' }
    );
    assert.deepEqual(group._chromeY(), { folded: 38, chrome: 53 });
    delete globalThis.getComputedStyle;
});

test('theme change clears the cache and emits preferred/constraints changes', () => {
    const group = new GroupView({ title: 'G' });
    group.el.getBoundingClientRect = () => ({ top: 100, height: 100 });
    group._header.getBoundingClientRect = () => ({ top: 109, bottom: 138, height: 29 });
    globalThis.getComputedStyle = (el) => (
        el === group._header
            ? { marginBottom: '6px' }
            : { paddingBottom: '8px', borderBottomWidth: '1px' }
    );
    group._chromeY();
    assert.ok(group._chromeYCache, 'cache should be populated after a measurement');

    let preferred = 0;
    let constraints = 0;
    group.on('preferredchange', () => { preferred += 1; });
    group.on('constraintschange', () => { constraints += 1; });

    document.dispatchEvent(new CustomEvent('tanga:themechange'));

    assert.equal(preferred, 1);
    assert.equal(constraints, 1);
    assert.equal(group._chromeYCache, null);
    delete globalThis.getComputedStyle;
});
