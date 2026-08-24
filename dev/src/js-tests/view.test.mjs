import test from 'node:test';
import assert from 'node:assert/strict';

// Stub the browser-only globals before importing view.js.
class FakeResizeObserver {
    constructor(cb) {
        this._cb = cb;
        FakeResizeObserver._instances.push(this);
    }
    observe() {}
    disconnect() {}
    static _instances = [];
    static triggerLast(width, height) {
        FakeResizeObserver._instances.at(-1)._cb([{ contentRect: { width, height } }]);
    }
}
globalThis.ResizeObserver = FakeResizeObserver;

const { View } = await import('../../../py/pytanga/viz/templates/views/view.js');

class FakeEl {
    constructor() { this.classList = { add() {} }; }
    remove() {}
}

test('View measures extent via ResizeObserver and emits extentchange', () => {
    const view = new View({ el: new FakeEl() });
    const events = [];
    view.on('extentchange', (e) => events.push(e.detail));
    FakeResizeObserver.triggerLast(100, 50);
    assert.equal(view.width, 100);
    assert.equal(view.height, 50);
    assert.equal(events.length, 1);
    assert.deepEqual(events[0], { prev: { width: 0, height: 0 }, width: 100, height: 50 });
});

test('View constraint setters emit constraintschange', () => {
    const view = new View({ el: new FakeEl() });
    const events = [];
    view.on('constraintschange', (e) => events.push(e.detail));
    view.minWidth = { value: 100, unit: 'px' };
    view.maxWidth = { value: 100, unit: 'px' };
    assert.equal(events.length, 2);
    assert.equal(view.fixedX, true);
    assert.equal(view.fixedY, false);
});

test('View resolution helpers', () => {
    const view = new View({ el: new FakeEl() });
    view.minWidth = { value: 50, unit: '%' };
    assert.equal(view.minSizePx('x', 1000), 500);
    assert.equal(view.minSizePx('y', 1000), 0); // no minHeight set
    assert.equal(view.maxSizePx('x', 1000), null); // no maxWidth set
});

test('View preferred setters emit preferredchange', () => {
    const view = new View({ el: new FakeEl() });
    const events = [];
    view.on('preferredchange', (e) => events.push(e.detail));
    view.preferredWidth = { value: 0.5, unit: '%' };
    assert.equal(events.length, 1);
});

test('View on() returns an unsubscribe function', () => {
    const view = new View({ el: new FakeEl() });
    const events = [];
    const off = view.on('constraintschange', (e) => events.push(e.detail));
    view.minWidth = { value: 10, unit: 'px' };
    assert.equal(events.length, 1);
    off();
    view.minWidth = { value: 20, unit: 'px' };
    assert.equal(events.length, 1);
});
