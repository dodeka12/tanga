// Tanga — unit tests for pure interaction hit resolution (node --test).
import test from 'node:test';
import assert from 'node:assert/strict';
import {
    hitPriority,
    matchTriggers,
    orderHitCandidates,
    resolveHitTarget,
} from '../../../py/pytanga/viz/templates/hit-resolution.js';

const cfg = (triggers) => ({ triggers });

const DRAG_LEFT = { event_type: 'drag', mouse_button: 'left' };
const DRAG_LEFT_CTRL = { event_type: 'drag', mouse_button: 'left', modifiers: ['ctrl'] };

// ── Pick precedence ──────────────────────────────────────────────

const candidatesFor = (entries) =>
    entries.map(([objectId, distance, screenSpace]) => ({
        objectId,
        intersect: { distance },
        screenSpace: !!screenSpace,
    }));

test('hitPriority defaults to 0 for missing or non-numeric configs', () => {
    assert.equal(hitPriority(null), 0);
    assert.equal(hitPriority({}), 0);
    assert.equal(hitPriority({ hit_priority: 'high' }), 0);
    assert.equal(hitPriority({ hit_priority: 10 }), 10);
});

test('orderHitCandidates puts a higher hit_priority first, however far it is', () => {
    const configs = new Map([
        ['body', cfg([DRAG_LEFT])],
        ['handle', { ...cfg([DRAG_LEFT]), hit_priority: 10 }],
    ]);
    const ordered = orderHitCandidates(candidatesFor([['body', 1], ['handle', 9]]), (id) =>
        configs.get(id) ?? null,
    );
    assert.deepEqual(
        ordered.map((c) => c.objectId),
        ['handle', 'body'],
    );
});

test('orderHitCandidates prefers a screen-space marker over a nearer body', () => {
    const configs = new Map([
        ['body', cfg([DRAG_LEFT])],
        ['marker', cfg([DRAG_LEFT])],
    ]);
    const ordered = orderHitCandidates(
        candidatesFor([['body', 1], ['marker', 5, true]]),
        (id) => configs.get(id) ?? null,
    );
    assert.deepEqual(
        ordered.map((c) => c.objectId),
        ['marker', 'body'],
    );
});

test('orderHitCandidates falls back to the nearest hit within the same tier', () => {
    const configs = new Map([
        ['far', cfg([DRAG_LEFT])],
        ['near', cfg([DRAG_LEFT])],
    ]);
    const ordered = orderHitCandidates(candidatesFor([['far', 7], ['near', 2]]), (id) =>
        configs.get(id) ?? null,
    );
    assert.deepEqual(
        ordered.map((c) => c.objectId),
        ['near', 'far'],
    );
});

test('orderHitCandidates keeps the input order for a full tie', () => {
    const configs = new Map([
        ['first', cfg([DRAG_LEFT])],
        ['second', cfg([DRAG_LEFT])],
    ]);
    const ordered = orderHitCandidates(candidatesFor([['first', 3], ['second', 3]]), (id) =>
        configs.get(id) ?? null,
    );
    assert.deepEqual(
        ordered.map((c) => c.objectId),
        ['first', 'second'],
    );
});

test('resolveHitTarget picks the priority-10 handle and falls through for unclaimed modifiers', () => {
    const configs = new Map([
        ['body', { ...cfg([DRAG_LEFT, DRAG_LEFT_CTRL]), hit_priority: 0 }],
        ['handle', { ...cfg([DRAG_LEFT]), hit_priority: 10 }],
    ]);
    const getConfig = (id) => configs.get(id) ?? null;
    const ordered = orderHitCandidates(candidatesFor([['body', 1], ['handle', 1.5]]), getConfig);

    // Plain drag: the handle wins although the body is nearer.
    assert.equal(
        resolveHitTarget(ordered, null, getConfig, 'drag', 'left', new Set()).objectId,
        'handle',
    );
    // ctrl+drag: the handle only declares a plain drag, so the body underneath wins.
    assert.equal(
        resolveHitTarget(ordered, null, getConfig, 'drag', 'left', new Set(['ctrl'])).objectId,
        'body',
    );
});


// ── Trigger matching and resolution ─────────────────────────────

test('matchTriggers requires an exact modifier match (empty = no modifiers)', () => {
    const config = cfg([DRAG_LEFT, DRAG_LEFT_CTRL]);
    assert.equal(matchTriggers(config, 'drag', 'left', new Set()).length, 1);
    assert.equal(matchTriggers(config, 'drag', 'left', new Set(['ctrl'])).length, 1);
    assert.equal(matchTriggers(config, 'drag', 'right', new Set(['ctrl'])).length, 0);
    assert.equal(matchTriggers(config, 'click', 'left', new Set()).length, 0);
    assert.deepEqual(matchTriggers(null, 'drag', 'left', new Set()), []);
});

test('a trigger without modifiers does not match a ctrl drag', () => {
    const config = cfg([DRAG_LEFT]);
    assert.equal(matchTriggers(config, 'drag', 'left', new Set()).length, 1);
    assert.equal(matchTriggers(config, 'drag', 'left', new Set(['ctrl'])).length, 0);
});

test('resolveHitTarget picks the nearest matching entity', () => {
    const getConfig = (id) => ({
        a: cfg([DRAG_LEFT]),
        b: cfg([DRAG_LEFT]),
        surface: cfg([DRAG_LEFT]),
    })[id];
    const candidates = [{ objectId: 'a', intersect: {} }, { objectId: 'b', intersect: {} }];
    const surface = { objectId: 'surface', intersect: {} };
    assert.equal(resolveHitTarget(candidates, surface, getConfig, 'drag', 'left', new Set()).objectId, 'a');
});

test('resolveHitTarget falls through to a farther matching entity', () => {
    const getConfig = (id) => ({
        a: cfg([]),
        b: cfg([DRAG_LEFT]),
        surface: cfg([DRAG_LEFT]),
    })[id];
    const candidates = [{ objectId: 'a', intersect: {} }, { objectId: 'b', intersect: {} }];
    const surface = { objectId: 'surface', intersect: {} };
    assert.equal(resolveHitTarget(candidates, surface, getConfig, 'drag', 'left', new Set()).objectId, 'b');
});

test('resolveHitTarget falls through to the surface when no entity matches', () => {
    const getConfig = (id) => ({ a: cfg([]), surface: cfg([DRAG_LEFT]) })[id];
    const candidates = [{ objectId: 'a', intersect: {} }];
    const surface = { objectId: 'surface', intersect: {} };
    assert.equal(resolveHitTarget(candidates, surface, getConfig, 'drag', 'left', new Set()).objectId, 'surface');
});

test('resolveHitTarget returns null when neither entity nor surface matches', () => {
    const getConfig = (id) => ({ a: cfg([]), surface: cfg([]) })[id];
    const candidates = [{ objectId: 'a', intersect: {} }];
    const surface = { objectId: 'surface', intersect: {} };
    assert.equal(resolveHitTarget(candidates, surface, getConfig, 'drag', 'left', new Set()), null);
});

test('resolveHitTarget lets ctrl+drag fall through to the surface when the entity only registers a plain drag', () => {
    const getConfig = (id) => ({ entity: cfg([DRAG_LEFT]), surface: cfg([DRAG_LEFT_CTRL]) })[id];
    const candidates = [{ objectId: 'entity', intersect: {} }];
    const surface = { objectId: 'surface', intersect: {} };
    // ctrl+drag: the entity's plain (no-modifier) drag does not match ctrl → surface wins.
    assert.equal(resolveHitTarget(candidates, surface, getConfig, 'drag', 'left', new Set(['ctrl'])).objectId, 'surface');
    // plain drag: the nearest entity wins.
    assert.equal(resolveHitTarget(candidates, surface, getConfig, 'drag', 'left', new Set()).objectId, 'entity');
});
