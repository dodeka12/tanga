// Tanga — unit tests for group-header click targeting (node --test).
import test from 'node:test';
import assert from 'node:assert/strict';
import { isGroupHeaderInteractiveEvent } from '../../../py/pytanga/viz/templates/views/group-header.js';

function nodeWith(matches = {}) {
    return {
        closest(selector) {
            for (const [token, value] of Object.entries(matches)) {
                if (selector.includes(token)) return value;
            }
            return null;
        },
    };
}

test('fold-toggle icon click is ignored after the icon was detached', () => {
    const staleIcon = { closest: () => null };
    const toggle = nodeWith({ button: {} });
    const header = nodeWith();
    const event = {
        target: staleIcon,
        composedPath: () => [staleIcon, toggle, header],
    };
    assert.equal(isGroupHeaderInteractiveEvent(event), true);
});

test('title-bar click folds the group', () => {
    const title = nodeWith();
    const header = nodeWith();
    const event = {
        target: title,
        composedPath: () => [title, header],
    };
    assert.equal(isGroupHeaderInteractiveEvent(event), false);
});

test('other interactive header descendants handle their own click', () => {
    const control = nodeWith({ '[role="button"]': {} });
    const event = {
        target: control,
        composedPath: () => [control, nodeWith()],
    };
    assert.equal(isGroupHeaderInteractiveEvent(event), true);
});

test('falls back to the target when composedPath is unavailable', () => {
    const button = nodeWith({ button: {} });
    assert.equal(isGroupHeaderInteractiveEvent({ target: button }), true);
    assert.equal(isGroupHeaderInteractiveEvent({ target: nodeWith() }), false);
    assert.equal(isGroupHeaderInteractiveEvent(null), false);
});
