// Tanga — unit tests for the pure frame pump (node --test).
import test from 'node:test';
import assert from 'node:assert/strict';
import { createFramePump } from '../../../py/pytanga/viz/templates/frame-pump.js';

function deferred() {
    let resolve;
    const promise = new Promise((r) => { resolve = r; });
    return { promise, resolve };
}

test('idle request applies once and resolves on idle', async () => {
    const calls = [];
    const gate = deferred();
    const pump = createFramePump(async (n) => {
        calls.push(n);
        await gate.promise;
    });

    const p = pump.request(3);
    assert.equal(pump.busy, true);
    assert.deepEqual(calls, [3]);

    gate.resolve();
    await p;
    await pump.idle();
    assert.equal(pump.busy, false);
    assert.deepEqual(calls, [3]);
});

test('burst while busy keeps only the newest target', async () => {
    const calls = [];
    const gate = deferred();
    const pump = createFramePump(async (n) => {
        calls.push(n);
        await gate.promise;
    });

    pump.request(1);
    pump.request(2);
    pump.request(3);

    gate.resolve();
    await pump.idle();
    assert.deepEqual(calls, [1, 3]); // middle target coalesced away
});

test('re-entrant request from inside apply is queued, not nested', async () => {
    const calls = [];
    let depth = 0;
    let maxDepth = 0;
    const pump = createFramePump(async (n) => {
        depth += 1;
        maxDepth = Math.max(maxDepth, depth);
        calls.push(n);
        if (n === 1) pump.request(2); // issued from inside apply
        depth -= 1;
    });

    pump.request(1);
    await pump.idle();
    assert.equal(maxDepth, 1);
    assert.deepEqual(calls, [1, 2]);
});

test('rejecting apply reports to onError, resets, and stays usable', async () => {
    const errors = [];
    const calls = [];
    let fail = true;
    const pump = createFramePump(async (n) => {
        calls.push(n);
        if (fail) throw new Error(`boom ${n}`);
    }, (err) => errors.push(String(err)));

    pump.request(1);
    await pump.idle();
    assert.equal(pump.busy, false);
    assert.deepEqual(calls, [1]);
    assert.deepEqual(errors, ['Error: boom 1']);

    fail = false;
    pump.request(2);
    await pump.idle();
    assert.deepEqual(calls, [1, 2]);
});

test('idle() resolves immediately when idle and waits during a run', async () => {
    const gate = deferred();
    const pump = createFramePump(async () => { await gate.promise; });

    await pump.idle(); // fresh pump → immediate

    let idleResolved = false;
    pump.request(1);
    pump.idle().then(() => { idleResolved = true; });
    await new Promise((r) => setTimeout(r, 0));
    assert.equal(idleResolved, false);

    gate.resolve();
    await pump.idle();
    assert.equal(idleResolved, true);
});

test('request() while busy returns a promise for the next idle moment', async () => {
    const gate = deferred();
    const pump = createFramePump(async () => { await gate.promise; });

    pump.request(1);
    let resolved = false;
    const p = pump.request(2).then(() => { resolved = true; });
    await new Promise((r) => setTimeout(r, 0));
    assert.equal(resolved, false); // still applying frame 1

    gate.resolve();
    await p;
    assert.equal(resolved, true);
});
