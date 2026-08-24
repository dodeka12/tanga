import test from 'node:test';
import assert from 'node:assert/strict';
import { resolveSplit, deriveMinSize, SPLITTER_SIZE } from '../../../py/pytanga/viz/templates/views/split-resolver.js';

const d = (min, max, preferred) => ({ min, max, preferred });

test('equal distribution between two flexible children', () => {
    const plan = resolveSplit([d(0, null, null), d(0, null, null)], 200);
    assert.equal(plan.items.length, 2);
    const childSpace = 200 - SPLITTER_SIZE;
    assert.equal(plan.items[0].size, childSpace / 2);
    assert.equal(plan.items[1].size, childSpace / 2);
    assert.equal(plan.splitters.length, 1);
    assert.equal(plan.splitters[0].position, childSpace / 2);
    assert.equal(plan.splitters[0].movable, true);
    assert.equal(plan.spacer, 0);
    assert.equal(plan.overflow, 0);
});

test('fixed child pins the splitter', () => {
    const plan = resolveSplit([d(100, 100, null), d(0, null, null)], 200);
    assert.equal(plan.items[0].fixed, true);
    assert.equal(plan.items[0].size, 100);
    assert.equal(plan.items[1].size, 200 - SPLITTER_SIZE - 100);
    assert.equal(plan.splitters[0].movable, false);
});

test('leftover space becomes a spacer when all children are fixed', () => {
    const plan = resolveSplit([d(50, 50, null), d(50, 50, null)], 200);
    assert.equal(plan.items[0].size, 50);
    assert.equal(plan.items[1].size, 50);
    assert.equal(plan.spacer, 200 - SPLITTER_SIZE - 100);
    assert.equal(plan.splitters[0].movable, false);
});

test('over-constrained minimums produce overflow (no negative sizes)', () => {
    const plan = resolveSplit([d(150, null, null), d(150, null, null)], 200);
    assert.equal(plan.items[0].size, 150);
    assert.equal(plan.items[1].size, 150);
    assert.equal(plan.spacer, 0);
    assert.equal(plan.overflow, 300 - (200 - SPLITTER_SIZE));
});

test('preferred sizes are honored proportionally', () => {
    const plan = resolveSplit([d(0, null, 100), d(0, null, 300)], 406);
    assert.equal(plan.items[0].size, 100);
    assert.equal(plan.items[1].size, 300);
    assert.equal(plan.splitters[0].position, 100);
});

test('three children → two splitters with correct positions', () => {
    const plan = resolveSplit([d(0, null, 100), d(0, null, 100), d(0, null, 100)], 3 * 100 + 2 * SPLITTER_SIZE);
    assert.equal(plan.items.length, 3);
    assert.equal(plan.splitters.length, 2);
    assert.equal(plan.splitters[0].position, 100);
    assert.equal(plan.splitters[1].position, 100 + SPLITTER_SIZE + 100);
    assert.equal(plan.spacer, 0);
});

// Fake child exposing minSizePx along an axis.
const child = (minX, minY) => ({ minSizePx: (axis) => (axis === 'x' ? minX : minY) });

test('deriveMinSize sums child minima along the split axis', () => {
    const children = [child(120, 120), child(100, 100)];
    assert.equal(deriveMinSize('x', 'x', children, 800), 120 + 100 + SPLITTER_SIZE);
});

test('deriveMinSize takes the max child minimum along the cross axis', () => {
    const children = [child(120, 120), child(100, 200)];
    assert.equal(deriveMinSize('y', 'x', children, 800), 200);
});

test('deriveMinSize returns 0 for no children', () => {
    assert.equal(deriveMinSize('x', 'x', [], 800), 0);
});
