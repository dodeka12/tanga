import test from 'node:test';
import assert from 'node:assert/strict';
import {
    GAP,
    stackMinSize,
    stackPreferredSize,
} from '../../../py/pytanga/viz/templates/views/stack-size.js';

const child = (min, pref) => ({
    minSizePx: (axis) => (axis === 'x' ? min.x : min.y),
    preferredPx: (axis) => (axis === 'x' ? pref.x : pref.y),
});

test('vertical stack min height = sum of child min heights + gaps', () => {
    const children = [child({ x: 100, y: 20 }, { x: null, y: 20 }), child({ x: 100, y: 30 }, { x: null, y: 30 })];
    assert.equal(stackMinSize('y', 'vertical', children, 0), 20 + 30 + GAP);
});

test('vertical stack min width = max child min width', () => {
    const children = [child({ x: 100, y: 20 }, {}), child({ x: 150, y: 30 }, {})];
    assert.equal(stackMinSize('x', 'vertical', children, 0), 150);
});

test('horizontal stack preferred width = sum of preferred widths + gaps', () => {
    const children = [child({ x: 0, y: 0 }, { x: 120, y: null }), child({ x: 0, y: 0 }, { x: 80, y: null })];
    assert.equal(stackPreferredSize('x', 'horizontal', children, 0), 120 + 80 + GAP);
});

test('wrap direction derives no min/preferred (measured DOM)', () => {
    const children = [child({ x: 100, y: 20 }, { x: 100, y: 20 })];
    assert.equal(stackMinSize('x', 'wrap', children, 0), 0);
    assert.equal(stackPreferredSize('x', 'wrap', children, 0), null);
});

test('empty children derive no min/preferred', () => {
    assert.equal(stackMinSize('y', 'vertical', [], 0), 0);
    assert.equal(stackPreferredSize('y', 'vertical', [], 0), null);
});
