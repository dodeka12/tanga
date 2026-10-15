// Tanga — unit tests for pure interaction hit resolution (node --test).
import test from 'node:test';
import assert from 'node:assert/strict';
import { matchTriggers, resolveHitTarget } from '../../../py/pytanga/viz/templates/hit-resolution.js';

const cfg = (triggers) => ({ triggers });

const DRAG_LEFT = { event_type: 'drag', mouse_button: 'left' };
const DRAG_LEFT_CTRL = { event_type: 'drag', mouse_button: 'left', modifiers: ['ctrl'] };

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
