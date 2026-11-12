// Tanga — unit tests for menu option-row click targeting (node --test).
import test from 'node:test';
import assert from 'node:assert/strict';
import {
    isMenuRowInteractiveTarget,
    menuRowForTarget,
} from '../../../py/pytanga/viz/templates/views/menu-row.js';

function targetWith(matches) {
    return {
        closest(selector) {
            for (const [token, value] of Object.entries(matches)) {
                if (selector.includes(token)) return value;
            }
            return null;
        },
    };
}

test('interactive menu targets handle their own click', () => {
    assert.equal(isMenuRowInteractiveTarget(targetWith({ button: {} })), true);
    assert.equal(isMenuRowInteractiveTarget(targetWith({ input: {} })), true);
    assert.equal(isMenuRowInteractiveTarget(targetWith({ label: {} })), true);
    assert.equal(isMenuRowInteractiveTarget(targetWith({ 'tanga-menu-item': {} })), false);
    assert.equal(isMenuRowInteractiveTarget(null), false);
});

test('menuRowForTarget resolves a click inside the option row', () => {
    const row = { className: 'tanga-control tanga-menu-item' };
    assert.equal(menuRowForTarget(targetWith({ 'tanga-menu-item': row })), row);
});

test('menuRowForTarget resolves blank space in the control-view wrapper', () => {
    const row = { className: 'tanga-control tanga-menu-item' };
    const view = {
        querySelector(selector) {
            return selector === '.tanga-menu-item' ? row : null;
        },
    };
    assert.equal(menuRowForTarget(targetWith({ 'tanga-control-view': view })), row);
});

test('menuRowForTarget ignores clicks outside a menu option', () => {
    assert.equal(menuRowForTarget(targetWith({ 'tanga-menu-panel': {} })), null);
    assert.equal(menuRowForTarget(null), null);
});
