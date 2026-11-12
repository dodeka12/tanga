// Tanga — unit tests for the pure stack size arithmetic (node --test).
import test from 'node:test';
import assert from 'node:assert/strict';
import {
    resolveGapPx,
    stackMinSize,
    stackPreferredSize,
} from '../../../py/pytanga/viz/templates/views/stack-size.js';

test('resolveGapPx parses CSS gap values', () => {
    assert.equal(resolveGapPx(12), 12);
    assert.equal(resolveGapPx('12px'), 12);
    assert.equal(resolveGapPx('12.5px'), 12.5);
    assert.equal(resolveGapPx('normal'), 4);
    assert.equal(resolveGapPx(''), 4);
    assert.equal(resolveGapPx(null), 4);
    assert.equal(resolveGapPx(0), 0);
});

test('resolveGapPx can report an unmeasurable gap', () => {
    assert.equal(resolveGapPx('12px', null), 12);
    assert.equal(resolveGapPx('normal', null), null);
});

const child = (size) => ({ minSizePx: () => size });
const preferredChild = (size) => ({
    minSizePx: () => size,
    preferredPx: () => size,
});

test('stackMinSize uses the default gap', () => {
    assert.equal(stackMinSize('y', 'vertical', [child(10), child(10)], 100), 24);
});

test('stackMinSize uses an explicit gap', () => {
    assert.equal(stackMinSize('y', 'vertical', [child(10), child(10)], 100, 12), 32);
});

test('stackMinSize is zero for wrap and maxes the cross axis', () => {
    assert.equal(stackMinSize('y', 'wrap', [child(10), child(10)], 100), 0);
    assert.equal(stackMinSize('x', 'vertical', [child(10), child(10)], 100), 10);
});

test('stackPreferredSize passes the explicit gap through', () => {
    assert.equal(
        stackPreferredSize('y', 'vertical', [preferredChild(10), preferredChild(10)], 100, 12),
        32
    );
});
