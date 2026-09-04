import test from 'node:test';
import assert from 'node:assert/strict';

// Stub the browser-only globals before importing the view module.
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
        scrollTop: 0,
        scrollHeight: 0,
        clientHeight: 0,
        classList: {
            add(...names) { names.forEach((n) => classes.add(n)); },
            remove(...names) { names.forEach((n) => classes.delete(n)); },
            contains: (n) => classes.has(n),
            toggle() {},
        },
        appendChild(c) { this.children.push(c); return c; },
        replaceChildren(...nodes) { this.children = nodes; },
        removeChild(c) {
            const i = this.children.indexOf(c);
            if (i >= 0) this.children.splice(i, 1);
            return c;
        },
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

const {
    LogView,
    registerLogView,
    applyLogUpdate,
} = await import('../../../py/pytanga/viz/templates/views/log-view.js');

test('initial lines render on mount (two columns)', () => {
    const view = new LogView({
        id: 'log0',
        lines: [{ time: 't1', message: 'a' }, { time: 't2', message: 'b' }],
    });
    view._onMounted();
    assert.equal(view.el.children.length, 2);
    assert.equal(view.el.children[0].children[0].textContent, 't1');
    assert.equal(view.el.children[0].children[1].textContent, 'a');
    assert.equal(view.el.children[1].children[1].textContent, 'b');
});

test('_messageOf uses message else JSON of non-time keys', () => {
    const view = new LogView({ id: 'log0' });
    assert.equal(view._messageOf({ time: 't', message: 'hi' }), 'hi');
    assert.equal(view._messageOf({ time: 't', level: 'info' }), '{"level":"info"}');
});

test('appendLines adds rows and enforces max_history', () => {
    const view = new LogView({ id: 'log0', max_history: 2 });
    view.appendLines([
        { time: 't', message: 'a' },
        { time: 't', message: 'b' },
        { time: 't', message: 'c' },
    ]);
    assert.equal(view.el.children.length, 2);
    assert.equal(view.el.children[0].children[1].textContent, 'b');
    assert.equal(view.el.children[1].children[1].textContent, 'c');
});

test('clearLines empties and replaceLines replaces', () => {
    const view = new LogView({ id: 'log0' });
    view.replaceLines([{ time: 't', message: 'x' }]);
    assert.equal(view.el.children.length, 1);

    view.clearLines();
    assert.equal(view.el.children.length, 0);

    view.replaceLines([{ time: 't', message: 'y' }, { time: 't', message: 'z' }]);
    assert.equal(view.el.children.length, 2);
    assert.equal(view.el.children[1].children[1].textContent, 'z');
});

test('append auto-scrolls only when already at the bottom', () => {
    const view = new LogView({ id: 'log0' });
    view.el.scrollTop = 0;
    view.el.clientHeight = 100;
    view.el.scrollHeight = 100; // at bottom
    view.appendLines([{ time: 't', message: 'm' }]);
    assert.equal(view.el.scrollTop, 100);

    const scrolled = new LogView({ id: 'log1' });
    scrolled.el.scrollTop = 0;
    scrolled.el.clientHeight = 100;
    scrolled.el.scrollHeight = 300; // scrolled up
    scrolled.appendLines([{ time: 't', message: 'm' }]);
    assert.equal(scrolled.el.scrollTop, 0);
});

test('applyLogUpdate routes append/clear/replace by id', () => {
    const view = new LogView({ id: 'log0' });
    registerLogView('log0', view);

    applyLogUpdate({ type: 'log_update', id: 'log0', action: 'append', lines: [{ time: 't', message: 'a' }] });
    assert.equal(view.el.children.length, 1);

    applyLogUpdate({ type: 'log_update', id: 'log0', action: 'clear' });
    assert.equal(view.el.children.length, 0);

    applyLogUpdate({ type: 'log_update', id: 'log0', action: 'replace', lines: [{ time: 't', message: 'b' }, { time: 't', message: 'c' }] });
    assert.equal(view.el.children.length, 2);
});

test('applyLogUpdate no-ops for unknown ids', () => {
    assert.doesNotThrow(() => applyLogUpdate({ type: 'log_update', id: 'nope', action: 'clear' }));
});

test('destroy deregisters the view', () => {
    const view = new LogView({ id: 'log0' });
    registerLogView('log0', view);
    view.destroy();
    applyLogUpdate({ type: 'log_update', id: 'log0', action: 'append', lines: [{ time: 't', message: 'x' }] });
    assert.equal(view.el.children.length, 0);
});
